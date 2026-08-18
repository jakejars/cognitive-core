# Reclassification v2.2 — Evidence Freeze and Status Correction

**Date:** 2026-08-18 (retrospective reclassification)
**Authority:** Independent protocol audit against Cognitive Core Research Contract v2.2
**Status:** This document freezes all prior EXP records and reclassifies them. It does not delete or overwrite any original data.

---

## 1. Purpose

This document preserves all original experiment outputs (EXP-001 through EXP-010) as auditable history while formally reclassifying them from `CONFIRMED` / `PHASE COMPLETE` / `THESIS PROVEN` to `DEV / EXPLORATORY EVIDENCE`.

The reclassification is required because the original experiments contain protocol violations that make their scientific conclusions unreliable under the terms of the Research Contract v2.2.

## 2. Original Classification (Withdrawn)

| Claim | Original Status | Corrected Status |
|---|---|---|
| All 7 phases complete | CONFIRMED | **WITHDRAWN** — see §3 |
| Thesis proven | CONFIRMED | **WITHDRAWN** — see §3 |
| EXP-001–010: valid experimental results | COMPLETED | **DEV / EXPLORATORY** |
| B1 > B2 (small executive beats larger model) | SUPPORTED | **UNRESOLVED** — invalid B2 comparison |
| S1 > B1 (substrate helps) | SUPPORTED | **AMBIGUOUS** — no S2 baseline |
| Million-token cognitive capability | SUPPORTED | **UNRESOLVED** — retriever validated, cognition not tested |
| Phase D complete | COMPLETED | **GATE NOT PASSED** — no fresh-task delta |

## 3. Protocol Violations Found

### 3.1 B2 Chat Template Mismatch (Contract §2, §3.4)

**Evidence:**
- All 13 gauntlet tasks in `gauntlets/gauntlet_tasks.py` hardcode `"chat_template": "minicpm"` (lines 27, 38, 49, 60, 77, 88, 99, 116, 127, 143, 154, 171, 183).
- `gauntlet_runner.py` line 42 reads `task.get("chat_template", "minicpm")` with no per-model override.
- When `--both` mode runs B2 (Qwen3.5-4B), it receives MiniCPM-style `<|user|>\n{prompt}<|end|>\n<|assistant|>\n` formatting instead of Qwen's native `<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n`.
- Qwen's `tokenizer_config.json` (line 285) defines a `chat_template` using `<|im_start|>` tokens; MiniCPM has no `chat_template` field and uses `<|user|><|end|>` natively.

**Impact:** B2's reported 46.2% pass rate on gauntlet tasks is unreliable evidence for comparison. The contract requires functionally equivalent evaluation conditions (model class, tools, budgets, evaluation conditions), which were not met.

**Note:** `phase_a_runner.py` (lines 85-94) correctly uses per-model templates, but only for 4 free-form prompts. The gauntlet runner was not similarly configured.

### 3.2 Missing S2 Experiment (Contract §2, §3.4)

**Evidence:**
- The experiment ledger (EXP-001–010) contains no S2 experiment.
- No S2 runner, results file, or session transcript exists anywhere in the project tree.
- `gauntlets/gauntlet_tasks.py`, `harness/s1_runner.py`, and all session checkpoints reference only B1, B2, and S1.

**Impact:** The mandatory experimental design is B1/S1/B2/S2. S1−B1 tests whether the substrate helps MiniCPM; S2−B2 tests whether it also helps a stronger (4B) model. **S1 vs S2** is the actual small-executive thesis test. Without S2, the project cannot distinguish "small executive + substrate is special" from "this substrate would be even better with the 4B model." The contract definition of `CONFIRMED` requires all four cells.

### 3.3 Lockbox Contamination (Contract §3.1)

**Evidence:**
- Three tasks were designated as `LOCKBOX` in `gauntlets/lockbox_partitions.py` (lines 41-45):
  - `M01-004` — semantic difference
  - `LCTX01-003` — conversation retrieval
  - `SA01-002` — configuration state
- These tasks were evaluated in ALL prior experiments:
  - **B1 run**: M01-004 (passed=false), LCTX01-003 (passed=true), SA01-002 (passed=true)
  - **B2 run**: M01-004 (passed=false), LCTX01-003 (passed=true), SA01-002 (passed=false)
  - **S1 run**: M01-004 (passed=false), LCTX01-003 (passed=true), SA01-002 (passed=true)
- Lockbox partitions were created `after` experiments were run.

**Impact:** Under the contract's own definition (§3.1), lockbox tasks must "never have been used for model selection, prompt tuning, coefficient tuning, skill mining, retrieval-index construction, or synthetic-data generation." Since these tasks were already evaluated, they are no longer valid lockbox items. The DEV/replication/lockbox partition is invalidated.

### 3.4 LCTX Suite Incomplete (Memory Spec §T1–T10)

**Evidence:**
- The LCTX gauntlet results file (`ledger/baselines/lctx_gauntlet_results.json`) reports only: LCTX01, LCTX02, LCTX04, LCTX05, LCTX09.
- Missing: LCTX03 (multi-hop), LCTX06 (distant procedure recall), LCTX07 (file evolution), LCTX08 (provenance), LCTX10 (compression parity).
- The 5 implemented tests grade retrieval string presence, not the model's ability to reason over retrieved information.
- Token counts in LCTX tests use `len(text.split())` rather than model tokenizer.

**Impact:** The million-token claim validates a retriever, not a cognitive system. The contract's Memory Spec explicitly calls for latest-state, supersession, provenance, procedure recall, and strong distractor resistance tests because ordinary needle retrieval is insufficient.

### 3.5 Phase D Gate Not Passed (Contract §6 — Phase D)

**Evidence:**
- The skill miner/verifier pipeline was built (EXP-007), but EXP-008 reports "skills accurate but trivial for single-turn tasks."
- No fresh-task A/B counterfactual evaluation was performed.
- The Phase D gate (§6 — Phase D) requires "promoted procedures must improve fresh held-out tasks, not merely compress recurring traces."

**Impact:** Phase D implementation is a useful prototype, but the scientific gate was not passed.

### 3.6 Phase E/F Skipped Without Contract Amendment (Contract §11)

**Evidence:**
- The final checkpoint (`rune-logs/checkpoints/2026-08-18--all-phases-complete.md`) reports: "Phase E — Skipped, Phase F — Skipped" with the reason "Not needed (DEC-001)."
- DEC-001 states external memory beats native attention.
- The contract §11 requires formal amendment process for phase skipping.

**Impact:** Phases E and F may indeed be skippable, but the contract's amendment record was not followed. This is a minor violation compared to the above, but it sets a precedent for protocol self-amendment.

## 4. Reclassified Experiment Register

Each original experiment retains its original data. The reclassification below replaces the scientific interpretation.

| # | Original Title | New Classification | Specific Issue |
|---|---|---|---|
| EXP-001 | B1 vs B2 latency/throughput | **DEV / exploratory** | Valid measurement, but B2 configured differently; not comparable |
| EXP-002 | B1 vs B2 gauntlet capability | **DEV / exploratory** | **Invalid** — B2 received MiniCPM chat template |
| EXP-003 | S1 vs B1 single-turn | **DEV / exploratory** | Useful prototype, but S2 missing prevents conclusion |
| EXP-004 | Multi-turn S1 vs B1 | **DEV / exploratory** | Promising delta, but no B2/S2 comparison |
| EXP-005 | Long-context B1 vs S1 | **DEV / exploratory** | Retriever validation, not cognition; missing LCTX tests |
| EXP-006 | 1M token scaling + LCTX suite | **DEV / exploratory** | Retriever validated at scale; model-over-retrieval not tested |
| EXP-007 | Procedural learning pipeline | **DEV / exploratory** | Implementation prototype complete |
| EXP-008 | Counterfactual skill evaluation | **DEV / exploratory** | Gate not passed — no fresh-task delta |
| EXP-009 | 4-bit MLX quantisation | **DEV / exploratory** | Valid engineering measurement |
| EXP-010 | Phase G completion | **DEV / exploratory** | Escalation/assessment records |

## 5. Preserved Evidence

The following files constitute the original evidence and are preserved without modification:

- `ledger/experiment-ledger.md` — Original experiment records
- `ledger/baselines/` — All 8 baseline JSON files
- `rune-logs/checkpoints/` — All 9 checkpoint files
- `rune-logs/decisions/` — Decision records
- `sessions/` — Session transcripts
- All harness, substrate, gauntlet, and tools source code

**This reclassification layer is additive.** No original file is overwritten or deleted.

## 6. Current Project Status (Corrected)

| Dimension | Assessment |
|---|---|
| Implementation feasibility | Demonstrated — working MLX harness, substrate, external memory |
| Substrate prototype | Demonstrated — 9-module runtime with event ledger, provenance |
| External-memory retrieval | Encouraging — 1M keywords retrieved in 17ms |
| Phase D infrastructure | Implemented — gate not passed |
| Small-executive hypothesis | **Unresolved** — B2 comparison invalid; S2 missing |
| Substrate-general hypothesis | **Unresolved** — S2 missing |
| Million-token cognitive capability | **Unresolved** — retriever works, cognition not tested |
| Quantisation path | Demonstrated — 4-bit at 580MB |

**Core thesis withdrawn pending confirmation campaign.**

## 7. Required Confirmation Campaign

A new confirmation campaign must satisfy all of the following before any `CONFIRMED` or `THESIS PROVEN` claim can be re-entered:

1. **Model evaluation:** Each checkpoint uses its native tokenizer, chat template, and appropriate reasoning/token-budget configuration.
2. **Fresh task sets:** New untouched replication and lockbox task sets, with hashes recorded before any evaluation.
3. **B1/B2 baselines:** Properly configured with functionally equivalent evaluation conditions.
4. **S1/S2 full matrix:** B1, B2, B1+substrate, B2+substrate — all four cells.
5. **Complete LCTX01-10:** End-to-end model-answer grading, not retrieval string presence.
6. **Phase D gate:** Fresh held-out task A/B comparison with procedural skills.
7. **Executable invariants:** The harness must fail closed when protocol invariants are violated.