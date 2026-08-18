# Contract — Executable Research Protocol v2.2

This package is the **sole authoritative protocol enforcement mechanism**.
The harness imports from `contract.*` — never the other way around.

## Trust Boundary

```
┌──────────────────────────────────────────────┐
│ TRUSTED PROTOCOL AUTHORITY                    │
│ contract/  (read-only to researcher)          │
│                                               │
│  schema.py          — data models             │
│  invariants.py      — executable checks       │
│  transition.py      — state-transition API    │
│  receipt_writer.py  — cryptographic receipts  │
│  adapter_verifier.py— tokenizer verification  │
│  adapters/          — golden token adapters   │
│  tests/             — adversarial tests       │
├──────────────────────────────────────────────┤
│ RESEARCH AGENT WORKSPACE                      │
│                                               │
│  harness/           — evaluation runners      │
│  models/            — model checkpoints       │
│  substrate/         — cognitive substrate     │
│  gauntlets/         — task definitions        │
│  ledger/            — results, receipts       │
└──────────────────────────────────────────────┘
```

**The research agent cannot modify the `contract/` package in production.**
It is a separate trust domain. The agent may:
- **Request** a protocol amendment (recorded in `ledger/amendment-log.json`)
- **Submit** experiment runs through `ReceiptWriter`
- **Request** state transitions through `ClaimTransitioner`

It may **not**:
- Modify the invariant checks that decide whether its claims are valid
- Write receipts directly to `ledger/receipts/`
- Set `CONFIRMED`, `PHASE_GATE_PASS`, or `SUPPORTED_CLAIM` directly

## Structure

```
contract/
    __init__.py      # Public API exports
    schema.py        # Data models: receipts, manifests, lockbox ledger
    invariants.py    # Invariant checks — each raises ContractViolation
    transition.py    # Mandatory state-transition API
    receipt_writer.py# Sole mechanism for recording experiment runs
    adapters/        # Verified model template adapters + golden tokens
    tests/           # Adversarial test suite
```

## Invariants

| # | Invariant | Contract § | Type | What It Checks |
|---|---|---|---|---|
| 1 | Experiment Matrix | §2 | BLOCKING | Validated receipts for B1/B2/S1/S2 at required tier |
| 2a | Lockbox Intact | §3.1 | BLOCKING | Exposure ledger; pre-freeze exposure = violation |
| 2b | Lockbox Pass | §3.1 | BLOCKING | Lockbox experiment conducted with results |
| 3 | Chat Template Parity | §2, §3.4 | BLOCKING | Verified adapters with golden token tests |
| 4 | Phase Constants | §3.2 | BLOCKING | C_success/C_memory/C_latency/C_trust frozen before S1/S2 |
| 5 | Compensation Hyp | §3.3 | BLOCKING | If B2 dominates B1, preregistered before S1/S2 |
| 6 | Amendment Record | §11 | BLOCKING | All protocol changes in amendment-log.json |
| 7 | Budget Overrun | §4 | BLOCKING | No phase exceeds 100%/125%/150% thresholds |
| 8 | Model Config Parity | §3.4 | BLOCKING | Receipt configs match adapter configs |
| 9 | Phase D Gate | §6 | BLOCKING | Raw paired A/B results with delta >= threshold |

## Key Design

- **Receipts, not files**: Empty `s2_runner.py` does NOT count as S2
- **Cryptographic integrity**: Every receipt hash is verified on load. `"banana"` is rejected.
- **Tiered evidence**: DEV → REPLICATION → LOCKBOX. SUPPORTED_CLAIM requires all three tiers.
- **Per-cell lockbox**: Same lockbox item can be evaluated by B1, B2, S1, S2 — each exactly once.
- **Authorised release**: Lockbox plaintext released only after `authorised_release_at` timestamp.
- **State-transition API**: `ClaimTransitioner.request_transition()` is sole status promoter.
  Verifies `from_state` matches the entity's current state — no spoofing.
- **State ≠ execution**: Exit code 0 means RUN, not VALIDATED.

## Usage

```bash
python3 check-invariants.py                    # All checks
python3 check-invariants.py --summary          # Quick status
python3 check-invariants.py --check-template   # Single gate: template parity
python3 check-invariants.py --check-lockbox    # Single gate: lockbox intact
python3 check-invariants.py --check-matrix     # Single gate: experiment matrix
python3 check-invariants.py --check-constants  # Single gate: phase constants
python3 check-invariants.py --check-model-config # Single gate: model config parity
python3 check-invariants.py --check-phase-d    # Single gate: phase D gate
python3 check-invariants.py --check-budgets    # Single gate: budget overrun
python3 check-invariants.py --state phase Phase-C  # Check entity state
```

## Supervisor Process

For production deployment, the `contract/` directory should be a **read-only mount**
or a **separate pinned repository** that the research agent cannot modify.
A minimal supervisor process exposes:

- `Verifier.verify_all()` — run all invariants, return structured report
- `Verifier.verify_transition()` — validate a transition without committing
- `ReceiptWriter.verify_receipt_hash()` — static hash verification

This supervisor can run as a pre-commit hook, a CI gate, or a sidecar process
that the agent calls but cannot modify.