# Frozen Constants

These constants are frozen at Phase-A exit and govern all subsequent evaluation.

## Target Constants

| Constant | Symbol | Value | Calibration Basis |
|---|---|---|---|
| Task retention/superiority | C_success | 0.90 | S1 task success ≥ 0.90 × S2 task success (B1 achieves 77% vs B2 46%; target accounts for substrate improvement) |
| Model-memory advantage | C_memory | 0.50 | S1 model-resident memory ≤ 0.50 × S2 model-resident memory (B1 ~2GB, B2 ~8GB; 4:1 ratio supports this) |
| Substrate latency overhead | C_latency | 0.20 | Substrate p95 latency ≤ (1 + 0.20) × vanilla baseline latency (B1 avg 0.28s per task) |
| Trust advantage | C_trust | 0.50 | Effect/provenance/state error rate ≤ 0.50 × vanilla baseline |

## Calibration Basis (Phase A Gauntlets)

Measured B1 vs B2 on 13 tasks across 5 gauntlet families:

| Gauntlet | B1 (MiniCPM5-1B) | B2 (Qwen3.5-4B) | Winner | Notes |
|---|---|---|---|---|
| M01 — Structural Identity | 50% (2/4) | **75% (3/4)** | B2 | B2 correctly catches semantic differences |
| LCTX01 — One Needle | **100% (3/3)** | 67% (2/3) | B1 | B2's thinking tokens truncate answers |
| LCTX02 — Many Needles | **100% (2/2)** | 0% (0/2) | B1 | B2 runs out of token budget thinking |
| LCTX03 — Multi-Hop | **50% (1/2)** | 0% (0/2) | B1 | Neither strong at multi-hop |
| SA01 — State Tracking | **100% (2/2)** | 50% (1/2) | B1 | B1 handles state perfectly |
| **Overall** | **76.9% (10/13)** | **46.2% (6/13)** | **B1** | |

| Metric | B1 | B2 | Ratio |
|---|---|---|---|
| Mean time per task | 0.28s | 1.08s | 3.9× faster |
| Total time | 3.6s | 14.1s | 3.9× faster |
| Mean tok/s (free-form) | 102.5 | 29.2 | 3.5× faster |

## Interpretation

**Preliminary finding:** B1 (MiniCPM5-1B) outperforms B2 (Qwen3.5-4B) on these specific cognitive-substrate gauntlets despite being 4× smaller. This supports the small-executive thesis.

The B2 model's "thinking" token overhead is a significant liability — it burns 15-40 tokens per query on thinking formatting before producing an answer, often getting truncated. For stateful agentic tasks where quick retrieval matters, B1's direct style is superior.

**Compensation Hypothesis (if needed):** If B2 dominates on a wider evaluation, the substrate compensation hypothesis is: *"S1 is expected to retain ≥90% of B2 task success while using ≤50% of B2 model-resident memory on multi-session workloads."*

## Freeze Status

- **Date:** 2026-08-18
- **Phase-A Exit:** ⬜ Work items 5 (native context), 6 (lockbox partitions), 8 (experiment throughput), 10 (Phase B-G budgets) still pending
- **Constants recorded above are preliminary estimates** — final freeze occurs when Phase A work items are complete

## Amendments

| Date | Constant | Old Value | New Value | Reason | Session |
|---|---|---|---|---|---|
| | | | | | |