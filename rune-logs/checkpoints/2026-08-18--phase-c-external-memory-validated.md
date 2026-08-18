# 2026-08-18 — Session Resumption: Phase C — External Memory Validated

## Situation Summary

**Major experimental result:** External memory (S1) achieves 100% retrieval accuracy at ALL tested context lengths (1K-100K). Native attention (B1) collapses to 20% at 100K — even within its advertised 131K context window. This confirms the Memory Spec thesis and justifies the entire external memory approach.

## Last Operations

- Built long-context synthetic data generator and evaluation runner
- Ran EXP-005: S1 100% vs B1 20% at 100K tokens
- Recorded DEC-001: External memory beats native attention — skip Phase F
- Created Phase C workbook (50% complete)

## Active Phase

**Phase C** — 50% complete. Core finding validated. Remaining work:
- Scale to 500K and 1M tokens
- Embedding-based chunk retrieval
- Full LCTX01-LCTX10 gauntlets
- InfLLM-style token-level retrieval

## Key Results

| Experiment | Finding | Significance |
|---|---|---|
| B1 vs B2 (EXP-002) | B1 76.9% > B2 46.2% | Small-executive thesis supported |
| S1 vs B1 single-turn (EXP-003) | Tie at 76.9% | No substrate regression |
| S1 vs B1 multi-turn (EXP-004) | S1 45.5% > B1 36.4% | Substrate adds value |
| **S1 vs B1 long-context (EXP-005)** | **S1 100% > B1 20% at 100K** | **External memory validated** |

## Decisions Made

- **DEC-001:** Double down on external memory. Skip Phase F (positional extension) unless specific dense-cross-referencing tasks require it.

## Blockers

- None. Ready to scale to 500K/1M and implement better indexing.

## Suggested First Action

1. Scale to 500K tokens — is the keyword retrieval still 100%?
2. Install sentence-transformers and add embedding-based chunk retrieval
3. Run full LCTX01-LCTX10 gauntlet suite
4. Test InfLLM-style per-token memory retrieval

## Important Context

- **Activate:** `cd /Users/jake/Projects/cognitive core && source .venv/bin/activate`
- **Run long-context:** `python3 harness/long_context_runner.py`
- **Key file:** `substrate/external_memory.py` — the LC0 baseline that just proved the thesis
- **Decision record:** `rune-logs/decisions/DEC-001--external-memory-beats-native-attention.md`
- **Latest commit:** (will commit with this session)
- **Spec reference:** Memory Spec §5 — "One million tokens are primarily an exact historical address space"