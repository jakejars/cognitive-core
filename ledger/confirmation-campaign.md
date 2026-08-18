# Cognitive Core Gen-2 — Confirmation Campaign Plan

**Date:** 2026-08-18
**Status:** DEV + REPLICATION + LOCKBOX matrices **complete and validated** on local M5 Pro with calibrated adapters; **Phase A′/B′ run done**. Remaining before any claim: Phase C′ (LCTX01–10 capability curve) and Phase D′ (paired counterfactual). Phase B exit gate (C_latency) not met; SUPPORTED_CLAIM blocked.
**Supersedes:** All previous experiment schedules

---

## 0. Authoritative execution path

The clean campaign must use:

```bash
python3 harness/confirmation_runner.py \
  --cell B1|B2|S1|S2 \
  --partition dev|replication|lockbox \
  --task-file /path/to/frozen-taskset.json \
  --seed 0
```

`gauntlet_runner.py`, `s1_runner.py`, and `s2_runner.py` are compatibility wrappers around this path. Do not create a second model-specific evaluation path.

The confirmation runner owns:

- partition loading;
- model adapter rendering;
- generation configuration;
- task/result/model/tokenizer/config hashing;
- identical S1/S2 substrate policy;
- lockbox exposure/evaluation accounting;
- fail-closed `ExperimentReceipt` creation.

A convenience result file is written only **after** the authoritative receipt succeeds.

---

## 1. Pull and verify protocol machinery first

On the target Mac:

```bash
git fetch origin
git switch fix/protocol-hardening-final
git pull --ff-only

python3 -m pytest -q contract/tests harness/tests
python3 -m compileall -q contract harness
```

Do not run confirmation models until these pass locally.

Then verify the actual local tokenizers/adapters:

```bash
python3 check-invariants.py --check-template
```

### Qwen calibration rule

Qwen3.5-4B now renders through its tokenizer's native `apply_chat_template()` with `enable_thinking=false`. The committed golden rendering/token IDs are deliberately fail-closed: **if the local pinned tokenizer renders differently, stop and inspect the official/local template.** Update the adapter's golden fixture only after establishing that the local tokenizer/checkpoint is the intended one. Never weaken the verifier to make a mismatch pass.

Pin the actual Qwen checkpoint revision in `contract/adapters/qwen3.5-4b.json` rather than leaving `revision: main` once the local checkpoint identity is known. Confirmatory receipts also hash the exact local weight and tokenizer bytes.

---

## 2. Remaining prerequisites before Phase A′

### P1 — Model evaluation plumbing

Implemented in the hardening branch:

- [x] per-model adapters rather than task-defined templates;
- [x] Qwen native `apply_chat_template()` execution path;
- [x] thinking policy is explicit (`false` for the current B2 design);
- [x] exact adapter rendering and token IDs are checked against the local tokenizer;
- [x] recorded stop tokens / temperature / top-p / answer budget / seed are passed to inference;
- [x] B1/B2/S1/S2 share one runner;
- [x] receipt failure is authoritative failure, not a legacy fallback.

Still required locally:

- [ ] verify both adapters against the actual installed checkpoints;
- [ ] pin Qwen revision after local checkpoint verification.

### P2 — Fresh protected task sets

Still required:

- [ ] create a fresh DEV gauntlet, stratified across the target families;
- [ ] create a separate REPLICATION gauntlet with different task content;
- [ ] create a separate LOCKBOX gauntlet;
- [ ] freeze full-task SHA-256 hashes before evaluation;
- [ ] record lockbox entries keyed by task ID with `content_hash`, `frozen_at`, `authorised_release_at`, `authorised_cells=[B1,B2,S1,S2]`, and empty per-cell counts;
- [ ] keep **LOCKBOX plaintext outside the research project/workspace**;
- [ ] release the plaintext only at authorised final evaluation.

DEV may technically use historical in-repo gauntlets for exploratory debugging, but **Phase A′ confirmation must use an explicit fresh `--task-file`** so the four cells are bound to one frozen taskset.

REPLICATION and LOCKBOX refuse to run without an explicit task file. LOCKBOX additionally refuses a file located inside the repository.

### P3 — S2

- [x] S2 exists through the same unified runner as S1;
- [x] S1/S2 receive the same substrate policy;
- [x] both S1 and S2 create a required `SubstrateManifest`;
- [x] the invariant compares S1/S2 substrate config hashes/modules.

### P4 — Full LCTX capability curve

Still required before Phase C′ can be claimed:

- [ ] implement all LCTX01–10 end-to-end, with model answer/action grading;
- [ ] implement LCTX03 multi-hop;
- [ ] LCTX06 distant procedure recall;
- [ ] LCTX07 file/version evolution;
- [ ] LCTX08 exact provenance;
- [ ] LCTX09 near-semantic distractors;
- [ ] LCTX10 raw-history/compressed-memory parity;
- [ ] use the actual model tokenizer for history-length construction;
- [ ] measure **131K, 200K, 256K, 512K, 1M**.

The goal remains the measured effective ceiling, not “10/10 at 1M or fail.”

### P5 — Phase D paired counterfactual gate

The verifier is implemented, but the fresh experiment is not:

- [x] aggregate pass rates are reconstructed from counts;
- [x] raw paired outcomes are required;
- [x] baseline/treatment task IDs must be identical and ordered;
- [x] freshness is checked against prior experiment receipts;
- [x] delta must meet the pre-registered threshold;
- [x] one-sided exact paired significance threshold is enforced;
- [ ] create fresh held-out Phase-D tasks;
- [ ] pre-register `criterion_threshold` and `criterion_alpha`;
- [ ] run without procedure vs with procedure and record raw pairs.

### P6 — Freeze Phase-A constants before S1/S2

After corrected B1/B2 DEV results and **before S1 or S2**:

- [ ] freeze `C_success`;
- [ ] freeze `C_memory`;
- [ ] freeze `C_latency`;
- [ ] freeze `C_trust`;
- [ ] record `frozen_at` and calibration basis in `ledger/phase-constants.json`;
- [ ] run `python3 check-invariants.py --check-constants`.

Chronology is enforced against the earliest S1/S2 receipt.

### P7 — Mechanical gate / Compensation Hypothesis

The trigger now uses **matched B1/B2 DEV receipts on the same taskset** and requires measured:

- task success;
- successful tasks / model-resident GB;
- successful tasks / second.

If B2 is non-worse on all three, Phase B may begin only after:

- [ ] a numeric Compensation Hypothesis is written to `ledger/compensation-hypothesis.json`;
- [ ] it includes `preregistered_at`;
- [ ] it names the compensating Axis-3 / efficiency metric and threshold;
- [ ] it is registered before the first S1/S2 receipt.

### P8 — Research budgets

- [x] the executable checker covers wall-clock, researcher days, compute hours, and materially distinct experiments;
- [x] 100% requires `mode: evaluate_best|closed`;
- [x] 125% requires a bounded written exception;
- [x] 150% freezes the phase;
- [ ] add/confirm a Phase F budget entry before Phase A′ exit;
- [ ] maintain current counters from the actual experiment receipts/ledger rather than leaving them static.

### P9 — External supervisor trust boundary

Code integrity is improved, but final-claim authenticity still requires a trust boundary outside the research agent:

- [ ] make `contract/` read-only to the research-agent process, **or** install it from a separate pinned protocol repository;
- [ ] ensure no writable directory can shadow the `contract` Python package;
- [ ] protect the authoritative `ledger/transitions/` append path behind the supervisor;
- [ ] run CI / `check-invariants.py` as a mandatory gate before accepting a claim;
- [ ] pin the contract package/commit hash in the confirmation record.

A self-hash proves integrity after creation; it does not prove that an untrusted researcher authored truthful data. Final lockbox/claim authority belongs to the supervisor.

---

## 3. Campaign sequence

### Phase A′ — Corrected baselines

Use one fresh frozen DEV file and one seed for both cells:

```bash
python3 harness/confirmation_runner.py --cell B1 --partition dev --task-file /path/dev-v1.json --seed 0
python3 harness/confirmation_runner.py --cell B2 --partition dev --task-file /path/dev-v1.json --seed 0

python3 check-invariants.py --check-template
python3 check-invariants.py --check-model-config
```

Then measure the Phase-A mechanical gate and freeze constants/budgets.

### Phase B′ — Substrate treatment

Only after Phase-A constants and any required Compensation Hypothesis are frozen:

```bash
python3 harness/confirmation_runner.py --cell S1 --partition dev --task-file /path/dev-v1.json --seed 0
python3 harness/confirmation_runner.py --cell S2 --partition dev --task-file /path/dev-v1.json --seed 0
python3 check-invariants.py --check-matrix
```

The four cells must have the same taskset hash, ordered task IDs, seed, and answer-token budget. S1/S2 must have the same substrate config hash/modules.

### Replication

Use a second frozen task sample and the pre-registered replication seed:

```bash
python3 harness/confirmation_runner.py --cell B1 --partition replication --task-file /path/rep-v1.json --seed 1
python3 harness/confirmation_runner.py --cell B2 --partition replication --task-file /path/rep-v1.json --seed 1
python3 harness/confirmation_runner.py --cell S1 --partition replication --task-file /path/rep-v1.json --seed 1
python3 harness/confirmation_runner.py --cell S2 --partition replication --task-file /path/rep-v1.json --seed 1
```

Confirmatory receipts bind:

- exact model weight bytes;
- exact tokenizer files;
- adapter hash;
- full task definitions;
- raw model outputs;
- aggregate result;
- code HEAD + working-tree diff;
- preregistration/amendment files;
- generation seed/config.

### Final LOCKBOX

LOCKBOX plaintext must be outside the repo and released only at `authorised_release_at`.

Run every cell exactly once on the identical ordered lockbox taskset:

```bash
python3 harness/confirmation_runner.py --cell B1 --partition lockbox --task-file /secure/outside-repo/lockbox-v1.json --seed 2
python3 harness/confirmation_runner.py --cell B2 --partition lockbox --task-file /secure/outside-repo/lockbox-v1.json --seed 2
python3 harness/confirmation_runner.py --cell S1 --partition lockbox --task-file /secure/outside-repo/lockbox-v1.json --seed 2
python3 harness/confirmation_runner.py --cell S2 --partition lockbox --task-file /secure/outside-repo/lockbox-v1.json --seed 2
```

An attempted model call consumes that cell's authorised lockbox evaluation even if inference or receipt finalisation subsequently fails. Do not rerun a failed lockbox cell by editing the ledger; use the amendment/untouched-evaluation process if the protocol genuinely requires a new final evaluation.

Then:

```bash
python3 check-invariants.py
```

`SUPPORTED_CLAIM` remains blocked unless DEV, REPLICATION, and LOCKBOX all have complete validated B1/B2/S1/S2 matrices and the other applicable contract gates pass.

---

## 4. Phase C′ — long-memory evaluation

After the factorial substrate result is established, implement/run LCTX01–10 as a capability curve:

| History size | Requirement |
|---:|---|
| 131K | native-window reference point |
| 200K | external-memory scaling |
| 256K | external-memory scaling |
| 512K | external-memory scaling |
| 1M | research target, not sacred pass/fail number |

Enter native positional Phase F only if a meaningful residual error class plausibly requires more simultaneous neural token context rather than better retrieval/materialisation.

---

## 5. Phase D′ — procedural learning

For each candidate procedure, evaluate the same fresh task IDs under:

```text
baseline:  model/substrate without candidate procedure
vs
treatment: same model/substrate with candidate procedure
```

Record raw pairs in `ledger/counterfactual_eval.json` along with the pre-registered effect threshold and alpha. Frequency/mining support does not pass the gate by itself.

---

## 6. Claim discipline

The historical EXP-001–010 remain **DEV / exploratory evidence**. They are not retroactively upgraded.

Before emitting any `CONFIRMED`, `THESIS PROVEN`, `SUPPORTED_CLAIM`, or equivalent:

```bash
python3 check-invariants.py
```

A runner completing successfully means a **RUN** occurred. It does not by itself imply replication, lockbox success, a phase gate, or a supported scientific claim.
