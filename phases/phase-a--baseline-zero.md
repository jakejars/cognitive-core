# Phase A — Baseline Zero and Measurement Harness

**Status:** 🔄 In progress (~70%)  
**Objective:** Reproduce stock MiniCPM5-1B in MLX, benchmark ~4B model, build B1/B2 baselines, freeze constants.

## Entry Gate

N/A — first phase.

## Work Items (from Research Contract §6)

- [x] 1. Reproduce stock MiniCPM5-1B in MLX
- [x] 2. Benchmark a strong ~4B B2 model (Qwen3.5-4B)
- [x] 3. Implement grammar-constrained minimal tool intents
- [x] 4. Build B1/B2 vanilla baselines
- [x] 5. Measure native context behaviour (13 gauntlet tasks across 5 families)
- [ ] 6. Freeze dev/replication/lockbox partitions
- [x] 7. Establish p50/p95 latency, memory and task-success distributions
- [ ] 8. Measure experiment throughput
- [x] 9. Preliminary constants estimated & recorded in `ledger/constants.md`
- [ ] 10. Freeze Phase B–G budget ledgers

## Mechanical Gate Assessment

> If B2 does **not** dominate B1 on both competence and cost-adjusted efficiency → proceed to Phase B normally.

**Finding:** B1 dominates B2 on these specific gauntlets (76.9% vs 46.2%) AND is faster (0.28s vs 1.08s) AND smaller (~2GB vs ~8GB). Therefore the mechanical gate passes — proceed to Phase B normally. No Compensation Hypothesis needed.

## Infrastructure Built

- **Harness:** `harness/__init__.py` — model loading, generation, benchmarking
- **Intents:** `tools/intents.py` — grammar-constrained semantic intent framework (Substrate Spec §3)
- **Evaluators:** `harness/gauntlet_evaluators.py` — 6 scoring functions with chat-markup stripping
- **Gauntlet Runner:** `harness/gauntlet_runner.py` — loads tasks JSONL, runs B1/B2, produces comparison
- **Tasks:** `gauntlets/gauntlet_tasks.py` — 13 tasks across M01, LCTX01-03, SA01
- **Gauntlet definitions:** `gauntlets/substrate-gauntlets.md`, `long-memory-gauntlets.md`, `stateful-gauntlets.md`

## Budget Status

| Resource | Consumed | Budget |
|---|---|---|
| Wall-clock days | 2 sessions | 14 (working default) |
| Experiments | 2 (baseline + gauntlet comparison) | TBD |

## Key Results

**B1 (MiniCPM5-1B): 76.9% pass rate — 10/13 tasks — 0.28s avg per task**
**B2 (Qwen3.5-4B): 46.2% pass rate — 6/13 tasks — 1.08s avg per task**

B1 outperforms B2 on these cognitive-substrate gauntlets despite being 4× smaller. The B2 "thinking" token overhead is a significant liability for stateful/retrieval tasks.

## Exit Gate

- [ ] All 10 work items complete
- [ ] Constants frozen in `ledger/constants.md` (preliminary values set)
- [ ] Phase B–G budgets frozen
- [x] Compensation Hypothesis decision: **Not needed** — B1 already leads on both competence and efficiency

## Links

- B1 results: `ledger/baselines/b1-minicpm5-1b.json`
- B2 results: `ledger/baselines/b2-qwen3.5-4b.json`
- Gauntlet B1: `ledger/baselines/gauntlet_b1_minicpm5_1b.json`
- Gauntlet B2: `ledger/baselines/gauntlet_b2_qwen3.5_4b.json`