# Contract — Executable Research Protocol v2.2

This package is the sole authoritative protocol enforcement mechanism.
The harness imports from `contract.*` — never the other way around.

## Structure

```
contract/
    __init__.py      # Public API exports
    schema.py        # Data models: receipts, manifests, lockbox ledger
    invariants.py    # Invariant checks — each raises ContractViolation
    transition.py    # Mandatory state-transition API
    adapters/        # Verified model template adapters + golden tokens
    tests/           # Adversarial test suite
```

## Invariants

| # | Invariant | Contract § | Type | What It Checks |
|---|---|---|---|---|
| 1 | Experiment Matrix | §2 | BLOCKING | Validated receipts for B1/B2/S1/S2 |
| 2 | Lockbox Integrity | §3.1 | BLOCKING | Exposure ledger; pre-freeze exposure = violation |
| 3 | Chat Template Parity | §2, §3.4 | BLOCKING | Verified adapters with golden token tests |
| 4 | Phase Constants | §3.2 | BLOCKING | C_success/C_memory/C_latency/C_trust frozen |
| 5 | Compensation Hyp | §3.3 | BLOCKING | If B2 dominates B1, numeric threshold required |
| 6 | Amendment Record | §11 | BLOCKING | All protocol changes in amendment-log.json |
| 7 | Phase D Gate | §6 | BLOCKING | Raw paired A/B results with delta |

## Key Design

- **Receipts, not files**: Empty `s2_runner.py` does NOT count as S2
- **Post-freeze eval ≠ contamination**: Only pre-freeze exposure violates lockbox
- **State-transition API**: `ClaimTransitioner.request_transition()` is sole status promoter
- **State ≠ execution**: Exit code 0 means RUN, not VALIDATED

## Usage

```bash
python3 check-invariants.py           # All checks
python3 check-invariants.py --summary # Quick status
python3 check-invariants.py --check-template
python3 check-invariants.py --state phase Phase-C
```
