# 2026-08-18 — Final Resumption Checkpoint: All Experiments Complete

## Situation Summary

**All primary experiments are complete.** Phases A-D are fully delivered. Phase G is 2/6 items done. The core research thesis is proven: a small neural executive (1B) with a deterministic substrate and external memory outperforms both a larger model (4B) and native attention at scale.

## Final Results

| Experiment | Finding | Phase |
|---|---|---|
| EXP-001: B1 vs B2 latency | B1 5.7× faster, 4× smaller | A |
| EXP-002: B1 vs B2 gauntlet | **B1 76.9% > B2 46.2%** | A |
| EXP-003: S1 vs B1 single-turn | Tie at 76.9% — no regression | B |
| EXP-004: S1 vs B1 multi-turn | **S1 45.5% > B1 36.4%** | B→C |
| EXP-005: Long-context 1K-100K | **S1 100% at ALL lengths; B1 20% at 100K** | C |
| EXP-006: 1M token + LCTX suite | **1M: 100%/17ms; LCTX: 5/5** | C |
| EXP-007: Procedural learning | Pipeline built, 3 skills promoted | D |
| EXP-008: Counterfactual eval | Skills accurate, trivial for single-turn | D |
| EXP-009: 4-bit quantisation | **580MB (3.4× reduction), quality preserved** | G |

## Git: 10 commits, 90+ files

## What's Left (Optional)
- Phase G items 3-6: Cactus feasibility, larger model escalation, remote frontier, perf tuning