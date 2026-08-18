# Gauntlets — Evaluation Definitions

This directory holds the gauntlet definitions used across all phases. Gauntlets are the task families that measure progress toward the research thesis.

## Gauntlet Families

### Substrate Gauntlets (M01–M12)
From Substrate Spec §26 and Research Contract §9. Test structural identity, execution identity, skill mining, harmful frequency, replay, effect safety, failure-aware skills, hysteresis, resonance, context compiler, entropy, conductance.

**File:** `substrate-gauntlets.md`

### Long-Memory Gauntlets (LCTX01–LCTX10)
From Memory Spec §22 and Research Contract §9. Test needle retrieval, many needles, multi-hop, latest state, supersession, procedural recall, file evolution, provenance, distractors, compression parity.

**File:** `long-memory-gauntlets.md`

### Stateful/Agentic Gauntlets
Custom gauntlets for Axis 1 (stateful agentic competence). Multi-session state, long-horizon tool use, effectful workflows, research provenance, latest-state reasoning, procedure reuse, failure recovery, memory-dependent continuation, ask/search/escalate calibration.

**File:** `stateful-gauntlets.md`

## Lockbox

The protected `lockbox/` subdirectory contains evaluation sets that are **never** used during development — not for model selection, prompt tuning, coefficient tuning, skill mining, retrieval-index construction, or synthetic-data generation.

## Gauntlet Format

Each gauntlet definition includes:

```
## {ID} — {Title}

- **Source:** which spec section
- **Description:** what is being tested
- **Task format:** input/output specification
- **Success criteria:** quantitative threshold
- **Difficulty scale:** levels if applicable
- **Provenance requirement:** whether exact evidence must be traceable
```