# Cognitive Core Gen-2 — Research Contract v2.2
## Immutable Experimental Rules for the Small-Executive / Cognitive-Substrate Programme

**Status:** Authoritative research contract  
**Date:** 2026-08-18  
**Scope:** Experimental method, baselines, gates, budgets, success criteria, kill criteria  
**Mutable architecture lives elsewhere:** see the Substrate and Memory/Neural specs  

> **Purpose:** This document is the part of Gen-2 that the research agent is **not allowed to silently rewrite in response to results**. Architecture may evolve; evaluation rules may not. Any change to this contract requires a dated protocol amendment recorded before the affected lockbox evaluation.

> **Falsifiable thesis:** A small neural executive can reach a better operating point than a substantially larger conventional local agent on **stateful, effectful, long-lived agentic work** when paired with deterministic effect handling, provenance, demand-paged exact memory, and validated reusable procedures.

> **Non-claim:** Gen-2 is not trying to prove that small models can perform strong verifiable reasoning. Models such as VibeThinker-3B already make that a poor novelty claim. Generic reasoning remains a regression metric; the primary question is whether a small model can operate a persistent cognitive system.

> **Document set:** This file is one of three authoritative Gen-2 v2.2 specifications.
> 1. `COGNITIVE-CORE-RESEARCH-CONTRACT-v2.2.md` — falsifiable thesis, baselines, gates, budgets, kill rules.
> 2. `COGNITIVE-SUBSTRATE-SPEC-v2.2.md` — trusted runtime, effect/provenance system, procedural cortex.
> 3. `COGNITIVE-MEMORY-AND-NEURAL-SPEC-v2.2.md` — MiniCPM, training, retrieval, and long-memory architecture.

# 1. Research thesis and non-goals

The core intuition is:

> **Do not make the neural model carry all memory, procedures, confidence accounting, authority, and continual learning inside its weights.**

Use a small neural model as an executive over a deterministic cognitive substrate.

The unifying systems principle is:

> **Large capacity, sparse activation.**

```text
WEIGHTS
optional model capacity
→ activate only what is needed

MEMORY
large exact historical address space
→ materialise only relevant state

PROCEDURES
large learned skill library
→ retrieve only relevant validated procedures
```

Gen-2 is **not** initially trying to:

- train a foundation model from scratch;
- make one million tokens participate in dense attention;
- establish novelty for small-model verifiable reasoning;
- replace deterministic execution with learned simulation;
- make a 1B model emit or remember every runtime field;
- deploy Native Sparse Attention by default;
- prove that named neural cartridges are discrete symbolic organs;
- grow a skill library merely because repeated traces exist;
- optimise generic leaderboard scores at the expense of stateful agent reliability;
- beat frontier cloud models at unconstrained intelligence.

The target workloads are deliberately narrower:

```text
multi-session state correctness
long-horizon task completion
effectful tool execution
supersession / temporal consistency
provenance recovery
procedure acquisition and reuse
failure recovery
memory-dependent behaviour
safe escalation / ask / search decisions
```

Generic math, coding, and reasoning benchmarks remain **capability-retention tests**, not the definition of victory.

---

# 2. Factorial baseline design

The two central hypotheses must be separable:

1. **Substrate hypothesis:** does the trusted Modus-derived substrate improve an otherwise fixed model?
2. **Small-executive hypothesis:** given the same validated substrate, can a ~1B executive match or beat the operating point of a stronger ~4B executive?

Therefore the mandatory comparison is a **2 × 2 factorial baseline**, not a one-way ladder.

| Model | Vanilla tools/RAG | Validated full substrate |
|---|---|---|
| **MiniCPM5-1B** | **B1** | **S1** |
| **Strong ~4B local model** | **B2** | **S2** |

Optional:

| Model | Vanilla tools/RAG | Validated full substrate |
|---|---|---|
| **Strong ~8B local model** | **B3** | **S3** |

All cells must use the same, or functionally equivalent:

- tool surface;
- retrieval corpus;
- task budget;
- permissions/effect policy where applicable;
- evaluation harness;
- lockbox tasks.

Interpretation:

```text
S1 - B1
= substrate benefit at ~1B

S2 - B2
= substrate benefit at ~4B

S1 vs S2
= small-executive thesis

expanded ~1.5B + substrate vs S1
= neural-expansion thesis
```

Possible scientifically useful outcomes:

```text
S2 >> S1
→ substrate validated; small-executive thesis weakened/falsified

S1 ≈ S2 at materially lower resident model memory/cost
→ strong evidence for small-executive thesis

S1 > B1 but S2 ≈ B2
→ substrate mainly compensates for small-model weakness

S1 ≈ B1 and S2 ≈ B2
→ substrate complexity is not justified on competence grounds

S1/S2 improve safety/state correctness but not raw task success
→ substrate may still be valuable, but the advantage must satisfy pre-registered thresholds
```

The current B2 should be a strong contemporary ~4B agentic local model, but the identity of B2 is replaceable. The experiment is defined by the class, not one checkpoint. During incremental substrate phases, use stage-qualified cells such as `S1-B`, `S2-B`, `S1-C`, `S2-C`; the full `S1/S2` comparison refers to the validated substrate stack at the frozen milestone.

---

# 3. Pre-registration rules

## 3.1 Protected evaluation layout

Use three evaluation tiers:

```text
DEV GAUNTLET
frequent iteration

REPLICATION GAUNTLET
second seed / second task sample / independent confirmation

FINAL LOCKBOX
never used for model selection, prompt tuning, coefficient tuning,
skill mining, retrieval-index construction, or synthetic-data generation
```

The system must not retrieve from, train on, or mine skills from protected gauntlets.

## 3.2 Relative target forms are frozen before Phase B

Absolute Mac-specific numbers may depend on Phase A measurement, but the **form of victory may not be chosen after seeing substrate results**.

Before Phase B starts, freeze constants for relationships of the form:

```text
TASK RETENTION / SUPERIORITY
S1 task success >= C_success × S2 task success

MODEL-MEMORY ADVANTAGE
S1 model-resident memory <= C_memory × S2 model-resident memory

SUBSTRATE OVERHEAD
substrate-only p95 latency overhead <= C_latency × vanilla baseline latency

TRUST ADVANTAGE
effect/provenance/state error rate <= C_trust × relevant vanilla baseline
```

If a baseline error rate is zero or too sparse for a stable ratio, pre-register an absolute error-rate ceiling instead.

Recommended initial design targets to consider during Phase-A calibration are approximately:

```text
C_success: 0.95–1.00
C_memory:  0.50–0.65
C_latency: 0.20 additional overhead ceiling
```

These are **recommended calibration ranges, not retroactive escape hatches**. The actual constants are entered once in the experiment ledger at Phase-A exit and frozen before substrate evaluation.

## 3.3 Compensation Hypothesis

If B2 dominates B1 on both target-task competence and cost-adjusted systems efficiency, Phase B may proceed only under a pre-registered **Compensation Hypothesis**.

It must state exactly which trustworthy-stateful metric is expected to compensate, and by how much, for example:

```text
"Proceed because the substrate is expected to reduce duplicate/unsafe
external effects by >= X% while retaining >= Y% of B2 task success."
```

or:

```text
"Proceed because S1 is expected to retain >= X% of B2 success while
using <= Y% of B2 model-resident memory on multi-session workloads."
```

No vague statement such as “inspectability may compensate” is sufficient.

## 3.4 One coherent hypothesis at a time

Autoresearch experiments should change one coherent idea at a time unless the experiment is explicitly testing an interaction.

Every run records:

```text
hypothesis
code/config diff
dataset/task slice
seed
budget consumed
metrics
keep/revert decision
reason
```

---

# 4. Research budgets and overrun policy

Research scope is constrained by four budgets per phase:

```text
wall-clock days
researcher/engineer days
compute hours or energy budget
number of materially distinct experiments
```

Phase A itself uses a **working default budget of 14 calendar days** for establishing the baseline harness and empirical experiment throughput. If that is unrealistic for the actual researcher/compute availability, amend it **before the first Phase-A run**, not after seeing results. At Phase-A exit, numeric budgets for later phases must be frozen before Phase B begins.

No later phase may start without a ledger entry of the form:

```yaml
phase: C
max_wall_clock_days:
max_researcher_days:
max_compute_hours:
max_material_experiments:
entry_gate:
exit_gate:
```

Overrun policy:

```text
100% of any phase budget
→ stop open-ended exploration and evaluate the best replicated result

125%
→ continuation requires a written exception tied to one specific
   unresolved hypothesis and a bounded extension

150%
→ freeze the phase; move unresolved ideas to the research backlog
```

Autoresearch does not get an unlimited number of trials merely because individual runs are cheap.

---

# 5. Success axes

Gen-2 has **three primary axes**.

## Axis 1 — stateful agentic competence

Measure successful completion of representative tasks involving:

- multi-session state;
- long-horizon tool use;
- effectful terminal/coding workflows;
- research with exact provenance;
- latest-state / supersession reasoning;
- procedure acquisition and reuse;
- failure recovery;
- memory-dependent continuation after long gaps;
- correct ask/search/escalate behaviour.

Generic reasoning benchmarks are secondary regression tests.

## Axis 2 — systems efficiency

Measure:

```text
successful tasks / model-resident GB
successful tasks / second
TTFT p50 / p95
end-to-end latency p50 / p95
peak resident memory
historic bytes/token
context-compiler overhead
energy/cost per successful task where measurable
```

The small-executive thesis is not validated if S1 is slower, larger in total operating footprint, and no more capable than S2.

## Axis 3 — trustworthy stateful operation

Measure:

```text
effect duplication / unsafe action rate
provenance correctness
latest-state / supersession correctness
citation/evidence correctness
answer-vs-search-vs-ask calibration
skill regression / quarantine behaviour
replay / idempotency correctness
state recovery after interruption
```

Secondary explanatory metrics include reasoning benchmarks, retrieval scores, cartridge probes, resonance statistics, and skill-library size. They do not define success by themselves.

---

# 6. Phase sequence and mechanical gates

## Phase A — baseline zero and measurement harness

1. reproduce stock MiniCPM5-1B in MLX;
2. benchmark a strong ~4B B2 model;
3. implement grammar-constrained minimal tool intents;
4. build B1/B2 vanilla tool + RAG baselines;
5. measure native context behaviour;
6. freeze dev / replication / lockbox partitions;
7. establish p50/p95 latency, memory and task-success distributions;
8. measure experiment throughput;
9. freeze post-A constants (`C_success`, `C_memory`, `C_latency`, `C_trust`);
10. freeze Phase B–G budget ledgers.

**Mechanical gate:**

- if B2 does **not** dominate B1 on both competence and cost-adjusted efficiency, proceed to Phase B normally;
- if B2 **does** dominate both, Phase B may start only if the Compensation Hypothesis has been pre-registered with a numeric Axis-3 or efficiency threshold;
- failure to write such a hypothesis means narrow/stop the small-executive programme and continue only with model-agnostic substrate research if desired.

## Phase B — minimal substrate bridge

Build only enough trusted substrate to test whether deterministic effects/provenance/state provide protected value.

**Gate:** overhead must remain inside the frozen budget and at least one pre-registered trustworthy-stateful metric must improve without violating task-retention constraints.

## Phase C — external memory

Test native 131K + external exact history before positional extension.

**Gate:** establish the effective long-memory ceiling of retrieval/materialisation before changing the neural positional architecture.

## Phase D — procedural learning

Mine, validate, promote, quarantine, and retire procedures.

**Gate:** promoted procedures must improve **fresh** tasks, not merely compress frequently observed traces.

## Phase E — neural improvements

Test retrieval/epistemic heads, identity-preserving depth expansion, SOLAR-style controls, and MoT only after its small replication succeeds.

**Gate:** each neural modification must beat the same model + same substrate without that modification after latency/memory accounting.

## Phase F — optional native long-context research

Enter only when Phase C identifies a failure plausibly caused by insufficient simultaneous neural context.

## Phase G — deployment optimisation

Quantisation/runtime optimisation occurs only after capability and safety are stable.

---

# 7. Kill criteria

Kill or postpone a subsystem when a pre-registered evaluation shows:

```text
repeatable held-out gain is absent
OR
gain disappears on replication seed/task sample
OR
latency or memory violates the frozen budget
OR
calibration / epistemic behaviour worsens materially
OR
safety / effect reliability regresses
OR
procedural reuse harms fresh tasks
OR
retrieval feedback locks out better alternatives
OR
long-memory capacity fails effective-context gauntlets
OR
phase reaches the 150% overrun ceiling
```

A subsystem can be scientifically interesting and still be rejected from the primary architecture.

---

# 8. Multiple-comparisons discipline

- prefer small, pre-registered parameter sweeps;
- retain every failed run in the ledger;
- require replication for material claims;
- use confidence intervals / bootstrap over task success where useful;
- do not repeatedly inspect the final lockbox;
- do not treat hundreds of automated trials against one dev set as independent discoveries;
- use Pareto/non-inferiority logic before scalar weighted scores;
- any protocol change after observing relevant results must be logged as an amendment and evaluated on untouched data.

---

# 9. Core gauntlet families

## Stateful / substrate gauntlets

```text
M01 structural identity
M02 execution identity
M03 skill mining
M04 harmful frequency
M05 exact replay
M06 effect safety
M07 failure-derived guards
M08 lifecycle hysteresis
M09 resonance without lock-in
M10 context compiler vs cosine-only
M11 retrieval ambiguity policy
M12 conductance / local overload
```

## Long-memory gauntlets

```text
LCTX01 one needle — sanity only
LCTX02 many exact items
LCTX03 distributed multi-hop
LCTX04 latest state after many updates
LCTX05 explicit supersession / contradictions
LCTX06 distant procedure recall
LCTX07 file/version evolution
LCTX08 exact provenance recovery
LCTX09 near-semantic distractors
LCTX10 raw-history vs compressed-memory parity
```

Additional gauntlets should be added by hypothesis family, but the protected lockbox must remain independent of the development process.

---

# 10. Research questions

Primary:

> **Can a ~1–2B neural executive plus a content-addressed, effect-aware, provenance-preserving, procedurally learning memory substrate reach a better operating point than the same substrate operated by a strong ~4B model on stateful, effectful, long-lived local agent work?**

Substrate:

> **Does the substrate improve both the ~1B and ~4B controls relative to their vanilla equivalents?**

Long memory:

> **Can the system accurately use exact information anywhere in at least a one-million-token history without requiring the whole history to occupy live neural attention?**

Neural expansion:

> **After the substrate is fixed, does depth expansion add repeatable value beyond stock MiniCPM5 that justifies its extra memory and latency?**

---

# 11. Change control

This contract is intentionally harder to change than the architecture specs.

A change requires:

```text
date
reason
which observed results motivated the change
which metrics / thresholds / gauntlets are affected
whether any previously viewed data becomes invalid for confirmation
new untouched evaluation source
```

The research agent may propose amendments. It may not silently apply them.

---

# 12. Compact thesis

> **Gen-2 is not a bet that a tiny model can magically become a frontier model. It is a test of whether exact memory, procedure, authority, provenance, and verification can be moved into a trusted substrate so that a small local model remains competitive on the stateful work that actually benefits from those properties.**

> **If S2 — the stronger ~4B model using the same substrate — is better enough to justify its operating cost, the substrate may still win while the small-executive thesis loses. The experimental design must be able to say that clearly.**

---

# 13. Key references

- MiniCPM5-1B: https://huggingface.co/openbmb/MiniCPM5-1B
- MiniCPM5 config: https://huggingface.co/openbmb/MiniCPM5-1B/blob/main/config.json
- Current replaceable ~4B baseline reference: https://huggingface.co/Qwen/Qwen3.5-4B
- VibeThinker-3B: https://huggingface.co/WeiboAI/VibeThinker-3B
- VibeThinker paper: https://arxiv.org/abs/2606.16140
- Karpathy autoresearch: https://github.com/karpathy/autoresearch
- Autoresearch programme: https://github.com/karpathy/autoresearch/blob/master/program.md
- MLX autoresearch adaptation: https://github.com/trevin-creator/autoresearch-mlx

**Source lineage:** distilled and tightened from `cognitive-core-gen2-revised-research-spec-v2.1.md`; this v2.2 split incorporates the subsequent review concerning factorial baselines, pre-registration, wall-clock/experiment budgets, and the narrower stateful-agent thesis.
