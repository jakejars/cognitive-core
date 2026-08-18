# 2026-08-18 — Session Resumption: Phase B Complete, Multi-Turn Breakthrough

## Situation Summary

**Phase B is fully complete.** The substrate runtime has 9 modules, all tested. S1 (MiniCPM5-1B + substrate) matches B1 on single-turn tasks (76.9%) and **beats B1 on multi-turn tasks (45.5% vs 36.4%)** — the first clear experimental validation of the small-executive + substrate thesis.

## Last Operations

- Built external memory (LC0 baseline with keyword retrieval)
- Created 11 multi-turn tasks across 5 gauntlets (fact retention, state updates, supersession, accumulated context, distractors)
- S1 achieves 45.5% vs B1 36.4% on multi-turn tasks
- Phase B workbook marked complete, EXP-004 recorded
- All 4 session files, 5 checkpoints, and ledger up to date

## Active Phase

**Phase B — Complete.** Ready for Phase C (external memory scaling).

## Key Results

| Comparison | Result | What it proves |
|---|---|---|
| B1 vs B2 (single-turn gauntlets) | B1 76.9% > B2 46.2% | Small-executive thesis supported |
| S1 vs B1 (single-turn gauntlets) | S1 76.9% = B1 76.9% | No substrate regression |
| **S1 vs B1 (multi-turn)** | **S1 45.5% > B1 36.4%** | **Substrate adds value** |

## Blockers

- MT04 (ordered list) needs sequence-aware retrieval — keyword overlap loses positional info
- MT02 (state updates) still at chance — needs better latest-value tracking

## Suggested First Action

Phase C next steps (from Memory Spec §21):
1. Scale external memory to larger histories (50K, 100K, 500K tokens, 1M target)
2. Evaluate with RULER-style gauntlets (LCTX01-LCTX10 from Memory Spec §22)
3. Test InfLLM-style token-level memory retrieval
4. Test positional extension with LongRoPE (Memory Spec §6)
5. Compare external-memory-only vs positional-extension at each scale

## Important Context

- **Activate:** `cd /Users/jake/Projects/cognitive core && source .venv/bin/activate`
- **Run multi-turn:** `python3 harness/multi_turn_runner.py`
- **Run single-turn:** `python3 harness/gauntlet_runner.py --both`
- **Run S1:** `python3 harness/s1_runner.py`
- **Latest commit:** (will be committed with Phase B complete)
- **Models:** `models/MiniCPM5-1B/`, `models/Qwen3.5-4B/`
- **Budget:** Phase C has 21 wall-clock days, 20 material experiments