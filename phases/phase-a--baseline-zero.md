# Phase A — Baseline Zero and Measurement Harness

**Status:** 🔄 In progress  
**Objective:** Reproduce stock MiniCPM5-1B in MLX, benchmark ~4B model, build B1/B2 baselines, freeze constants.

## Entry Gate

N/A — first phase.

## Work Items (from Research Contract §6)

- [x] 1. Reproduce stock MiniCPM5-1B in MLX
- [x] 2. Benchmark a strong ~4B B2 model (Qwen3.5-4B)
- [x] 3. Implement grammar-constrained minimal tool intents
- [x] 4. Build B1/B2 vanilla baselines
- [ ] 5. Measure native context behaviour (long-context tests pending)
- [ ] 6. Freeze dev/replication/lockbox partitions
- [x] 7. Establish p50/p95 latency, memory and task-success distributions (preliminary, needs more runs)
- [ ] 8. Measure experiment throughput
- [x] 9. Preliminary constants estimated
- [ ] 10. Freeze Phase B–G budget ledgers

## Mechanical Gate

> If B2 does **not** dominate B1 on both competence and cost-adjusted efficiency → proceed to Phase B normally.
>
> If B2 **does** dominate both → Phase B may start only with a pre-registered Compensation Hypothesis.

**Preliminary finding:** B1 (1B) is 5.7× faster in inference and 4× smaller in memory than B2 (4B). B2 outputs include thinking/CoT tokens which make it more verbose. Cost-adjusted efficiency likely favours B1 on simple tasks. Full gauntlet evaluation needed before conclusion.

## Infrastructure Built

- **Harness:** `harness/__init__.py` — model loading, generation, benchmarking
- **Intents:** `tools/intents.py` — grammar-constrained semantic intent framework
- **Gauntlets:** `gauntlets/substrate-gauntlets.md`, `gauntlets/long-memory-gauntlets.md`, `gauntlets/stateful-gauntlets.md`
- **Phase A runner:** `harness/phase_a_runner.py` — B1 vs B2 comparison

## Budget Status

| Resource | Consumed | Budget |
|---|---|---|
| Wall-clock days | 1 session | 14 (working default) |
| Experiments | 1 (B1+B2 baseline) | TBD |

## Key Decisions

- **Qwen3.5-4B** chosen as B2 baseline (per Research Contract §13 reference)
- **Chat formats:** MiniCPM uses `<|user|>...<|end|>\n<|assistant|>\n` format; Qwen uses `<|im_start|>...<|im_end|>` format
- **Sampling:** `make_sampler(temp=0.0, top_p=0.0)` for deterministic greedy decoding

## Results Summary

- B1: 24 layers, ~2GB, 102.5 tok/s mean, 0.34s load
- B2: 32 layers, ~8GB, 29.2 tok/s mean, 0.57s load
- B1 is ~5.7× faster on inference, ~4× more memory efficient

## Exit Gate

- [ ] All 10 work items complete
- [ ] Constants frozen in `ledger/constants.md`
- [ ] Phase B–G budgets frozen
- [ ] Compensation Hypothesis decision recorded

## Links

- B1 results: `ledger/baselines/b1-minicpm5-1b.json`
- B2 results: `ledger/baselines/b2-qwen3.5-4b.json`