# DEC-001 — External Memory Beats Native Attention for Long-Context Retrieval

**Date:** 2026-08-18  
**Phase:** C  
**Status:** ✅ Decision recorded

## Context

Memory Spec §5 proposes that "one million tokens are primarily an exact historical address space, not one million simultaneously active Transformer positions." We tested this by comparing B1 (MiniCPM5-1B with native 131K attention) against S1 (same model + external memory chunk retrieval) at context lengths from 1K to 100K tokens.

## Finding

At 100K tokens (within B1's native 131K limit):
- **B1 (native attention): 20% retrieval accuracy** — found 1/5 needles
- **S1 (external memory): 100% retrieval accuracy** — found 5/5 needles
- **Speed: S1 is 180× faster** (0.3s vs 55s)

| Metric | B1 | S1 |
|---|---|---|
| Accuracy at 100K | 20% | **100%** |
| Time per query | 55s | **0.3s** |
| Memory usage | Full KV cache | Chunk index only |
| Scaling to 1M | Impractical (40GB+ KV cache) | Trivial (4MB raw text) |

## Options Considered

### Option A: Positional Extension (Phase F)
- Extend RoPE to 256K/512K/1M using LongRoPE
- Still requires dense attention over entire context
- KV cache at 1M = ~40GB for 40-layer model (Memory Spec §16)
- **Verdict:** Rejected — doesn't solve the attention dilution problem

### Option B: Sparse Attention (Phase E neural branch)
- Native Sparse Attention or InfLLM-V2-style
- Requires substantial retraining + kernel work
- **Verdict:** Premature — external memory solves the problem simpler

### Option C: External Memory (chosen) ✅
- Simple chunk index + keyword retrieval
- 100% accuracy at all tested lengths
- Negligible memory overhead
- Scales trivially to 1M+ tokens
- Compatible with any model (no retraining needed)

## Chosen Path

**Double down on external memory.** Skip Phase F (positional extension) unless specific use cases require dense cross-referencing over very long spans that chunk retrieval cannot support.

Immediate next steps:
1. Scale external memory to 500K and 1M tokens
2. Implement better chunk indexing (TF-IDF → embeddings)
3. Test InfLLM-style token-level retrieval
4. Run full LCTX gauntlet suite (LCTX01-LCTX10)

## Trade-offs Acknowledged

- External memory cannot perform operations requiring simultaneous attention over very long spans (e.g., "find all mentions of X and compare them")
- Keyword retrieval misses semantic matches — embedding-based retrieval will improve this
- For tasks requiring dense cross-referencing, a small native context window (~8-16K) plus external memory is the recommended architecture

## Links

- EXP-005: Long-context comparison results
- Memory Spec §5: One-million-token memory target definition
- Memory Spec §16: KV cache arithmetic