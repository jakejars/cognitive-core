# Cognitive Core Gen-2 v2.2 — Corrected Status Document

**Date:** 2026-08-18 (revision after protocol audit)
**Supersedes:** All previous "all phases complete" / "thesis proven" conclusion documents
**Classification:** HONEST ASSESSMENT — not a victory claim

---

## Summary

The v2.2 specification set is coherent, the research contract is unusually good at making its thesis falsifiable, and the three specification documents agree internally. The implementation work produced a working MLX harness, event ledger, operation registry, effect classes, provenance machinery, context compiler, external memory, execution traces, skill mining infrastructure, and a quantised MiniCPM deployment path.

However, under the terms of the Research Contract v2.2, the experiments as run do not support the claimed conclusions. Several controls required by the contract were absent or accidentally invalidated.

**The work is best described as a successful DEV/feasibility prototype, not a completed research campaign.**

---

## Honest Status by Phase

### Pre-Phase: Project Setup ✅
- 3 v2.2 specification documents written
- Project structure, git, session templates
- No issues found.

### Phase A: Baselines ❌ — Protocol Violation
**Claimed:** B1 beats B2 76.9% vs 46.2%. Small executive hypothesis supported.
**Actual:** B2 received wrong chat template (MiniCPM format for Qwen model). The 46.2% B2 result is unreliable as comparative evidence. See `ledger/reclassification-v2.2.md §3.1`.
**Corrected Status:** **INVALID** — rerun with correct per-model template handling.

### Phase B: Substrate ⚠️ — Incomplete
**Claimed:** S1 matches B1. Substrate ready.
**Actual:** S1 (MiniCPM + substrate) baseline measured correctly. But S2 (Qwen + substrate) was **never run**. The contract requires B1/S1/B2/S2; S1 vs S2 is the actual small-executive thesis test.
**Corrected Status:** **INCOMPLETE** — S2 must be run before any claim about substrate generality.

### Phase C: External Memory ⚠️ — Overclaimed
**Claimed:** Million-token memory validated. LCTX suite 5/5 passed.
**Actual:** External keyword retrieval reaches 1M tokens with 17ms lookup — encouraging engineering evidence. But:
- Only 5 of 10 required LCTX tests were implemented (missing 03/06/07/08/10)
- The 5 implemented tests grade retrieval string presence, not model cognition over retrieved information
- Token counts use `len(text.split())` not the model tokenizer
- Distractor tests use broadly unrelated filler, not near-semantic decoys
**Corrected Status:** **RETRIEVAL FEASIBILITY DEMONSTRATED** — million-token *cognitive capability* unresol ved.

### Phase D: Procedural Learning ❌ — Gate Not Passed
**Claimed:** Pipeline complete. 3 skills promoted.
**Actual:** Infrastructure works. But the Phase D gate requires "promoted procedures must improve fresh held-out tasks, not merely compress recurring traces" (Contract §6 — Phase D). EXP-008 explicitly reports "skills accurate but trivial for single-turn tasks — no performance delta."
**Corrected Status:** **IMPLEMENTATION PROTOTYPE COMPLETE; SCIENTIFIC GATE NOT PASSED.**

### Phase E: Neural Improvements ⏭️ — Improperly Skipped
**Claimed:** Not needed (DEC-001).
**Actual:** May be correct to skip, but the contract's amendment process was not followed.
**Corrected Status:** **SUSPENDED PENDING PROTOCOL AMENDMENT.**

### Phase F: Long Context Extension ⏭️ — Improperly Skipped
**Claimed:** Not needed (DEC-001).
**Actual:** Same as Phase E.
**Corrected Status:** **SUSPENDED PENDING PROTOCOL AMENDMENT.**

### Phase G: Deployment ✅
**Claimed:** 4-bit quant at 580MB, escalation analysis, Cactus assessment.
**Actual:** Valid engineering work. Quantisation measurements are sound. Escalation analysis and Cactus assessment are exploratory but useful.
**Corrected Status:** **DEV COMPLETE** — deployment path demonstrated.

---

## Honest Status by Experiment

| # | Title | Corrected Status | Key Issue |
|---|---|---|---|
| EXP-001 | B1 vs B2 latency/throughput | DEV — valid measurement, not comparable between models | B2 configured differently; latency diff confounded |
| EXP-002 | B1 vs B2 gauntlet | **INVALID** — B2 received MiniCPM chat template | `gauntlet_runner.py` bug (see reclassification §3.1) |
| EXP-003 | S1 vs B1 single-turn | DEV — useful prototype | S2 missing prevents conclusion |
| EXP-004 | S1 vs B1 multi-turn | DEV — promising delta (45.5% vs 36.4%) | No B2/S2 comparison |
| EXP-005 | Long-context B1 vs S1 | DEV — retriever works, cognition untested | Missing LCTX03/06/07/08/10 |
| EXP-006 | 1M token + LCTX suite | DEV — 1M retrieval validated | Not cognitive evaluation |
| EXP-007 | Procedural learning pipeline | DEV — implementation complete | Infrastructure only |
| EXP-008 | Counterfactual eval | DEV — gate not passed | No fresh-task delta |
| EXP-009 | 4-bit quantisation | DEV — valid engineering | Sound measurement |
| EXP-010 | Phase G completion | DEV — exploratory | Escalation/Cactus notes |

---

## Thesis Status

> **Original claim:** "A small neural executive (1B) plus a deterministic cognitive substrate with external memory reaches a better operating point than a larger model (4B) or native attention alone."

**Corrected status:** **UNRESOLVED.** The thesis may be true, but the experiments conducted cannot distinguish between:
- Small executive + substrate is special
- Substrate helps any model equally
- Substrate does not help (S2 would be needed to rule this in or out)

The external-memory retrieval result provides good evidence that the central "demand-paged cognition" direction is computationally sensible. But millon-token *cognition* was not tested.

---

## What to Keep

The following are genuinely valuable and should not be discarded:

- Working MLX evaluation harness (`harness/`)
- Event ledger and operation registry (`substrate/ledger.py`)
- Effect classes and provenance machinery (`substrate/effects.py`, `substrate/provenance.py`)
- Context compiler (`substrate/compiler.py`)
- External memory with keyword + embedding retrieval (`substrate/external_memory.py`)
- Skill miner and trace analyser (`substrate/skill_miner.py`, `substrate/trace_analyser.py`)
- Execution traces from session history (`substrate/traces/`)
- 4-bit quantised MiniCPM deployment path (`models/MiniCPM5-1B-4bit/`)
- 13 gauntlet task definitions (with chat_template corrected) (`gauntlets/gauntlet_tasks.py`)
- Multi-turn task suite (`gauntlets/multi_turn_tasks.py`)

## What to Discard

The following conclusions are withdrawn:

- "All phases complete" — only Pre-Phase, G, and partial C are complete
- "Thesis proven" — unresolved
- "B1 beats B2" — invalid comparison
- "Phase D complete" — gate not passed
- "Million-token cognitive capability" — not tested

---

## Next Campaign Requirements

Before entering another `CONFIRMED` claim, the project must:

1. **Fix model evaluation** — each checkpoint uses its native tokenizer/chat template and appropriate configuration
2. **Create fresh task sets** — untouched replication and lockbox items with pre-recorded hashes
3. **Run B1 → B2 → S1 → S2** — all four cells of the experimental matrix
4. **Implement and pass all LCTX01-10** with end-to-end model-answer grading
5. **Pass Phase D gate** — fresh-task A/B counterfactual with procedural delta
6. **Implement executable protocol invariants** — harness refuses to emit invalid claims
7. **Formally amend or justify Phase E/F skip** through the contract amendment process

---

## References

- `docs/specs/COGNITIVE-CORE-RESEARCH-CONTRACT-v2.2.md` — Research contract defining the protocol
- `docs/specs/COGNITIVE-SUBSTRATE-SPEC-v2.2.md` — Substrate specification
- `docs/specs/COGNITIVE-MEMORY-AND-NEURAL-SPEC-v2.2.md` — Memory and neural specification
- `ledger/reclassification-v2.2.md` — Detailed reclassification with evidence
- `ledger/experiment-ledger.md` — Original experiment records (preserved)
- `harness/gauntlet_runner.py` — Contains the B2 template bug at lines 32-42
- `gauntlets/gauntlet_tasks.py` — All tasks hardcode `chat_template: "minicpm"`