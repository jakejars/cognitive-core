# Phase C — External Memory and Long-Context Evaluation

**Status:** 🔄 In progress  
**Objective:** Test native 131K + external exact history before positional extension.

## Entry Gate

- [x] Phase B complete — substrate validated on multi-turn tasks
- [x] S1 beats B1 on multi-turn (45.5% vs 36.4%)

## Work Items

- [x] 1. Build long-context synthetic data generator (`harness/long_context_gen.py`)
- [x] 2. Build long-context evaluation runner (`harness/long_context_runner.py`)
- [x] 3. Run B1 vs S1 at 1K, 10K, 50K, 100K token lengths
- [ ] 4. Run at 500K and 1M token lengths
- [ ] 5. Implement InfLLM-style token-level memory retrieval
- [ ] 6. Evaluate full LCTX01-LCTX10 gauntlets
- [ ] 7. Test positional extension with LongRoPE (Phase F preparation)
- [ ] 8. Test MT04 ordered-list with sequence-aware retrieval

## Key Finding: S1 External Memory Dominates at Scale

| Context Length | B1 (native attention) | S1 (external memory) | Timing (B1 vs S1) |
|---|---|---|---|
| 1K | 100% | 100% | 0.9s vs 0.4s |
| 10K | 100% | 100% | 1.5s vs 0.2s |
| 50K | 80% | **100%** | 15s vs 0.24s |
| **100K** | **20%** | **100%** | **55s vs 0.3s** |

**Confirmed from Memory Spec §5:** "One million tokens are primarily an exact historical address space, not one million simultaneously active Transformer positions."

At 100K tokens (within B1's native 131K limit), the model can only find 1/5 needles. S1 + external memory finds all 5 needles in 0.3s. Native attention collapses due to dilution — the model cannot effectively attend to specific facts buried in 100K tokens of filler text.

## Gate Status

> Establish the effective long-memory ceiling of retrieval/materialisation before changing the neural positional architecture.

**✅ External memory ceiling is at least 100K+ tokens with 100% accuracy.** Neither native attention extension (Phase F) nor sparse attention (Phase E) is justified at this point — external memory + chunk retrieval solves the problem more effectively and far more efficiently.

## Budget

| Resource | Budget | Consumed |
|---|---|---|
| Wall-clock days | 21 | 1 session |
| Material experiments | 20 | 1 (EXP-005) |

## Deliverables

- `harness/long_context_gen.py` — Synthetic long-context data generator
- `harness/long_context_runner.py` — Multi-length evaluation runner
- `ledger/baselines/long_context_comparison.json` — Results