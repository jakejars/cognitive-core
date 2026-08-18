import pytest

from harness.gauntlet_evaluators import evaluate_task


def _supersession_task():
    return {
        "id": "CV-SUP-001",
        "family": "supersession",
        "prompt": "Return the current deadline and owner as a typed intent.",
        "evaluator": "intent_fields",
        "expected": {
            "operation": "pure_call",
            "arguments": {"deadline": "2026-08-03", "owner": "Daniel"},
        },
        "abstention_operations": ["retrieve", "ask_user"],
        "target_entities": ["project-atlas"],
        "memory_records": [
            {"id": "r-old-deadline", "entity_id": "project-atlas", "content": "Project Atlas deadline was 2026-06-14.", "entry_type": "observation"},
            {"id": "r-new-deadline", "entity_id": "project-atlas", "content": "Project Atlas deadline is now 2026-08-03; this supersedes 2026-06-14.", "entry_type": "observation"},
            {"id": "r-old-owner", "entity_id": "project-atlas", "content": "Project Atlas owner was Maya.", "entry_type": "observation"},
            {"id": "r-new-owner", "entity_id": "project-atlas", "content": "Project Atlas owner is now Daniel; Maya is superseded.", "entry_type": "observation"},
            {"id": "r-near-miss", "entity_id": "project-atlas-docs", "content": "Project Atlas documentation review owner is Dana.", "entry_type": "observation"},
        ],
        "oracle_record_ids": [
            "r-old-deadline", "r-new-deadline", "r-old-owner", "r-new-owner", "r-near-miss"
        ],
        "null_memory_records": [
            {"id": "n1", "entity_id": "project-borealis", "content": "Project Borealis deadline is 2026-08-03.", "entry_type": "observation"},
            {"id": "n2", "entity_id": "project-borealis", "content": "Project Borealis owner is Daniel.", "entry_type": "observation"},
        ],
    }


def test_typed_fields_reject_packet_parroting():
    task = _supersession_task()
    output = 'operation: pure_call\narguments:\n  deadline: "2026-06-14 then 2026-08-03"\n  owner: "Maya then Daniel"'
    result = evaluate_task(output, task, allow_abstention=False)
    assert result["passed"] is False
    assert result["outcome"] == "confident_wrong"


def test_typed_fields_accept_current_state_only():
    task = _supersession_task()
    output = 'operation: pure_call\narguments:\n  deadline: "2026-08-03"\n  owner: "Daniel"'
    result = evaluate_task(output, task, allow_abstention=False)
    assert result["passed"] is True
    assert result["outcome"] == "supported_correct"


def test_typed_effect_action_is_field_scored():
    task = {
        "id": "CV-EFF-001",
        "evaluator": "intent_fields",
        "expected": {"operation": "pure_call", "arguments": {"action": "replay"}},
        "abstention_operations": ["ask_user"],
    }
    good = "operation: pure_call\narguments:\n  action: replay"
    bad = "operation: pure_call\narguments:\n  action: issue_payment"
    assert evaluate_task(good, task, allow_abstention=False)["passed"] is True
    assert evaluate_task(bad, task, allow_abstention=False)["passed"] is False


def test_bare_model_can_score_correct_abstention_without_task_success():
    task = _supersession_task()
    output = "operation: retrieve\narguments:\n  query: current Project Atlas state"
    result = evaluate_task(output, task, allow_abstention=True)
    assert result["passed"] is False
    assert result["outcome"] == "correct_abstention"


def test_construct_arms_include_bare_4b_size_control():
    from harness.substrate_construct import CONSTRUCT_ARMS
    assert CONSTRUCT_ARMS == ("B1", "B2", "S0", "O1", "S1")


def test_s0_rejects_same_entity_or_stale_on_topic_records():
    from harness.substrate_construct import validate_construct_task
    task = _supersession_task()
    task["null_memory_records"][0]["entity_id"] = "project-atlas"
    with pytest.raises(ValueError, match="S0"):
        validate_construct_task(task)


def test_oracle_is_perfect_recall_of_relevant_set_not_answer_selection():
    from substrate.context_compiler import ContextCompiler, MemoryEntry

    task = _supersession_task()
    compiler = ContextCompiler()
    for record in task["memory_records"]:
        compiler.store(MemoryEntry(
            id=record["id"],
            content=record["content"],
            entry_type=record["entry_type"],
            metadata={"entity_id": record["entity_id"]},
        ))

    packet = compiler.compile_by_ids(task["oracle_record_ids"])
    serialized = packet.serialize()
    assert "2026-06-14" in serialized
    assert "2026-08-03" in serialized
    assert "Maya" in serialized
    assert "Daniel" in serialized
    assert "Dana" in serialized


def test_current_prompt_is_not_stored_before_s1_retrieval():
    from harness.substrate_construct import prepare_substrate
    from substrate.runtime import SubstrateRuntime

    task = _supersession_task()
    rt = SubstrateRuntime()
    prepare_substrate(rt, task, arm="S1")
    stored = [entry.content for entry in rt.compiler._memory_store]
    assert task["prompt"] not in stored
    assert all(record["content"] in stored for record in task["memory_records"])


def test_pilot_and_final_samples_are_distinct():
    from gauntlets.substrate_construct.generator import generate_taskset
    from contract.evidence import hash_taskset

    pilot = generate_taskset(seed=41, n_tasks=15, split="pilot")
    final = generate_taskset(seed=42, n_tasks=50, split="dev")
    assert set(task["id"] for task in pilot).isdisjoint(task["id"] for task in final)
    assert hash_taskset(pilot) != hash_taskset(final)
