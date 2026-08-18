"""Pre-pilot construct guards.

This gate is intentionally separate from the final construct-validity gate. It
freezes typed-output failure handling, O1/S1 interpretation, and pilot
predictions before any pilot results exist.
"""

from __future__ import annotations

import json
from pathlib import Path

from contract.invariants import ContractViolation


EXPECTED_FORMAT_POLICY = {
    "string_value_normalization": "casefold_collapse_whitespace",
    "argument_key_policy": "exact",
    "unexpected_keys": "reject",
    "on_threshold_breach": "BENCHMARK_DEFECT_REVISE_FORMAT",
}

EXPECTED_RETRIEVAL_INTERPRETATION = {
    "o1_minus_s1_expected": "approximately_zero",
    "role": "attribution_control",
    "meaning": "confirms_retrieval_not_bottleneck_if_prediction_holds",
    "retrieval_difficulty": "neutral_address_space_only",
    "near_semantic_distractors": "separate_experiment",
}
EXPECTED_RETRIEVAL_NONCLAIMS = {"retrieval_quality", "address_space_scaling"}

EXPECTED_PILOT_PREDICTIONS = {
    "s1_full_oracle_recovery": "15/15",
    "o1_minus_s1": "approximately_zero",
    "b1_supported_correct": "near_zero_on_substrate_required_families",
    "b2_supported_correct": "near_zero_on_substrate_required_families",
    "o1_invalid_rate_max": 0.10,
    "frozen_before_pilot": True,
}


def _record(project_root: str) -> dict:
    path = Path(project_root) / "ledger" / "construct-validity.json"
    if not path.is_file():
        raise ContractViolation("ledger/construct-validity.json is required")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ContractViolation("construct-validity.json must be an object")
    return data


def _check_retrieval_interpretation(data: dict) -> None:
    interpretation = data.get("retrieval_interpretation")
    if not isinstance(interpretation, dict):
        raise ContractViolation(
            "construct pilot retrieval interpretation must be frozen before pilot"
        )

    for key, expected in EXPECTED_RETRIEVAL_INTERPRETATION.items():
        if interpretation.get(key) != expected:
            raise ContractViolation(
                f"construct pilot retrieval interpretation {key} must be {expected!r}"
            )

    nonclaims = set(interpretation.get("not_evidence_for", []))
    if not EXPECTED_RETRIEVAL_NONCLAIMS.issubset(nonclaims):
        raise ContractViolation(
            "construct pilot retrieval interpretation must explicitly exclude "
            "retrieval_quality and address_space_scaling claims"
        )


def _check_pilot_predictions(data: dict) -> None:
    predictions = data.get("pilot_predictions")
    if not isinstance(predictions, dict):
        raise ContractViolation("construct pilot predictions must be frozen before pilot")

    for key, expected in EXPECTED_PILOT_PREDICTIONS.items():
        if predictions.get(key) != expected:
            raise ContractViolation(
                f"construct pilot predictions {key} must be {expected!r}"
            )


def check_construct_pilot_ready(project_root: str = None) -> None:
    """Validate pre-pilot interpretation rules, predictions, and typed-output policy.

    If pilot O1 invalid-rate later exceeds the pre-registered threshold, the
    result is BENCHMARK_DEFECT_REVISE_FORMAT, not construct invalidation.

    O1≈S1 is pre-registered as an attribution-control prediction for this
    neutral-address-space benchmark. A near-zero delta means retrieval was not
    the observed bottleneck; it is not evidence of general retrieval quality or
    address-space scaling.
    """
    pr = project_root or "."
    data = _record(pr)
    policy = data.get("format_policy")
    if not isinstance(policy, dict):
        raise ContractViolation("construct pilot format policy must be frozen before pilot")

    for key, expected in EXPECTED_FORMAT_POLICY.items():
        if policy.get(key) != expected:
            raise ContractViolation(
                f"construct pilot format policy {key} must be {expected!r}"
            )

    threshold = policy.get("o1_invalid_rate_benchmark_defect_threshold")
    if threshold is None:
        raise ContractViolation(
            "construct pilot format policy missing o1_invalid_rate_benchmark_defect_threshold"
        )
    threshold = float(threshold)
    if not (0.0 <= threshold <= 1.0):
        raise ContractViolation("construct pilot O1 invalid-rate threshold must be in [0,1]")

    _check_retrieval_interpretation(data)
    _check_pilot_predictions(data)

    pilot = data.get("pilot") or {}
    invalid_rate = pilot.get("o1_invalid_rate")
    if invalid_rate is not None and float(invalid_rate) > threshold:
        raise ContractViolation(
            "BENCHMARK_DEFECT_REVISE_FORMAT: "
            f"pilot O1 invalid rate {float(invalid_rate):.1%} exceeds "
            f"pre-registered threshold {threshold:.1%}; do not interpret this as construct failure"
        )

    print(
        "  [Contract] Construct pilot policy frozen: "
        f"normalization={policy['string_value_normalization']}, "
        f"O1 invalid defect threshold={threshold:.1%}, "
        "O1-S1 expected≈0 as attribution control only, pilot predictions frozen"
    )
