# 2026-08-18 — Phase D: Procedural Learning Pipeline Built; Skills Mined from Real Traces

## Context

Phase C complete (1M token target achieved). Moving to Phase D — procedural learning. Built the full pipeline: trace capture → skill mining → verification → promotion.

## Work Done

### Phase C Completion
- Marked Phase C complete ✅
- MT04 ordered-list fix: added `retrieve_recent()` to ExternalMemory
- S1 multi-turn final: **63.6%** (7/11) vs B1 **36.4%** (4/11) — S1 beats B1 by 27.2pp

### Phase D — Procedural Learning Pipeline
- **`substrate/trace_capture.py`** — Execution DAG capture with node-level granularity. Records intents, model calls, results, and their parent-child relationships.
- **`substrate/skill_miner.py`** — Contiguous sub-sequence mining. Finds all repeated patterns across traces with interface inference (inputs, outputs, effects).
- **`substrate/skill_verifier.py`** — 4-gate promotion pipeline: min_length, min_frequency, success_rate, duration. Verdicts: promote, shadow, quarantine, reject.
- **`substrate/runtime.py`** — Integrated with `start_trace()`, `end_trace()`, `mine_skills()`, `record_trace_node()`

### EXP-007: Full Pipeline Test
- 10 gauntlet tasks traced through the substrate
- 3 skills promoted from traces:
  - `gauntlet_task → generate → evaluate` (full pipeline, freq=10)
  - `gauntlet_task → generate` (intent + inference, freq=10)
  - `generate → evaluate` (inference + evaluation, freq=10)
- Skills registered in SkillRegistry with metadata

## Current State
- Phase A: ✅ Complete
- Phase B: ✅ Complete
- Phase C: ✅ Complete
- Phase D: 🔄 ~55% complete (6/11 items)

## Next Steps
1. Failure-derived guards (item 7) — learn from failed traces
2. Held-out counterfactual promotion (item 8) — test if promoted skills actually improve performance
3. Resonance + quality separation (item 9)
4. Then Phase G — deployment optimisation (4-bit MLX, latency tuning)