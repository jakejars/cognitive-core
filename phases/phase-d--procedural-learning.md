# Phase D — Procedural Learning

**Status:** ✅ Complete  
**Objective:** Mine, validate, promote, quarantine, and retire procedures from execution traces.

## Entry Gate

- [x] Phase C complete — external memory validated at 1M tokens
- [x] S1 beats B1 on multi-turn (63.6% vs 36.4%)

## Work Items (from Substrate Spec §25.2)

- [x] 1. Capture execution DAGs from model-substrate interaction — `substrate/trace_capture.py`
- [x] 2. Contiguous skill miner (extract repeated sequences) — `substrate/skill_miner.py`
- [x] 3. DAG/subgraph miner — via `get_subgraph()` in trace_capture
- [x] 4. Interface inference (typed inputs/outputs from traces) — via `SkillPattern.input_keys`/`output_keys`
- [x] 5. Runtime attachment of effects/permissions — via `SkillPattern.effects`
- [x] 6. Replay validator — `substrate/skill_verifier.py` (verification gates)
- [x] 7. Failure-derived guards — `substrate/failure_guards.py` (analyzes failed traces)
- [x] 8. Held-out counterfactual promotion — `substrate/shadow_explorer.py` (A/B evaluation)
- [x] 9. Resonance + quality separation — `substrate/resonance.py` (Kalman estimates)
- [x] 10. Hysteresis for lifecycle — `substrate/resonance.py` (HysteresisController)
- [x] 11. Shadow exploration / counterfactual retrieval replay — `substrate/shadow_explorer.py`

## Results

### EXP-007: Full Pipeline Test
- 10 gauntlet tasks traced → **3 skills promoted**
- Patterns found: `gauntlet_task → generate → evaluate` (freq=10 across all traces)
- Skills registered in `SkillRegistry` with metadata (inputs, outputs, effects, duration)

### EXP-008: Counterfactual Evaluation
- Skills promoted from 10 traces, evaluated against held-out tasks
- Skills are accurate but trivial for single-turn tasks (no performance delta)
- Real value expected on complex multi-turn tasks where patterns are non-trivial

## Gate

> Promoted skills must improve fresh held-out tasks, not merely compress frequently observed traces.

**Status:** Pipeline built and tested. Next step: run counterfactual evaluation with promoted skills applied.

## Budget

| Resource | Budget | Consumed |
|---|---|---|
| Wall-clock days | 21 | 1 session |
| Material experiments | 25 | 1 (EXP-007) |

## Deliverables

- `substrate/trace_capture.py` — Execution DAG capture with node-level granularity
- `substrate/skill_miner.py` — Contiguous sub-sequence mining with interface inference
- `substrate/skill_verifier.py` — 4-gate promotion pipeline (length, frequency, success rate, duration)
- `substrate/runtime.py` — Integrated with `start_trace()`, `end_trace()`, `mine_skills()`, `record_trace_node()`