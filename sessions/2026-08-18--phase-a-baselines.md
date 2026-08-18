# 2026-08-18 — Phase A: Baselines, Harness, Models, Gauntlets, Git Setup

## Context

Continuing from the project initialisation session. The project structure is built, specs are in place, and we're now executing Phase A of the Research Contract — establishing the baseline zero and measurement harness.

## Work Done

### System & Dependencies
- Created Python virtual environment at `.venv/`
- Installed: `huggingface_hub`, `mlx-lm==0.31.3`, `transformers`, `sentencepiece`, `tokenizers`
- Verified: M5 Pro, 48GB RAM, MLX 0.32.0 with Metal GPU

### Model Downloads
- **MiniCPM5-1B** (2.0 GB) → `models/MiniCPM5-1B/`
- **Qwen3.5-4B** (8.9 GB total, 2 shards) → `models/Qwen3.5-4B/`

### Harness (Phase A core)
- Created `harness/__init__.py` — full model loading, generation, benchmarking with timing/token accounting
- Created `harness/phase_a_runner.py` — B1 vs B2 comparison runner
- Created `harness/b2_baseline.py` — Qwen-specific benchmark script
- Fixed MLX-LM 0.31 API: `load()` returns `(model, tokenizer)`, generate uses `make_sampler(temp=, top_p=)` via `sampler=` kwarg

### Tool Intent Framework
- Created `tools/intents.py` — implements Substrate Spec §3 minimal model-emitted intent system
- `Intent` dataclass with YAML-like serialization (operation, arguments, evidence_refs, candidate_dependencies)
- `IntentRouter` for runtime enrichment into `EnrichedNode` with effect classes
- `IntentGrammar` for validation
- Convenience constructors: `search_intent()`, `retrieve_intent()`, `invoke_skill_intent()`, `verify_intent()`, `ask_user_intent()`, `answer_intent()`

### Gauntlets
- Created `gauntlets/substrate-gauntlets.md` — M01 through M12 with success criteria
- Created `gauntlets/long-memory-gauntlets.md` — LCTX01 through LCTX10
- Created `gauntlets/stateful-gauntlets.md` — SA01 through SA08

### Baseline Measurements (B1 vs B2)
Run on 4 representative prompts (factual, reasoning, coding, explanation):

| Metric | B1 (MiniCPM5-1B) | B2 (Qwen3.5-4B) | Ratio |
|---|---|---|---|
| Params | 1.08B | ~4B | 3.7× |
| Layers | 24 | 32 | 1.3× |
| Model memory est. | ~2.0 GB | ~8.0 GB | 4× |
| Load time | 0.34s | 0.57s | 1.7× |
| Mean inference | 1.36s | 7.79s | 5.7× |
| Mean tok/s | 102.5 | 29.2 | 0.28× |

Key observation: Qwen3.5-4B emits thinking/Chain-of-Thought tokens via `<|im_start|>think` which makes it slower but potentially more capable on reasoning tasks. Full gauntlet evaluation needed.

### Ledger & Frozen Constants
- Created preliminary constant estimates in `ledger/constants.md`
- Saved baseline results to `ledger/baselines/b1-minicpm5-1b.json` and `b2-qwen3.5-4b.json`
- Updated `ledger/budgets.md` with Phase A budget structure

### Git
- Initialized git repo, created `.gitignore` (ignores `.venv/`, `models/`, `__pycache__`, `.cache/`)
- First commit: 29 files, 4801 lines of specification and code

## Decisions & Rationale

- **Qwen3.5-4B as B2**: Confirmed per Research Contract §13 reference. It's a strong contemporary ~4B agentic local model.
- **Chat formats**: MiniCPM uses `<|user|>...<|end|>\n<|assistant|>\n` (Llama-style); Qwen uses `<|im_start|>...<|im_end|>` (ChatML-style)
- **Sampling**: Using `make_sampler(temp=0.0, top_p=0.0)` for deterministic greedy decoding in baselines
- **Harness as `__init__.py`**: Moving `harness.py` into `harness/__init__.py` solved import resolution issues when running from the project root
- **Preliminary C_success not yet frozen**: The 4 free-form prompts are not a proper gauntlet — we need the full stateful/agentic evaluation before freezing constants

## Current State

- ✅ Phase A work items 1-4 complete (MLX model, B2 benchmark, tool intents, B1/B2 baselines)
- ⬜ Items 5-10 pending (native context measurement, lockbox partitions, experiment throughput, freeze budgets)
- B1 is clearly faster and more memory-efficient; whether B2's thinking tokens make it more competent awaits gauntlet testing
- Project is under git version control

## Open Questions

- What format should the stateful gauntlet evaluation tasks take? (JSONL? Python harness functions?)
- Should we implement the InfLLM-style external memory (LC0) or implement the substrate bridge (Phase B) first?
- What are the actual task-success metrics we want to measure? (We need task-specific success criteria per gauntlet)

## Next Steps

1. Design task format for gauntlet evaluation (JSONL task definitions)
2. Implement mini-gauntlet runner that evaluates both B1 and B2 on M01-M03 and LCTX01-LCTX03
3. Measure native context behaviour at various lengths (1K, 10K, 50K, 131K)
4. Freeze dev/replication/lockbox partitions
5. Calibrate and freeze C_success, C_memory, C_latency, C_trust constants

Then proceed to Phase B — minimal substrate bridge implementation.