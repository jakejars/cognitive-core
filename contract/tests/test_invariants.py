"""Adversarial test suite for contract invariants.

Every invariant is tested with:
1. KNOWN-VALID fixture — should pass
2. KNOWN-INVALID fixture — should raise ContractViolation
3. BYPASS-ATTEMPT fixture — adversarial bypass the old version would miss
"""

import json, os, sys, tempfile
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest

from contract.schema import (
    ExperimentCell, ExperimentReceipt, GenerationManifest, LockboxEntry,
    Partition, PhaseConstants, ProtocolInfo, RunMetrics, RunResult,
    SubstrateManifest, TaskManifest, ModelManifest,
)
from contract.invariants import (
    ContractViolation, check_experiment_matrix, check_lockbox_integrity,
    check_chat_template_parity, check_phase_d_gate, check_phase_constants,
)

# ── Helpers ──────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_proj():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "ledger", "receipts").mkdir(parents=True)
        Path(tmp, "contract", "adapters").mkdir(parents=True)
        Path(tmp, "phases").mkdir()
        yield tmp


def _receipt(cell=ExperimentCell.B1, part=Partition.DEV, rate=0.8, rid=None):
    rid = rid or f"{cell.value}-{part.value}-001"
    return ExperimentReceipt(
        run_id=rid, cell=cell, partition=part,
        created_at="2026-08-18T00:00:00Z",
        model=ModelManifest(model_id=f"{cell.value}-m", revision="a",
            weights_hash="h", tokenizer_id="t", tokenizer_hash="th",
            template_adapter_version="verified_v1", applied_template="t"),
        generation=GenerationManifest(thinking_mode=False,
            max_total_tokens=4096, max_answer_tokens=256,
            temperature=0.0, top_p=0.0, stop_policy="eos"),
        tasks=TaskManifest(source="t", partition=part,
            task_ids=["t1","t2"], content_hash="h", n_tasks=2),
        substrate=SubstrateManifest(revision="v1", config_hash="c",
            modules=["m"]) if cell in (ExperimentCell.S1, ExperimentCell.S2) else None,
        result=RunResult(result_hash="rh", completed_at="2026-08-18T01:00:00Z",
            metrics=RunMetrics(n_passed=int(2*rate), n_total=2, pass_rate=rate,
                mean_score=rate, mean_latency_ms=100, total_time_s=1.0)),
        protocol=ProtocolInfo(contract_version="2.2",
            preregistration_hash="p", amendment_log_hash="a"),
    )


def _save(proj, r):
    from dataclasses import asdict
    r.finalize()
    with open(Path(proj, "ledger", "receipts", f"{r.run_id}.json"), "w") as f:
        json.dump(asdict(r), f, default=str)


# ═══════════════════════════════════════════════════════════════════════════
# 1. EXPERIMENT MATRIX (Contract §2)
# ═══════════════════════════════════════════════════════════════════════════

class TestMatrix:
    def test_valid_full(self, tmp_proj):
        for c in (ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1, ExperimentCell.S2):
            _save(tmp_proj, _receipt(c, Partition.DEV))
        check_experiment_matrix(tmp_proj)  # should not raise

    def test_missing_s2(self, tmp_proj):
        for c in (ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1):
            _save(tmp_proj, _receipt(c, Partition.DEV))
        with pytest.raises(ContractViolation, match="S2"):
            check_experiment_matrix(tmp_proj)

    def test_bypass_empty_file(self, tmp_proj):
        """Empty json file must not count as S2."""
        Path(tmp_proj, "ledger", "receipts", "s2_fake.json").write_text('{"cell":"S2"}')
        for c in (ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1):
            _save(tmp_proj, _receipt(c, Partition.DEV))
        with pytest.raises(ContractViolation):
            check_experiment_matrix(tmp_proj)

    def test_bypass_placeholder_runner(self, tmp_proj):
        """s2_runner.py file must not count as S2."""
        Path(tmp_proj, "harness").mkdir()
        Path(tmp_proj, "harness", "s2_runner.py").write_text("# placeholder\n")
        for c in (ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1):
            _save(tmp_proj, _receipt(c, Partition.DEV))
        with pytest.raises(ContractViolation):
            check_experiment_matrix(tmp_proj)


# ═══════════════════════════════════════════════════════════════════════════
# 2. LOCKBOX INTEGRITY (Contract §3.1)
# ═══════════════════════════════════════════════════════════════════════════

class TestLockbox:
    def test_valid_untouched(self, tmp_proj):
        data = {"entries": {"h1": {"content_hash":"h1","partition":"lockbox",
            "created_at":"2026-08-17T00:00:00Z","frozen_at":"2026-08-18T00:00:00Z",
            "evaluation_count":0}}}
        with open(Path(tmp_proj, "ledger", "lockbox-ledger.json"), "w") as f:
            json.dump(data, f)
        check_lockbox_integrity(tmp_proj)

    def test_valid_legitimate_post_freeze(self, tmp_proj):
        """Post-freeze evaluation is not contamination."""
        data = {"entries": {"h1": {"content_hash":"h1","partition":"lockbox",
            "created_at":"2026-08-17T00:00:00Z","frozen_at":"2026-08-18T00:00:00Z",
            "first_evaluated_at":"2026-08-19T00:00:00Z","evaluation_count":1}}}
        with open(Path(tmp_proj, "ledger", "lockbox-ledger.json"), "w") as f:
            json.dump(data, f)
        check_lockbox_integrity(tmp_proj)

    def test_invalid_eval_before_freeze(self, tmp_proj):
        data = {"entries": {"h1": {"content_hash":"h1","partition":"lockbox",
            "created_at":"2026-08-17T00:00:00Z","frozen_at":"2026-08-18T00:00:00Z",
            "first_evaluated_at":"2026-08-17T12:00:00Z","evaluation_count":1}}}
        with open(Path(tmp_proj, "ledger", "lockbox-ledger.json"), "w") as f:
            json.dump(data, f)
        with pytest.raises(ContractViolation, match="before freeze"):
            check_lockbox_integrity(tmp_proj)

    def test_invalid_exposed_before_freeze(self, tmp_proj):
        data = {"entries": {"h1": {"content_hash":"h1","partition":"lockbox",
            "created_at":"2026-08-17T00:00:00Z","frozen_at":"2026-08-18T00:00:00Z",
            "first_exposed_at":"2026-08-17T12:00:00Z","evaluation_count":0}}}
        with open(Path(tmp_proj, "ledger", "lockbox-ledger.json"), "w") as f:
            json.dump(data, f)
        with pytest.raises(ContractViolation, match="before freeze"):
            check_lockbox_integrity(tmp_proj)

    def test_invalid_multiple_evals(self, tmp_proj):
        data = {"entries": {"h1": {"content_hash":"h1","partition":"lockbox",
            "created_at":"2026-08-17T00:00:00Z","frozen_at":"2026-08-18T00:00:00Z",
            "first_evaluated_at":"2026-08-19T00:00:00Z","evaluation_count":3}}}
        with open(Path(tmp_proj, "ledger", "lockbox-ledger.json"), "w") as f:
            json.dump(data, f)
        with pytest.raises(ContractViolation, match="3x"):
            check_lockbox_integrity(tmp_proj)


# ═══════════════════════════════════════════════════════════════════════════
# 3. CHAT TEMPLATE PARITY (Contract §2, §3.4)
# ═══════════════════════════════════════════════════════════════════════════

class TestTemplate:
    def test_valid_adapter(self, tmp_proj):
        a = {"model_id":"M","template_source":"apply_chat_template",
             "golden_tokenisation_test":{"test_input":"Hi","expected_token_ids":[1]},
             "generation_config":{"thinking_mode":False,"max_total_tokens":4096,"temperature":0.0},
             "template_string":"<test>"}
        with open(Path(tmp_proj, "contract", "adapters", "a.json"), "w") as f:
            json.dump(a, f)
        check_chat_template_parity(tmp_proj)

    def test_invalid_no_adapters(self, tmp_proj):
        with pytest.raises(ContractViolation, match="adapter"):
            check_chat_template_parity(tmp_proj)

    def test_bypass_bad_adapter(self, tmp_proj):
        """Incomplete adapter must fail."""
        a = {"model_id":"M"}
        with open(Path(tmp_proj, "contract", "adapters", "bad.json"), "w") as f:
            json.dump(a, f)
        with pytest.raises(ContractViolation):
            check_chat_template_parity(tmp_proj)

    def test_bypass_unverified_receipt(self, tmp_proj):
        """Receipt with unverified_template must fail."""
        a = {"model_id":"M","template_source":"x",
             "golden_tokenisation_test":{"test_input":"Hi","expected_token_ids":[1]},
             "generation_config":{"thinking_mode":False,"max_total_tokens":4096,"temperature":0.0},
             "template_string":"<test>"}
        with open(Path(tmp_proj, "contract", "adapters", "a.json"), "w") as f:
            json.dump(a, f)
        r = _receipt()
        r.model.template_adapter_version = "unverified_v1"
        _save(tmp_proj, r)
        with pytest.raises(ContractViolation, match="not verified"):
            check_chat_template_parity(tmp_proj)


# ═══════════════════════════════════════════════════════════════════════════
# 4. PHASE D GATE (Contract §6 — Phase D)
# ═══════════════════════════════════════════════════════════════════════════

class TestPhaseD:
    def test_valid_full_ab(self, tmp_proj):
        data = {"protocol_version":"2.2","pre_registered_criterion":"min 10% improvement",
                "criterion_threshold":0.1,
                "baseline":{"n_passed":3,"n_total":10,"pass_rate":0.3},
                "treatment":{"n_passed":6,"n_total":10,"pass_rate":0.6},
                "task_ids":["f1","f2"]}
        with open(Path(tmp_proj, "ledger", "counterfactual_eval.json"), "w") as f:
            json.dump(data, f)
        check_phase_d_gate(tmp_proj)

    def test_invalid_missing(self, tmp_proj):
        with pytest.raises(ContractViolation, match="no counterfactual"):
            check_phase_d_gate(tmp_proj)

    def test_bypass_boolean_only(self, tmp_proj):
        """gate_passed: true alone must fail."""
        with open(Path(tmp_proj, "ledger", "counterfactual_eval.json"), "w") as f:
            json.dump({"gate_passed":True,"task_ids":["fake"]}, f)
        with pytest.raises(ContractViolation, match="protocol_version"):
            check_phase_d_gate(tmp_proj)

    def test_bypass_no_criterion(self, tmp_proj):
        data = {"protocol_version":"2.2",
                "baseline":{"n_passed":3,"n_total":10,"pass_rate":0.3},
                "treatment":{"n_passed":6,"n_total":10,"pass_rate":0.6}}
        with open(Path(tmp_proj, "ledger", "counterfactual_eval.json"), "w") as f:
            json.dump(data, f)
        with pytest.raises(ContractViolation, match="pre_registered_criterion"):
            check_phase_d_gate(tmp_proj)


# ═══════════════════════════════════════════════════════════════════════════
# 5. PHASE CONSTANTS (Contract §3.2)
# ═══════════════════════════════════════════════════════════════════════════

class TestConstants:
    def test_valid(self, tmp_proj):
        with open(Path(tmp_proj, "ledger", "phase-constants.json"), "w") as f:
            json.dump({"C_success":0.95,"C_memory":0.5,"C_latency":0.2,"C_trust":0.5,
                       "frozen_at":"2026-08-18T00:00:00Z","calibration_basis":"A"}, f)
        check_phase_constants(tmp_proj)

    def test_invalid_missing(self, tmp_proj):
        with pytest.raises(ContractViolation, match="not frozen"):
            check_phase_constants(tmp_proj)

    def test_invalid_out_of_range(self, tmp_proj):
        with open(Path(tmp_proj, "ledger", "phase-constants.json"), "w") as f:
            json.dump({"C_success":5.0,"C_memory":0.5,"C_latency":0.2,"C_trust":0.5,
                       "frozen_at":"2026-08-18T00:00:00Z"}, f)
        with pytest.raises(ContractViolation, match="C_success"):
            check_phase_constants(tmp_proj)
