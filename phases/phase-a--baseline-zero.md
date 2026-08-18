# Phase A — Baseline Zero and Measurement Harness

**Status:** ✅ Complete  
**Objective:** Reproduce stock MiniCPM5-1B in MLX, benchmark ~4B model, build B1/B2 baselines, freeze constants.

## Work Items

- [x] 1. Reproduce stock MiniCPM5-1B in MLX
- [x] 2. Benchmark a strong ~4B B2 model (Qwen3.5-4B)
- [x] 3. Implement grammar-constrained minimal tool intents
- [x] 4. Build B1/B2 vanilla baselines
- [x] 5. Measure native context behaviour (13 gauntlet tasks across 5 families)
- [x] 6. Freeze dev/replication/lockbox partitions (7 dev, 3 replication, 3 lockbox)
- [x] 7. Establish p50/p95 latency, memory and task-success distributions
- [x] 8. Measure experiment throughput (221 runs/minute on B1)
- [x] 9. Preliminary constants estimated & recorded in `ledger/constants.md`
- [x] 10. Freeze Phase B–G budget ledgers

## Mechanical Gate

✅ **Pass — proceed to Phase B normally.** B1 dominates B2 on both competence (76.9% vs 46.2%) and cost-adjusted efficiency (3.9× faster, 4× smaller). No Compensation Hypothesis needed.

## Key Results

| Metric | B1 (MiniCPM5-1B) | B2 (Qwen3.5-4B) |
|---|---|---|
| Overall pass rate | **76.9%** (10/13) | 46.2% (6/13) |
| Mean time per task | **0.28s** | 1.08s |
| Experiment throughput | **221 runs/min** | — |
| Memory | **~2 GB** | ~8 GB |

## Deliverables

- `harness/__init__.py` — Model harness (load, generate, benchmark)
- `harness/gauntlet_runner.py` — Gauntlet evaluation pipeline
- `harness/gauntlet_evaluators.py` — Scoring functions with chat-markup stripping
- `gauntlets/gauntlet_tasks.py` — 13 tasks across 5 families
- `gauntlets/lockbox_partitions.py` — Dev/replication/lockbox split
- `tools/intents.py` — Grammar-constrained semantic intent framework
- `ledger/experiment-ledger.md` — EXP-001, EXP-002 recorded
- `ledger/constants.md` — Preliminary constants
- `ledger/budgets.md` — Phase A-G budgets frozen

## Phase B Entry Gate Status

| Criterion | Status |
|---|---|
| Phase A complete | ✅ |
| Mechanical gate: B1 dominates | ✅ (no Compensation Hypothesis needed) |
| Budget frozen | ✅ |
| Constants frozen (preliminary) | ✅ |