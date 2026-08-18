#!/usr/bin/env python3
"""
Check Research Contract Invariants — Convenience Entry Point

Usage:
    python3 check-invariants.py                    # Run all checks
    python3 check-invariants.py --summary          # Quick status
    python3 check-invariants.py --check-all        # Same as default
    python3 check-invariants.py --check-template   # Single gate
    python3 check-invariants.py --check-model-config
    python3 check-invariants.py --state phase Phase-C
"""

import sys, os
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from contract import (
    check_experiment_matrix, check_lockbox_intact, check_lockbox_pass,
    check_chat_template_parity, check_phase_d_gate,
    check_phase_constants, check_compensation_hypothesis,
    check_amendment_record, check_budget_overrun, check_model_config_parity,
    ContractViolation,
    ClaimTransitioner,
)

CHECKS = [
    ("Chat Template Parity (Contract §2, §3.4)", check_chat_template_parity),
    ("Lockbox Intact (Contract §3.1)", check_lockbox_intact),
    ("Lockbox Pass (Contract §3.1)", check_lockbox_pass),
    ("Experiment Matrix (Contract §2)", check_experiment_matrix),
    ("Phase Constants Frozen (Contract §3.2)", check_phase_constants),
    ("Compensation Hypothesis (Contract §3.3)", check_compensation_hypothesis),
    ("Amendment Record (Contract §11)", check_amendment_record),
    ("Budget Overrun (Contract §4)", check_budget_overrun),
    ("Model Config Parity (Contract §3.4)", check_model_config_parity),
    ("Phase D Gate (Contract §6)", check_phase_d_gate),
]

def run_all():
    print("=" * 65)
    print("  Cognitive Core — Research Contract Invariants v2.2")
    print("=" * 65)

    all_pass = True
    for name, fn in CHECKS:
        print(f"\n  [{name}]")
        try:
            fn(script_dir)
            print(f"    PASS")
        except ContractViolation as e:
            all_pass = False
            for line in str(e).split('\n'):
                print(f"    {line}")

    print(f"\n{'=' * 65}")
    if all_pass:
        print("  ALL INVARIANTS SATISFIED")
    else:
        print("  CONTRACT VIOLATIONS DETECTED — claims blocked")
    print(f"{'=' * 65}")
    return 0 if all_pass else 1


def run_summary():
    """Quick one-line-per-check summary."""
    print("Contract Invariants:")
    all_pass = True
    for name, fn in CHECKS:
        try:
            fn(script_dir)
            print(f"  ✅ {name}")
        except ContractViolation as e:
            all_pass = False
            first_line = str(e).split('\n')[0][:80]
            print(f"  ❌ {name}: {first_line}")
    return 0 if all_pass else 1


def check_state(entity_type: str, entity_id: str):
    """Check the current state of an entity."""
    t = ClaimTransitioner(script_dir)
    state = t.get_entity_state(entity_type, entity_id)
    print(f"  {entity_type}/{entity_id}: {state.value if state else 'UNKNOWN'}")
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check Research Contract Invariants")
    parser.add_argument("--summary", action="store_true", help="Quick summary")
    parser.add_argument("--state", nargs=2, metavar=("TYPE", "ID"),
                        help="Check entity state (e.g. phase Phase-C)")
    parser.add_argument("--check-all", action="store_true", help="Run all checks")
    parser.add_argument("--check-template", action="store_true")
    parser.add_argument("--check-lockbox", action="store_true")
    parser.add_argument("--check-matrix", action="store_true")
    parser.add_argument("--check-phase-d", action="store_true")
    parser.add_argument("--check-constants", action="store_true")
    parser.add_argument("--check-model-config", action="store_true")
    parser.add_argument("--check-budgets", action="store_true")
    args = parser.parse_args()

    if args.summary:
        sys.exit(run_summary())
    if args.state:
        sys.exit(check_state(args.state[0], args.state[1]))

    # Map single-check flags to functions
    check_map = {
        "check_template": check_chat_template_parity,
        "check_lockbox": check_lockbox_intact,
        "check_matrix": check_experiment_matrix,
        "check_phase_d": check_phase_d_gate,
        "check_constants": check_phase_constants,
        "check_model_config": check_model_config_parity,
        "check_budgets": check_budget_overrun,
    }
    for flag, fn in check_map.items():
        if getattr(args, flag, False):
            try:
                fn(script_dir)
                print(f"PASS")
                sys.exit(0)
            except ContractViolation as e:
                print(f"FAIL: {e}")
                sys.exit(1)

    # Default: run all
    sys.exit(run_all())