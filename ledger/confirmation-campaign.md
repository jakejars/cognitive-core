# Cognitive Core Gen-2 — Confirmation Campaign Plan

**Date:** 2026-08-18
**Status:** Planned (not yet started)
**Supersedes:** All previous experiment schedules

---

## Prerequisites

Before any experiment runs, the following must be fixed:

### P1. Fix model evaluation
- [ ] `gauntlet_runner.py` `format_chat()` must accept a model parameter (`"minicpm"` or `"qwen"`) instead of reading `chat_template` from task definitions
- [ ] Replace hardcoded `format_chat()` with per-model verified adapters (see `contract/adapters/`)
- [ ] Create verified adapter manifests for MiniCPM5-1B and Qwen3.5-4B with:
  - template_source (apply_chat_template or verified equivalent)
  - golden tokenisation test (known input → expected token IDs)
  - generation config (thinking_mode, max_total_tokens, temperature, stop_policy)
  - template_string (the actual format applied)
- [ ] Record runtime generation config **in the experiment receipt** per Contract §3.4 — do not create a `generation_config.json` simply to satisfy the invariant
- [ ] Explicitly decide: is B2 evaluated with thinking enabled or disabled?
- [ ] Use `tokenizer.apply_chat_template()` for checkpoints that supply one; for MiniCPM (which does not), use a model adapter independently verified against the model's expected format

### P2. Create fresh task sets with exposure ledger
- [ ] Create new DEV gauntlet (minimum 10 tasks, stratified across all gauntlet families)
- [ ] Create new REPLICATION gauntlet (same distribution, different task content)
- [ ] Create new LOCKBOX gauntlet (never seen by any model, never used for tuning)
- [ ] Record SHA-256 hashes of all task prompts/expected outputs BEFORE any evaluation
- [ ] Store task content hashes, partition assignments, and freeze timestamps in `ledger/lockbox-ledger.json`
- [ ] **Lockbox plaintext contents must not be in the research agent's development workspace** — only hashes/manifests live there; protected contents are released to the evaluator only when the final run is authorised
- [ ] Every experiment run produces a cryptographically hashed `ExperimentReceipt` stored in `ledger/receipts/`
- [ ] Apply `python3 check-invariants.py --check-lockbox` before any lockbox evaluation

### P3. Create S2 runner
- [ ] Implement `harness/s2_runner.py` — Qwen3.5-4B + SubstrateRuntime (analogous to `s1_runner.py`)
- [ ] The substrate should operate identically to S1 (same seeding, context compilation, provenance)
- [ ] Only the underlying model changes

### P4. Implement full LCTX suite as capability curve (Contract §6 — Phase C)
- [ ] Implement all LCTX03–10 end-to-end (model answer/action grading, not retrieval string presence)
  - LCTX03 — Multi-hop reasoning over retrieved chunks
  - LCTX06 — Distant procedure recall: retrieve and follow a procedure defined >500K tokens earlier
  - LCTX07 — File evolution tracking: trace how a document changed across 10+ versions
  - LCTX08 — Provenance: answer "where did this fact come from?" for retrieved information
  - LCTX09 — Near-semantic distractors (at least 50 decoys per 100K)
  - LCTX10 — Compression parity: verify summarisation quality parity with native full-context
- [ ] Use actual model tokenizer for token counting, not `len(text.split())`
- [ ] Measure capability curve at: **131K, 200K, 256K, 512K, 1M** tokens
- [ ] **Success is determining the effective ceiling**, not "10/10 at 1M = pass"
  - The Memory/Neural Spec explicitly says 1M is not sacred
  - The Phase C question is: does demand-paged exact memory provide an effective long-memory ceiling sufficient for target workloads?
  - Residual failures may justify native positional work (Phase F), not declare the approach invalid

### P5. Distractor quality (contract §6 — Phase C)
- [ ] LCTX09 distractors must use near-semantic decoys, not unrelated filler text
- [ ] Add at least 50 semantically similar decoys per 100K tokens of filler

### P6. Phase D gate infrastructure (Contract §6 — Phase D)
- [ ] Create fresh held-out tasks for counterfactual evaluation (minimum 5 per axis)
- [ ] Implement A/B evaluation harness: model runs without procedure → with procedure → measure delta
- [ ] Record results in `ledger/counterfactual_eval.json` with protocol_version='2.2', criterion_threshold, and raw paired A/B data

### P7. Freeze Phase-A constants before Phase B (Contract §3.2)
- [ ] Record C_success, C_memory, C_latency, C_trust in `ledger/phase-constants.json`
- [ ] Constants are frozen before any substrate evaluation — the form of victory must not be chosen after seeing substrate results
- [ ] Apply `python3 check-invariants.py --check-constants` before Phase B begins

### P8. Pre-register Compensation Hypothesis if needed (Contract §3.3)
- [ ] If corrected B2 dominates B1 on both competence and cost-adjusted efficiency,
    Phase B may proceed only under a pre-registered Compensation Hypothesis
- [ ] The hypothesis must state: "Proceed because S1 is expected to retain >= X% of B2 success
    while using <= Y% of B2 model-resident memory on multi-session workloads"
- [ ] No vague statement; must have a numeric Axis-3 or efficiency threshold
- [ ] Record in `ledger/compensation-hypothesis.json` with preregistered_at timestamp

### P9. Integrate contract invariants as mandatory gate
- [ ] All experiment runners must use `contract.transition.ClaimTransitioner` to record results
- [ ] No research code may write CONFIRMED, PHASE_GATE_PASS, or SUPPORTED_CLAIM directly
- [ ] `python3 check-invariants.py` must pass non-zero for any material claim
- [ ] The check-invariants exit code is the gate — not advisory
- [ ] Formally decide on Phase E/F skip status through the contract amendment process
- [ ] Record amendment in `ledger/amendment-log.json`
- [ ] Or reopen Phases E/F with minimal scope

---

## Campaign Structure

### Phase A′ — Corrected Baselines

| Experiment | Purpose | Comparison |
|---|---|---|
| EXP-A1 | B1 on fresh DEV gauntlet | Measure baseline pass rate |
| EXP-A2 | B2 on fresh DEV gauntlet (correct template) | Fair B1 vs B2 comparison |
| EXP-A3 | Template parity verification | Confirm both models receive native formatting |

**Gate:** Both B1 and B2 report pass rates with recorded model config. Verify invariants: `python3 check-invariants.py --check-template && python3 check-invariants.py --check-model-config`

### Phase B′ — Substrate Treatment

| Experiment | Purpose | Comparison |
|---|---|---|
| EXP-B1 | S1 on fresh DEV gauntlet | S1 vs B1 (does substrate help MiniCPM?) |
| EXP-B2 | S2 on fresh DEV gauntlet | S2 vs B2 (does substrate help Qwen?) |

**Gate:** All four cells of the matrix (B1, B2, S1, S2) complete on identical tasks. 
Verify invariants: `python3 check-invariants.py --check-matrix`

### Phase B′-D′ — Replication and Lockbox

| Experiment | Purpose | Comparison |
|---|---|---|
| EXP-C1 | B1, B2, S1, S2 on REPLICATION gauntlet | Confirm results replicate |
| EXP-C2 | B1, B2, S1, S2 on LOCKBOX gauntlet | Untouched final evaluation |

**Gate:** Lockbox tasks have never been used for any development. Hashes match pre-recorded values.
Verify invariants: `python3 check-invariants.py --check-lockbox`

### Phase C′ — Long-Memory Evaluation (Full LCTX01-10)

| Experiment | Purpose | Comparison |
|---|---|---|
| EXP-D1 | LCTX01-10 at 131K tokens | Native vs external memory |
| EXP-D2 | LCTX01-10 at 256K tokens | Scaling behaviour |
| EXP-D3 | LCTX01-10 at 512K tokens | Scaling behaviour |
| EXP-D4 | LCTX01-10 at 1M tokens | Million-token target |

**Gate:** Measure the effective long-memory ceiling across 131K–200K–256K–512K–1M.
Success is determining whether demand-paged exact memory provides a sufficient ceiling
for target workloads and whether residual failures justify native positional work (Phase F).
Token counts use actual model tokenizer. Contract §6 — Phase C.

### Phase D′ — Procedural Learning Gate

| Experiment | Purpose | Comparison |
|---|---|---|
| EXP-E1 | Multi-step trace mining from session history | Skill discovery |
| EXP-E2 | Counterfactual A/B on fresh held-out tasks | Procedure delta measurement |

**Gate:** At least one mined procedure produces a statistically meaningful improvement on held-out tasks compared to baseline.
Verify invariants: `python3 check-invariants.py --check-phase-d`

### Phase E/F — Neural / Long-Context (conditional)

- Only entered if Phase C′ results show a specific capability gap that external memory cannot address
- Requires formal contract amendment

### Phase G′ — Deployment

- Already demonstrated (4-bit quantisation)
- May add ONNX / CoreML export if deployment targets require it

---

## How This Differs from the Previous Campaign

| Aspect | Previous Campaign | This Campaign |
|---|---|---|
| Chat template handling | Read from task (always "minicpm") | Per-model verified adapter + golden tokens |
| Comparison cells | B1, B2 (invalid), S1 (no S2) | B1, B2 (correct), S1, S2 via validated receipts |
| Lockbox | Contaminated — tasks run before designation | Exposure ledger, content hashes, pre-freeze check |
| LCTX tests | 5/10 implemented, string-presence grading | 10/10 end-to-end model-answer, capability curve |
| Token counting | `len(text.split())` | Actual model tokenizer |
| Distractors | Broadly unrelated | Near-semantic decoys |
| Phase D gate | Not passed, declared complete | A/B results with pre-registered criterion, raw delta |
| Protocol enforcement | Manual/voluntary CLI | Fail-closed state-transition API + invariants |
| Experiment tracking | File existence | Cryptographically hashed ExperimentReceipt |
| Phase constants | Some values recorded, never enforced | C_success/C_memory/C_latency/C_trust frozen + checked |
| Compensation Hypothesis | Not implemented | Checked if B2 dominates B1 |
| Lockbox content location | In researcher workspace | Only hashes in workspace; contents at final eval |

---

## Invariant Verification Before Any Claim

Before emitting any `CONFIRMED`, `THESIS PROVEN`, or `PHASE COMPLETE`:

```bash
python3 check-invariants.py
```

If this returns non-zero, the claim is blocked. No exceptions.

Individual gates can be checked:

```bash
python3 check-invariants.py --check-lockbox      # Before lockbox evaluation
python3 check-invariants.py --check-matrix       # Before small-executive claim
python3 check-invariants.py --check-template     # Before any cross-model comparison
python3 check-invariants.py --check-model-config # Before any model comparison
python3 check-invariants.py --check-phase-d      # Before Phase D gate claim
```