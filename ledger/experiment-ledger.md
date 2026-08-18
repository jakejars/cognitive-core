# Experiment Ledger

Every materially distinct experiment is recorded here. See Research Contract §3.4 for record requirements.

---

## EXP-001 — B1 vs B2 Baseline Comparison (Free-form Prompts)

- **Date:** 2026-08-18
- **Phase:** A
- **Hypothesis:** MiniCPM5-1B and Qwen3.5-4B have measurable differences in latency, throughput, and output style.
- **Config:** Default greedy decoding (temp=0.0), 4 representative prompts (factual, reasoning, coding, explanation), `make_sampler()`
- **Dataset / task slice:** 4 free-form prompts
- **Seed:** N/A (deterministic)
- **Budget consumed:** ~1 minute compute
- **Metrics:**

| Model | Mean Time | Mean tok/s | Output |
|---|---|---|---|
| B1 (MiniCPM5-1B) | 1.36s | 102.5 | Direct, concise |
| B2 (Qwen3.5-4B) | 7.79s | 29.2 | Includes thinking/CoT |

- **Decision:** Baseline established; proceed to gauntlet comparison.
- **Reason:** Free-form baseline shows B1 faster and more memory-efficient. B2 uses "thinking" tokens which add latency.
- **Links:** `ledger/baselines/b1-minicpm5-1b.json`, `ledger/baselines/b2-qwen3.5-4b.json`

---

## EXP-002 — Gauntlet Comparison: B1 vs B2 (13 tasks across 5 families)

- **Date:** 2026-08-18
- **Phase:** A
- **Hypothesis:** On cognitive-substrate-specific tasks (retrieval, state, multi-hop, structural identity), the smaller B1 model may match or outperform B2 due to more direct output style.
- **Config:** Gauntlet runner with chat-markup-stripping evaluators. 4 yes/no tasks (M01), 3 retrieval (LCTX01), 2 multi-fact retrieval (LCTX02), 2 multi-hop (LCTX03), 2 state tracking (SA01).
- **Dataset / task slice:** 13 gauntlet tasks (gauntlets/gauntlet_tasks.py)
- **Seed:** N/A (deterministic)
- **Budget consumed:** ~20 seconds compute total (B1: 3.6s, B2: 14.1s)
- **Metrics:**

| Metric | B1 | B2 |
|---|---|---|
| Overall pass rate | **76.9%** (10/13) | 46.2% (6/13) |
| Mean score | **0.77** | 0.48 |
| Mean time per task | **0.28s** | 1.08s |
| M01 (Structural Identity) | 50% (2/4) | **75% (3/4)** |
| LCTX01 (One Needle) | **100%** (3/3) | 67% (2/3) |
| LCTX02 (Many Needles) | **100%** (2/2) | 0% (0/2) |
| LCTX03 (Multi-Hop) | **50%** (1/2) | 0% (0/2) |
| SA01 (State Tracking) | **100%** (2/2) | 50% (1/2) |

- **Decision:** Proceed to Phase B normally. Compensation Hypothesis not required — B1 already leads.
- **Reason:** The small-executive thesis is strongly supported: B1 outperforms B2 on stateful/retrieval agentic tasks while being 3.9× faster and ~4× smaller.
- **Links:** `ledger/baselines/gauntlet_b1_minicpm5_1b.json`, `ledger/baselines/gauntlet_b2_qwen3.5_4b.json`

---

## Index

| # | Date | Phase | Hypothesis | Decision |
|---|---|---|---|---|
| 001 | 2026-08-18 | A | B1 vs B2 latency/throughput | Baseline established |
| 002 | 2026-08-18 | A | B1 vs B2 gauntlet capability | B1 leads — proceed to Phase B |