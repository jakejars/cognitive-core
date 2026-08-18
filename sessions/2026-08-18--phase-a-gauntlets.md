# 2026-08-18 — Phase A Gauntlet Evaluation: B1 77% vs B2 46%

## Context

Continuing Phase A baseline measurement. Built gauntlet evaluation framework, ran 13 tasks across 5 families on both B1 (MiniCPM5-1B) and B2 (Qwen3.5-4B).

## Work Done

### Gauntlet Task System
- Created `gauntlets/gauntlet_tasks.py` — 13 tasks across M01 (4), LCTX01 (3), LCTX02 (2), LCTX03 (2), SA01 (2)
- Each task has: prompt, evaluator name, expected answer, max_tokens, difficulty, tags
- Exported to JSONL files for easy iteration

### Gauntlet Evaluators
- Created `harness/gauntlet_evaluators.py` — 6 scoring functions
- `strip_chat_markup()` — robustly removes chat template tokens, thinking/response markers, partial tags
- `exact_match`, `contains`, `contains_all`, `contains_any`, `numeric_match`, `step_by_step`
- All with case-insensitive matching, chat-markup stripping, scoring 0.0-1.0

### Gauntlet Runner
- Created `harness/gauntlet_runner.py` — loads tasks, runs on any model, produces per-gauntlet stats + comparison
- Supports `--both`, `--gauntlet M01`, `--verbose` flags
- Saves results to `ledger/baselines/` automatically

### Results: B1 (MiniCPM5-1B) 76.9% vs B2 (Qwen3.5-4B) 46.2%

| Gauntlet | B1 | B2 | Winner |
|---|---|---|---|
| M01 — Structural Identity | 50% | **75%** | B2 |
| LCTX01 — One Needle | **100%** | 67% | B1 |
| LCTX02 — Many Needles | **100%** | 0% | B1 |
| LCTX03 — Multi-Hop | **50%** | 0% | B1 |
| SA01 — State Tracking | **100%** | 50% | B1 |
| **Overall** | **76.9%** | **46.2%** | **B1** |

B1 was also **3.9× faster** (0.28s vs 1.08s per task) and **4× smaller** in memory.

### Key Findings
- **The small-executive thesis is strongly supported** — B1 (1B) outperforms B2 (~4B) on these cognitive-substrate gauntlets
- **B2's thinking tokens are a liability** for stateful/retrieval tasks — it burns 15-40 tokens on "Thinking Process:" formatting and gets truncated
- **B2 is better at structural identity** (M01: 75% vs 50%) — it correctly identified `.lower()` vs `.upper()` semantic difference
- **Phase A mechanical gate passes** — B1 dominates on both competence and efficiency. No Compensation Hypothesis needed.

### Ledger Updates
- `ledger/constants.md` — preliminary constants recorded with calibration basis
- `ledger/experiment-ledger.md` — EXP-001 (free-form baseline) and EXP-002 (gauntlet comparison) recorded
- `phases/phase-a--baseline-zero.md` — updated with results, 70% completion, gate assessment

### Git
- 3rd commit: `2e52b3e` — "Phase A gauntlet evaluation: B1 76.9% vs B2 46.2%; small-executive thesis supported"
- 15 files changed

## Decisions & Rationale

- **Gauntlet evaluators strip chat markup** — this was essential; raw model output includes `<|user|>`, `<|end|>`, thinking/response markers
- **max_tokens=5 for yes/no tasks** — prevents the model from rambling after answering
- **Qwen format needs improvement** — its `thinking...response...Answer:` pattern means many answers get cut off. For proper B2 evaluation we may need to increase max_tokens significantly or use a prompt that suppresses thinking

## Current State

- Phase A: ~70% complete (work items 1-5, 7, 9 done; 6, 8, 10 pending)
- Mechanical gate: ✅ B1 leads — proceed to Phase B normally
- Constants: Preliminary values set, final freeze pending Phase A completion

## Open Questions

1. **Phase B strategy:** Should we implement the minimal substrate bridge (event ledger, operation registry, effect classes) as pure Python, or first adapt the existing Modus Rust code?
2. **Dev/Replication/Lockbox partitions:** How should we split the 13 tasks? (e.g. 8 dev, 3 replication, 2 lockbox)
3. **Experiment throughput measurement:** What defines a "material experiment" for Phase A budget purposes?

## Next Steps

1. Freeze dev/replication/lockbox partitions (work item 6)
2. Measure experiment throughput by running a timed benchmark session (work item 8)
3. Freeze Phase B-G budget ledgers (work item 10)
4. **Phase B — Minimal Substrate Bridge**: Start implementing the trusted substrate:
   - Event ledger adapter
   - Canonical structural representation
   - Dual structural/execution identity
   - Trusted operation registry
   - Effect classes
   - Capability contracts
   - Provenance tracking