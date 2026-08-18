# 2026-08-18 — Phase C: 1M Token Target Achieved; LCTX Suite 5/5 Passed

## Context

Building on the external memory breakthrough. Scaled to 1M tokens, added embedding-based retrieval, ran full LCTX gauntlet suite.

## Work Done

### 1M Token Scaling 🏆
- **500K tokens:** 5/5 needles found in 7ms
- **1M tokens:** 5/5 needles found in **17ms**
- 5001 chunks, 0.44s store time, 496 keyword entries
- The million-token addressable memory target from Memory Spec §5 is **achieved**

### Embedding-Based Retrieval
- Installed `sentence-transformers` with `all-MiniLM-L6-v2` (384-dim, 80MB)
- Built `substrate/embedding_retriever.py` with lazy model loading
- Added `retrieval_mode` parameter to `ExternalMemory`: `keyword` | `embedding` | `hybrid`
- Hybrid mode combines keyword overlap (30%) + embedding similarity (70%)
- Model loads in ~5s, then retrieval is fast

### LCTX Gauntlet Suite
- Built `harness/lctx_runner.py` — runs LCTX01-10 tests with synthetic contexts
- **5/5 passed:** LCTX01, LCTX02, LCTX04, LCTX05, LCTX09
- Tests latest state tracking, supersession, distractor resistance at 100K tokens

### Experiment Ledger
- EXP-005: Long-context B1 vs S1 (1K-100K) — S1 dominates
- EXP-006: 1M token scaling + LCTX suite — 100% at 1M, 5/5 LCTX

## Current State
- Phase C: ~80% complete (6/8 items; MT04 and LCTX03/06/07/08/10 pending)
- **1M token target achieved** — the core Phase C objective is met

## Next Steps
1. Fix MT04 ordered-list with sequence-aware retrieval
2. Complete remaining LCTX tests (03 multi-hop, 06 procedure recall, 07 file evolution, 08 provenance, 10 compression parity)
3. Phase D — Procedural learning (skill mining from traces)