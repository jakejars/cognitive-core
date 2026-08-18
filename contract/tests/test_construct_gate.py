import json
from pathlib import Path

import pytest

from contract.hardening import (
    ContractViolation,
    paired_exact_improvement,
    check_construct_validity,
    check_lockbox_creation_ready,
)


def test_construct_gate_reuses_phase_d_paired_exact_statistic():
    pairs = (
        [{"baseline_passed": False, "treatment_passed": True}] * 8
        + [{"baseline_passed": True, "treatment_passed": False}] * 1
        + [{"baseline_passed": True, "treatment_passed": True}] * 3
    )
    result = paired_exact_improvement(pairs)
    assert result["improved"] == 8
    assert result["harmed"] == 1
    assert result["discordant"] == 9
    assert result["p_value"] < 0.05


def _valid_record():
    pairs = []
    for i in range(50):
        pairs.append({
            "task_id": f"D-{i:03d}",
            "s0_passed": i < 8,
            "s1_passed": i < 35,
        })
    return {
        "protocol_version": "2.2",
        "status": "CONSTRUCT_VALID",
        "pilot_taskset_hash": "pilot-hash",
        "dev_taskset_hash": "dev-hash",
        "criteria": {
            "s1_vs_s0_min_delta": 0.30,
            "paired_alpha": 0.05,
            "oracle_min_supported_correct": 0.80,
            "bare_max_supported_correct": 0.20,
        },
        "arms": {
            "B1": {"supported_correct_rate": 0.08},
            "B2": {"supported_correct_rate": 0.12},
            "S0": {"supported_correct_rate": 0.16},
            "O1": {"supported_correct_rate": 0.90},
            "S1": {"supported_correct_rate": 0.70},
        },
        "pairs_s0_s1": pairs,
        "benchmark_frozen": True,
        "oracle_frozen": True,
        "evaluator_frozen": True,
        "replication": {
            "status": "DIRECTION_REPLICATED",
            "taskset_hash": "rep-hash",
            "s1_vs_s0_delta": 0.40,
            "paired_p_value": 0.01,
        },
    }


def test_construct_gate_requires_bare_4b_to_fail_without_capability(tmp_path):
    record = _valid_record()
    record["arms"]["B2"]["supported_correct_rate"] = 0.75
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "construct-validity.json").write_text(json.dumps(record))
    with pytest.raises(ContractViolation, match="B2"):
        check_construct_validity(str(tmp_path))


def test_construct_gate_rejects_cosmetic_freeze_on_same_pilot_and_dev_sample(tmp_path):
    record = _valid_record()
    record["pilot_taskset_hash"] = record["dev_taskset_hash"]
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "construct-validity.json").write_text(json.dumps(record))
    with pytest.raises(ContractViolation, match="pilot"):
        check_construct_validity(str(tmp_path))


def test_construct_gate_passes_with_oracle_bare_controls_and_paired_s1_gain(tmp_path):
    record = _valid_record()
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "construct-validity.json").write_text(json.dumps(record))
    check_construct_validity(str(tmp_path))


def test_lockbox_creation_requires_construct_validity_and_replication(tmp_path):
    record = _valid_record()
    record["replication"]["status"] = "NOT_RUN"
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "construct-validity.json").write_text(json.dumps(record))
    with pytest.raises(ContractViolation, match="replication"):
        check_lockbox_creation_ready(str(tmp_path))


def test_lockbox_creation_ready_only_after_construct_valid_replication(tmp_path):
    record = _valid_record()
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "construct-validity.json").write_text(json.dumps(record))
    check_lockbox_creation_ready(str(tmp_path))
