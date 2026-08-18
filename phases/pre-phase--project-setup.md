# Pre-Phase: Project Setup

**Status:** ✅ Active  
**Objective:** Establish the project structure, tooling, and conventions needed to begin Phase A.

## Timeline

- **Start:** 2026-08-18
- **Target completion:** TBD (one session)

## Entry Gate

N/A — this is the bootstrap phase.

## Work Items

- [x] Create directory structure
- [x] Copy spec documents into `docs/specs/`
- [x] Set up session log system (`sessions/`)
- [x] Set up rune log system (`rune-logs/`)
- [x] Set up research ledger (`ledger/`)
- [x] Set up phase workbooks (`phases/`)
- [x] Set up gauntlet definitions (`gauntlets/`)
- [x] Create first session entry
- [x] Create first resumption checkpoint
- [ ] Verify tooling: MLX, MiniCPM5-1B access, model download
- [ ] Choose ~4B baseline model (reference: Qwen3.5-4B)

## Exit Gate

All project structure in place; tooling verified; ready for Phase A.

## Budget Status

| Resource | Consumed | Budget |
|---|---|---|
| Wall-clock days | 1 session | 1 session |
| Experiments | 0 | 0 |

## Decisions

- **Session log format:** dated YYYY-MM-DD files with standard sections
- **Rune log types:** training runs (TRAIN-NNN), decisions (DEC-NNN), resumption checkpoints
- **Ledger follows Research Contract §3.4** exactly for experiment records
- **Phase workbooks mirror** the Research Contract phase structure

## Next Actions

1. Verify MiniCPM5-1B is accessible via MLX
2. Verify Qwen3.5-4B or alternative ~4B model access
3. Begin Phase A work items