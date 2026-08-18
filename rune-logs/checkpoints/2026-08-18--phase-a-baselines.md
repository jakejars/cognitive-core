# 2026-08-18 — Session Resumption: After Phase A Baselines

## Situation Summary

Cognitive Core Gen-2 is operational. We have:
- Both models downloaded (MiniCPM5-1B @ 2.0GB, Qwen3.5-4B @ 8.9GB)
- Working MLX harness with generation, benchmarking, timing
- Grammar-constrained tool intent framework implementing Substrate Spec §3
- Three gauntlet families defined (substrate M01-M12, memory LCTX01-LCTX10, stateful SA01-SA08)
- B1 baseline measured (102.5 tok/s, 1.36s mean, 24 layers)
- B2 baseline measured (29.2 tok/s, 7.79s mean, 32 layers, includes thinking tokens)
- Preliminary constants estimated
- Git repository with 29 files committed

## Last Operations

- Ran `phase_a_runner.py` — full B1 vs B2 comparison on factual/reasoning/coding/explanation prompts
- Saved results to `ledger/baselines/b1-minicpm5-1b.json` and `b2-qwen3.5-4b.json`
- Updated Phase A workbook and constants with preliminary values

## Active Phase

**Phase A** — ~40% complete. Items 1-4 done; items 5-10 pending.

## Blockers

- Need to design task-level evaluation format before we can run gauntlet tests
- Need to decide Phase B implementation approach (build substrate from scratch or adapt existing Modus code?)

## Suggested First Action

1. **Design the gauntlet task format.** I suggest JSONL files where each line defines a task with prompt, expected behaviour pattern, and success criteria function. This lets us evaluate both B1 and B2 (and later S1, S2) consistently.

2. **Implement a mini-gauntlet runner** that loads tasks from JSONL, runs them through the harness, and scores results.

3. **Run M01-M03 and LCTX01-LCTX03** to get proper head-to-head capability comparison.

Then freeze constants and decide Phase B strategy.

## Important Context for Resumption

- **Virtual environment:** `source .venv/bin/activate` from project root
- **Run harness tests:** `cd /Users/jake/Projects/cognitive core && python3 harness/phase_a_runner.py`
- **Latest commit:** `640bc46` — "Initial project setup: specs, harness, intents, gauntlets, ledger, Phase A baselines"
- **Model paths:** `models/MiniCPM5-1B/`, `models/Qwen3.5-4B/`
- **Key spec sections for Phase A:** Research Contract §6 (Phase A work items), §3 (pre-registration rules), §4 (budgets)