# Research Ledger — Cognitive Core Gen-2

This ledger tracks all pre-registrations, baseline measurements, frozen constants, amendments, and budget allocations across all phases. It is the **authoritative record** required by the Research Contract.

## Contents

| File | Purpose |
|---|---|
| `experiment-ledger.md` | Every run: hypothesis, config diff, metrics, keep/revert, reason |
| `constants.md` | Frozen Phase-A exit constants (C_success, C_memory, C_latency, C_trust) |
| `budgets.md` | Phase budget ledgers (wall-clock, researcher, compute, experiments) |
| `amendment-log.md` | Any change to the Research Contract, with date, reason, and untouched evaluation source |
| `baselines/` | Measured B1, B2, S1, S2 baseline results per milestone |
| `lockbox/` | Protected evaluation definitions (never used during development) |

## Rules (from Research Contract §3, §11)

- The form of victory is frozen **before** Phase B begins
- No later phase starts without a ledger entry with entry_gate, exit_gate, and budgets
- Every run records: hypothesis, code/config diff, dataset/task slice, seed, budget consumed, metrics, keep/revert decision, reason
- Contract amendments require: date, reason, which observed results motivated the change, which metrics/thresholds/gauntlets are affected, whether any previously viewed data becomes invalid, and a new untouched evaluation source