import json

import pytest

from contract.construct_pilot import ContractViolation, check_construct_pilot_ready


def _record():
    return {
        "protocol_version": "2.2",
        "status": "PENDING_PILOT",
        "pilot_taskset_hash": "pilot",
        "dev_taskset_hash": "dev",
        "format_policy": {
            "string_value_normalization": "casefold_collapse_whitespace",
            "argument_key_policy": "exact",
            "unexpected_keys": "reject",
            "o1_invalid_rate_benchmark_defect_threshold": 0.10,
            "on_threshold_breach": "BENCHMARK_DEFECT_REVISE_FORMAT",
        },
        "retrieval_interpretation": {
            "o1_minus_s1_expected": "approximately_zero",
            "role": "attribution_control",
            "meaning": "confirms_retrieval_not_bottleneck_if_prediction_holds",
            "not_evidence_for": ["retrieval_quality", "address_space_scaling"],
            "retrieval_difficulty": "neutral_address_space_only",
            "near_semantic_distractors": "separate_experiment",
        },
        "pilot_predictions": {
            "s1_full_oracle_recovery": "15/15",
            "o1_minus_s1": "approximately_zero",
            "b1_supported_correct": "near_zero_on_substrate_required_families",
            "b2_supported_correct": "near_zero_on_substrate_required_families",
            "o1_invalid_rate_max": 0.10,
            "frozen_before_pilot": True,
        },
        "pilot": {},
    }


def _write(tmp_path, record):
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    (ledger / "construct-validity.json").write_text(json.dumps(record))


def test_construct_pilot_requires_format_policy_before_running(tmp_path):
    record = _record()
    record.pop("format_policy")
    _write(tmp_path, record)
    with pytest.raises(ContractViolation, match="format policy"):
        check_construct_pilot_ready(str(tmp_path))


def test_construct_pilot_requires_retrieval_interpretation_before_running(tmp_path):
    record = _record()
    record.pop("retrieval_interpretation")
    _write(tmp_path, record)
    with pytest.raises(ContractViolation, match="retrieval interpretation"):
        check_construct_pilot_ready(str(tmp_path))


def test_construct_pilot_rejects_retrieval_quality_claim_from_neutral_address_space(tmp_path):
    record = _record()
    record["retrieval_interpretation"]["not_evidence_for"] = ["address_space_scaling"]
    _write(tmp_path, record)
    with pytest.raises(ContractViolation, match="retrieval interpretation"):
        check_construct_pilot_ready(str(tmp_path))


def test_construct_pilot_requires_predictions_before_running(tmp_path):
    record = _record()
    record.pop("pilot_predictions")
    _write(tmp_path, record)
    with pytest.raises(ContractViolation, match="pilot predictions"):
        check_construct_pilot_ready(str(tmp_path))


def test_construct_pilot_rejects_changed_predictions(tmp_path):
    record = _record()
    record["pilot_predictions"]["s1_full_oracle_recovery"] = "14/15"
    _write(tmp_path, record)
    with pytest.raises(ContractViolation, match="pilot predictions"):
        check_construct_pilot_ready(str(tmp_path))


def test_construct_pilot_policies_are_accepted_before_results_exist(tmp_path):
    record = _record()
    _write(tmp_path, record)
    check_construct_pilot_ready(str(tmp_path))


def test_o1_invalid_rate_above_preregistered_threshold_is_benchmark_defect(tmp_path):
    record = _record()
    record["pilot"]["o1_invalid_rate"] = 0.20
    _write(tmp_path, record)
    with pytest.raises(ContractViolation, match="BENCHMARK_DEFECT"):
        check_construct_pilot_ready(str(tmp_path))


def test_o1_invalid_rate_at_or_below_threshold_does_not_kill_construct(tmp_path):
    record = _record()
    record["pilot"]["o1_invalid_rate"] = 0.10
    _write(tmp_path, record)
    check_construct_pilot_ready(str(tmp_path))
