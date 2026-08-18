import copy
import re

from gauntlets.substrate_construct.generator import generate_taskset
from harness.gauntlet_evaluators import evaluate_task
from harness.substrate_construct import build_model_prompt, prepare_substrate
from substrate.runtime import SubstrateRuntime


def _one_per_family():
    tasks = generate_taskset(seed=42, n_tasks=50, split="dev")
    selected = {}
    for task in tasks:
        selected.setdefault(task["family"], task)
    return list(selected.values())


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_-]+", text.casefold()))


def test_every_construct_family_has_background_address_space():
    for task in generate_taskset(seed=42, n_tasks=50, split="dev"):
        assert task.get("history_filler"), f"{task['family']} has no address-space filler"


def test_history_filler_lexicon_is_disjoint_from_task_prompt():
    for task in _one_per_family():
        assert task.get("history_filler"), task["family"]
        probe = copy.deepcopy(task)
        probe["history_filler"] = {
            **probe["history_filler"],
            "count": 8,
            "words_per_record": 24,
            "minimum_address_space_words": 192,
        }
        rt = SubstrateRuntime()
        prepare_substrate(rt, probe, arm="S1")
        filler_text = " ".join(
            entry.content
            for entry in rt.compiler._memory_store
            if entry.metadata.get("source") == "synthetic_history_filler"
        )
        overlap = _words(filler_text) & _words(task["prompt"])
        assert not overlap, f"{task['family']} filler overlaps prompt lexicon: {sorted(overlap)}"


def test_s1_recovers_oracle_record_set_with_background_address_space():
    for task in _one_per_family():
        probe = copy.deepcopy(task)
        probe["history_filler"] = {
            **probe["history_filler"],
            "count": 40,
            "words_per_record": 24,
            "minimum_address_space_words": 960,
        }
        rt = SubstrateRuntime()
        prepare_substrate(rt, probe, arm="S1")
        prompt = build_model_prompt(rt, probe, arm="S1")
        for record in probe["memory_records"]:
            assert record["content"] in prompt, (
                f"{task['family']} S1 failed to recover oracle-set record {record['id']}"
            )


def test_typed_string_values_are_casefolded_and_whitespace_normalised():
    task = {
        "evaluator": "intent_fields",
        "expected": {
            "operation": "pure_call",
            "arguments": {"deadline": "2026-08-03", "owner": "Daniel"},
        },
    }
    output = (
        "operation: pure_call\n"
        "arguments:\n"
        "  deadline: \"  2026-08-03  \"\n"
        "  owner: \"  dAnIeL   \""
    )
    result = evaluate_task(output, task, allow_abstention=False)
    assert result["passed"] is True


def test_typed_argument_key_set_remains_exact():
    task = {
        "evaluator": "intent_fields",
        "expected": {
            "operation": "pure_call",
            "arguments": {"deadline": "2026-08-03", "owner": "Daniel"},
        },
    }
    output = (
        "operation: pure_call\n"
        "arguments:\n"
        "  deadline: \"2026-08-03\"\n"
        "  owner: \"Daniel\"\n"
        "  note: \"extra\""
    )
    result = evaluate_task(output, task, allow_abstention=False)
    assert result["passed"] is False
