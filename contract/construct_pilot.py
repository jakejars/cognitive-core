"""Pre-pilot construct-format guard.

This gate is intentionally separate from the final construct-validity gate. It
freezes how typed-output failures are interpreted before any pilot results exist.
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


def _record(project_root: str) -> dict:
    path = Path(project_root) / "ledger" / "construct-validity.json"
    if not path.is_file():
        raise ContractViolation("ledger/construct-validity.json is required")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ContractViolation("construct-validity.json must be an object")
    return data


def check_construct_pilot_ready(project_root: str = None) -> None:
    """Validate the typed-output policy before pilot and interpret O1 invalids.

    If pilot O1 invalid-rate later exceeds the pre-registered threshold, the
    result is BENCHMARK_DEFECT_REVISE_FORMAT, not construct invalidation.
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

    pilot = data.get("pilot") or {}
    invalid_rate = pilot.get("o1_invalid_rate")
    if invalid_rate is not None and float(invalid_rate) > threshold:
        raise ContractViolation(
            "BENCHMARK_DEFECT_REVISE_FORMAT: "
            f"pilot O1 invalid rate {float(invalid_rate):.1%} exceeds "
            f"pre-registered threshold {threshold:.1%}; do not interpret this as construct failure"
        )

    print(
        "  [Contract] Construct pilot format policy frozen: "
        f"normalization={policy['string_value_normalization']}, "
        f"O1 invalid defect threshold={threshold:.1%}"
    )
