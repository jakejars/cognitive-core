# 2026-08-18 — Project Initialisation & Structure Setup

## Context

This is the first conversation. Three v2.2 specification documents were downloaded and we need to set up the Cognitive Core Gen-2 project as the sole working folder, with organised documentation, session logging, rune/training logs, and a research ledger so the project can be resumed after any gap.

## Work Done

- Reviewed all three authoritative v2.2 specs from Downloads:
  - **Research Contract** — immutable experimental rules
  - **Substrate Spec** — trusted runtime architecture
  - **Memory/Neural Spec** — MiniCPM, training, memory hierarchy
- Created full directory structure at `/Users/jake/Projects/cognitive core/`:
  - `docs/specs/` — authoritative specification documents
  - `docs/references/` — prior art notes (empty, ready)
  - `sessions/` — per-conversation logs with README template
  - `rune-logs/` — training runs (TRAIN-NNN), decisions (DEC-NNN), resumption checkpoints
  - `ledger/` — experiment ledger, frozen constants, budgets, amendment log, baselines, lockbox
  - `phases/` — one workbook per phase (Pre-Phase, A–G)
  - `experiments/` — experimental designs (empty, ready)
  - `gauntlets/` — evaluation definitions (substrate, memory, stateful)
  - `substrate/` — trusted runtime implementation (empty, ready)
  - `neural/` — MiniCPM/training/retrieval work (empty, ready)
- Copied spec files into `docs/specs/`
- Created Project README
- Created Pre-Phase workbook with setup tasks tracked
- Created Phase A workbook with all 10 work items and mechanical gate listed
- Created resumption checkpoint at `rune-logs/checkpoints/2026-08-18--project-initialisation.md`

## Decisions & Rationale

- **Directory layout follows phase structure** from Research Contract §6 so each phase has a natural home
- **Rune logs** separate from sessions because rune logs are permanent operational records; sessions are conversational logs
- **Constants/budgets/amendments** in the ledger follow Research Contract §3 and §11 exactly — they are the immutable infrastructure
- **Gauntlets directory** matches the two gauntlet families (substrate M01–M12, memory LCTX01–LCTX10) with space for stateful/agentic custom gauntlets

## Current State

- Project structure is complete
- Specs are in place
- No experimental work has been done yet
- We are at Pre-Phase, about to enter Phase A

## Open Questions

- Which specific ~4B model should serve as B2? (Reference: Qwen3.5-4B per Research Contract §13)
- Is MLX available on this system? MiniCPM5-1B access?
- Any preferred compute/researcher budget constraints?

## Next Steps

1. Verify tooling: MLX, MiniCPM5-1B access
2. Confirm ~4B baseline model choice
3. Begin Phase A work items (starting with stock MiniCPM5-1B in MLX and ~4B benchmark)