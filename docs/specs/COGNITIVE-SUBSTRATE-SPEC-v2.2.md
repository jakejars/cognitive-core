# Cognitive Core Gen-2 — Cognitive Substrate Specification v2.2
## Trusted Runtime, Effect-Aware IR, Provenance, Procedural Cortex, and Continual Governance

**Status:** Authoritative architecture reference  
**Date:** 2026-08-18  
**Scope:** Model-agnostic trusted substrate beneath the neural executive  
**Primary implementation lineage:** Modus source concepts reviewed in the Gen-2 programme  

> **Thesis:** The neural model proposes semantic intent. The substrate owns execution semantics, authority, exact state, provenance, validation, procedure lifecycle, and the parts of memory governance that are better implemented deterministically.

> **Document set:** This file is one of three authoritative Gen-2 v2.2 specifications.
> 1. `COGNITIVE-CORE-RESEARCH-CONTRACT-v2.2.md` — falsifiable thesis, baselines, gates, budgets, kill rules.
> 2. `COGNITIVE-SUBSTRATE-SPEC-v2.2.md` — trusted runtime, effect/provenance system, procedural cortex.
> 3. `COGNITIVE-MEMORY-AND-NEURAL-SPEC-v2.2.md` — MiniCPM, training, retrieval, and long-memory architecture.

# 1. Trust boundary and role in the complete system

The substrate is intentionally **not** the neural architecture.

Do not put lambda reduction, PageRank, Bayesian updates, procedural graphs, conductance, capability minting, or effect semantics inside the Transformer merely because the Transformer can approximate them.

The neural executive should learn questions such as:

```text
what is the task?
what information matters?
which skill/tool should I invoke?
do I have enough evidence?
what should I do next?
should I answer, search, ask, or escalate?
```

The trusted substrate owns:

```text
identity
exact event/state memory
provenance
effects and authority
idempotency / replay
skill execution
validation
confidence accounting
promotion / quarantine / retirement
context assembly
```

## 1.1 Minimal model intent

The small model should emit only the semantic content it can reasonably be expected to produce reliably, for example:

```yaml
operation: search
arguments:
  query: "..."
evidence_refs: []
```

The runtime then resolves the operation and attaches:

```text
operation_version
effect class
determinism / idempotency
permissions / capability requirements
validator
retry / rollback policy
provenance
cost / latency estimates
```

The model proposes intent. It does not mint authority or define trusted execution semantics.

## 1.2 True verification

A neural critique block can bias representations toward evidence sensitivity, but **verification of a completed answer/action is post-generation**:

```text
PASS 1 — candidate answer or action plan
            ↓
DETERMINISTIC CHECKS
schema / provenance / citations / effects / tool state
            ↓
PASS 2 — only when required
candidate + evidence + checker results
            ↓
ACCEPT / REVISE / SEARCH / ASK / ESCALATE
```

Only trusted deterministic components may construct privileged types such as `CitationCheckedAnswer` or one-shot authority tokens.

---

# 2. Modus is not the neural architecture

A crucial design decision:

> **Do not put lambda reduction, PageRank, Bayesian updates, procedural graphs, or conductance inside the Transformer.**

Keep those deterministic and inspectable.

The neural core should learn:

```text
what is the task?
what information matters?
which skill/tool should I invoke?
do I have enough evidence?
what should I do next?
is the result trustworthy?
```

The Modus substrate should implement:

```text
identity
memory
provenance
effects
caching
skill execution
confidence accounting
promotion / retirement
context assembly
```

This preserves the advantages of pretraining while creating formal execution data as a side effect of ordinary agent use.

---

# 3. Effect-aware workflow IR: model intent, runtime semantics

The practical IR remains closer to typed SSA/dataflow than raw lambda syntax, but the trusted runtime—not the language model—owns most semantic metadata.

## 3.1 Minimal model-emitted intent

The model should normally emit only the information it must decide:

```yaml
operation: search
arguments:
  query: "MiniCPM long-context configuration"
requested_result: evidence
candidate_dependencies:
  - current_question
```

or:

```yaml
operation: invoke_skill
skill: verify_claims
arguments:
  draft_ref: answer_17
  evidence_set_ref: evidence_31
```

Grammar-constrained decoding should keep this interface compact.

A ~1B executive should **not** be expected to reliably author the entire execution contract for each node.

## 3.2 Runtime-enriched node

The substrate resolves the requested operation against a trusted registry and constructs the full executable node:

```yaml
operation_id:
operation_version:

input_schema:
output_schema:
canonical_arguments:

content_hash:
execution_hash:

effect_class:
deterministic:
idempotency:

permissions:
required_capabilities:
confidentiality:

estimated_cost:
estimated_latency:

provenance:
validator:

retry_policy:
rollback_policy:
```

The model cannot override registry-defined safety semantics by emitting different metadata.

## 3.3 Suggested node vocabulary

```text
PureCall
ModelCall
ToolCall
Retrieve
Search
Compute
Map
Join
Branch
Retry
Verify
Materialize
AskUser
Escalate
HumanApproval
CommitEffect
```

## 3.4 Trust boundary

The rule is:

> **The model proposes semantic intent. The runtime attaches authority, effects, versions, validation, and execution identity.**

This makes the capability-type design meaningful and prevents schema verbosity from becoming a small-model reliability bottleneck.

---

# 4. Effect system

Recommended initial effect classes:

```text
PURE
READ_LOCAL
READ_REMOTE
SEARCH
MODEL_STOCHASTIC
COMPUTE_SANDBOXED
MUTATE_REVERSIBLE
MUTATE_EXTERNAL
IRREVERSIBLE
HUMAN_APPROVAL
```

Pure deterministic regions may be:

- reordered;
- memoised;
- deduplicated;
- parallelised.

Effectful regions require:

- ordering;
- capabilities;
- transaction semantics;
- explicit idempotency;
- auditability.

This is especially important for:

```text
send_email
publish
charge_card
delete
modify_database
```

A structural match is **not** sufficient reason to deduplicate an effect.

---

# 5. Capability types

Types are useful when trusted runtime components mint values the model cannot forge.

Example:

```text
verify_citations:
    DraftAnswer × EvidenceSet
    → Result[CitationCheckedAnswer, VerificationError]
```

Only the deterministic verifier may construct `CitationCheckedAnswer`.

Likewise:

```text
charge:
    PaymentIntent
    × OneShot[PaymentAuthority]
    → PaymentReceipt
```

The model can request the operation.

It cannot mint `PaymentAuthority`.

This is stronger than prompt-level instructions.

---

# 6. Dual identity: structural vs executable

One of the strongest Modus ideas is canonicalisation.

The Lexicon code maps names into positional identities such as:

```text
Param(index)
Local(index)
Free(symbol)
Lit(kind)
Form(tag, children)
```

and deliberately removes cosmetic alpha-renaming.

In the uploaded Modus source:

```text
crates/lexicon/src/ir.rs
crates/lexicon/src/normalise.rs
```

literal values are currently abstracted to literal **kinds** for structural stability.

That is useful for skill discovery but dangerous for execution caching.

Therefore Gen-2 should maintain two hashes.

## 6.1 Structural identity

Used for:

```text
near-duplicate detection
skill mining
abstraction
clustering
anti-unification
retrieval
```

May ignore:

- bound variable names;
- formatting;
- comments;
- selected literal values.

## 6.2 Execution identity

Used for:

```text
memoization
replay
provenance
idempotency
effect tracking
```

Must include every semantically relevant value:

```text
hash(
  operation_version,
  canonical_arguments,
  dependency_hashes,
  relevant_environment_version,
  model/tool version,
  decoding settings
)
```

Never use the structural identity as the execution cache key.

---

# 7. Hash-consed memory DAG

Long-lived memory should not be represented exclusively as repeated prose.

Use:

```text
canonical binding
+
content-addressed Merkle DAG / hash-consing
+
versioned operation semantics
+
optional normalization / e-graph equality
```

This allows repeated entities, tool results, files, decisions, skills, and evidence to point to shared nodes.

Example:

```text
                      Project decision
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
            Claim       Evidence      Skill
              │            │            │
              └──────┬─────┘            │
                     ▼                  │
                source chunk           │
                     │                  │
                     └────────┬─────────┘
                              ▼
                         execution DAG
```

A one-million-token history can contain enormous textual repetition.

The DAG should not.

---

# 8. Procedural Cortex

The cognitive system should learn reusable procedures outside the model weights.

Initial process:

```text
execution traces
      ↓
canonical trace/DAG representation
      ↓
resonance / structural clustering
      ↓
candidate procedure
      ↓
derive typed interface
      ↓
attach effects / permissions / failures
      ↓
shadow replay
      ↓
counterfactual held-out gauntlet
      ↓
promote / quarantine / reject
      ↓
versioned skill graph
```

The existing uploaded Modus implementation already contains important pieces in:

```text
crates/skills/src/extract.rs
crates/skills/src/interface.rs
crates/skills/src/verify.rs
crates/skills/src/promote.rs
crates/skills/src/graph.rs
crates/praxis/src/resonance.rs
```

The next-generation implementation should extend contiguous-sequence mining into:

- frequent subgraph mining;
- anti-unification;
- Stitch-like abstraction;
- e-graph equivalence classes;
- causal dependency recovery.

---

# 9. Frequency is not usefulness: promotion by gates and Pareto dominance

A recurring subgraph may represent:

- a genuinely useful procedure;
- repeated exploration;
- an accidental loop;
- repeated recovery from the same model weakness;
- benchmark artefacts;
- harmful behaviour.

Therefore frequency is only a **candidate-generation signal**.

Do not promote a skill with a large hand-tuned scalar objective unless experiments show that a scalarisation is necessary.

## 9.1 Promotion pipeline

```text
candidate procedure
      ↓
HARD VALIDITY GATES
schema / replay / preconditions
      ↓
EFFECT-SENSITIVE SAFETY GATES
no forbidden duplicate / irreversible action
      ↓
HELD-OUT CAPABILITY GATE
success improves or is non-inferior
      ↓
RELIABILITY GATE
failure / calibration does not regress materially
      ↓
PARETO COMPARISON
latency / cost / memory / tool calls / complexity
      ↓
PARSIMONY WITHIN NEAR-TIE BAND
      ↓
promote / quarantine / reject
```

## 9.2 Why this is preferable

This removes many degrees of freedom from the autoresearch loop and reduces the risk of discovering a lucky coefficient vector that overfits a small gauntlet.

For research analysis, keep the original component deltas separately:

```text
Δ success
Δ reliability
Δ latency
Δ cost
Δ retrieval overhead
Δ library complexity
Δ safety failures
```

but do not require them to be collapsed into a single permanent utility scalar.

## 9.3 When scalarisation is acceptable

A scalar objective may be used for a constrained search only when:

- coefficients are fixed before protected evaluation;
- the objective reflects a real deployment trade-off;
- a final untouched test set exists;
- winners are confirmed on multiple seeds/task samples;
- Pareto information is still retained.

The research question remains counterfactual:

```text
system without candidate skill
vs
system with candidate skill
```

Only promote if the **whole system** improves.

---

# 10. Skill contract

Every promoted skill should expose:

```yaml
name:

typed_inputs:
typed_outputs:

preconditions:
postconditions:

effects:
permissions:

failure_modes:
retry_policy:
rollback_policy:

validator:

provenance:
source_trace_hashes:

support_range:
confidence:

version:
structural_hash:
execution_semantics_version:
```

A skill remains provisional until held-out validation shows real benefit.

---

# 11. Learn from failure traces

Failures are first-class training and procedure-refinement data.

They reveal:

- missing guards;
- unsafe reorderings;
- insufficient preconditions;
- unreliable tools;
- incorrect permissions;
- necessary retries;
- stale dependencies;
- when a macro should fall back to model reasoning.

A good learned skill is therefore not merely:

```text
compressed happy path
```

but:

```text
procedure
+
guards
+
branches
+
retry
+
verification
+
escalation conditions
```

## 11.1 Relationship to Reflexion-style learning

Reflexion is useful prior art for turning failure feedback into future behavioural improvement, but Gen-2 should not stop at textual self-reflection.

Where possible, convert validated lessons into inspectable substrate state:

```text
failure observation
→ attributed cause
→ typed precondition / guard / validator / fallback
→ replay
→ held-out counterfactual test
```

Reference:

- Reflexion: https://arxiv.org/abs/2303.11366

Textual lessons may remain as weak evidence, but runtime-enforceable guards are preferable when the failure can be formalised.

---

# 12. Resonance, stigmergic memory, and anti-lock-in exploration

Modus contains a useful continual-memory primitive.

A trace/skill has weight \(w\).

Reuse reinforces:

\[
w \leftarrow w + \Delta
\]

Logical ticks decay multiplicatively:

\[
w \leftarrow w(1-\lambda)
\]

The source documents the approximate equilibrium:

\[
w^* = \frac{\Delta r}{\lambda}
\]

where \(r\) is reuse rate.

Relevant source:

```text
crates/praxis/src/stigmergy.rs
crates/praxis/src/resonance.rs
```

This gives an interpretable use-dependent prior for:

- skills;
- memories;
- evidence;
- tools;
- recurring concepts.

Frequently useful objects stay easier to retrieve; unused objects fade without immediate deletion.

## 12.1 Positive-feedback risk

The same mechanism can self-lock:

```text
early retrieval
→ more use
→ more resonance
→ easier future retrieval
→ less exposure for alternatives
```

Therefore resonance must **never be the sole retrieval or retention signal**.

## 12.2 Exploration without unsafe random actions

Do not inject random live tool use merely to explore.

Instead use:

```text
production retrieval
+
shadow candidate retrieval
+
uncertainty-directed exploration
+
temporal held-out shards
+
periodic counterfactual replay
```

For each production query, the system may record one or more *shadow* candidates that were not placed into active context. Offline evaluation can ask whether those candidates would have improved the result.

This creates exploration pressure without allowing exploratory candidates to directly trigger side effects.

## 12.3 Fresh-task evaluation

Promotion and resonance policies must also be evaluated on tasks and memory shards that were not used to generate the policy. A memory system that only becomes better at retrieving its own earlier preferences has failed.

---

# 13. Separate frequency from quality

A frequently used thing is not necessarily good.

Gen-2 should maintain separate signals.

## 13.1 Resonance / reuse

Answers:

> How often is this useful enough to be invoked?

## 13.2 Kalman quality estimate

The uploaded Modus governance layer contains a scalar Kalman estimator:

```text
crates/governance/src/kalman.rs
```

Conceptually:

\[
K = \frac{P^-}{P^-+R}
\]

\[
x = x^- + K(z-x^-)
\]

\[
P = (1-K)P^-
\]

This tracks latent quality and uncertainty over noisy observations.

## 13.3 Bayesian claim/evidence confidence

The uploaded Modus source also contains Bayesian confidence/re-estimation components:

```text
crates/governance/src/bayes_reest.rs
```

Use distinct estimates for:

```text
P(claim correct | evidence)
source reliability
freshness / staleness risk
skill safety
verification confidence
```

Do not collapse all of these into one language-model "confidence" scalar.

---

# 14. Neural confidence + deterministic confidence

Needle-style neural heads and Modus-style deterministic confidence should complement each other.

The Cognitive Core can produce:

```text
model_self_confidence
evidence_sufficiency
needs_search
needs_escalation
```

The substrate supplies:

```text
source_reliability
claim_evidence_posterior
retrieval_entropy
skill_quality
skill_support
freshness
```

Final action policy consumes both.

Example:

```text
model confidence:          0.86
evidence posterior:        0.41
retrieval entropy:         high
source freshness:          poor

=> SEARCH, not ANSWER
```

This is more reliable than asking the model to introspect everything internally.

---

# 15. Hysteresis for continual learning

The uploaded Modus governance layer deliberately uses asymmetric lifecycle thresholds.

Relevant source:

```text
crates/governance/src/hysteresis.rs
crates/governance/src/lifecycle.rs
```

The principle should remain:

```text
candidate creation       cheap
promotion                difficult

quarantine               easy + reversible
permanent retirement     difficult
```

This prevents oscillation and overreaction.

For high-effect skills:

```text
promotion threshold higher
quarantine threshold lower
```

For read-only skills:

```text
promotion may be statistical
```

For irreversible skills:

```text
promotion may require perfect replay + explicit human policy
```

---

# 16. Parsimony as a research law

The uploaded Modus parsimony implementation follows an important rule:

1. identify the best-performing region;
2. define an epsilon near-tie band;
3. within the band, prefer the simplest candidate.

Relevant source:

```text
crates/governance/src/parsimony.rs
```

So autoresearch should not reward:

```text
smaller but meaningfully worse
```

nor:

```text
vastly more complex for statistically negligible gain
```

Procedure:

```text
capability first
then, among near-equivalent survivors:
    fewer parameters
    lower latency
    less memory
    fewer tool calls
    simpler skill graph
```

---

# 17. PageRank / centrality is a prior, not the retriever

Modus contains PageRank-style graph centrality machinery:

```text
crates/governance/src/centrality.rs
```

Use centrality as one global memory-importance prior, never as a replacement for task-conditioned retrieval.

Memory retrieval should not be:

```text
embedding cosine only
```

nor:

```text
PageRank only
```

Instead combine a small number of independently meaningful signals:

```text
semantic task fit
state/provenance fit
recency or supersession relevance
quality/confidence
centrality/resonance as weak priors
```

Then use diversity selection where multiple pieces of evidence are required.

## 17.1 HippoRAG calibration

HippoRAG is important prior art because it combines a graph memory with Personalized PageRank for retrieval.

Reference:

- https://arxiv.org/abs/2405.14831

Gen-2's distinction is that its graph also carries executable procedure, effect state, provenance, identities, and lifecycle metadata. Nevertheless, HippoRAG should be treated as a serious retrieval baseline rather than rediscovering graph-centrality retrieval in isolation.

---

# 18. Conductance and homeostatic memory budgets

The uploaded Modus code contains a conductance/homeostasis system:

```text
crates/governance/src/conductance.rs
```

Its valuable conceptual property is **local overload control**.

Rather than one giant global memory pool:

```text
coding
personal
research
project A
project B
tools
skills
```

each cluster maintains a local activation/retrieval budget.

```text
                    retrieval demand
                           │
          ┌────────────────┼───────────────┐
          ▼                ▼               ▼
        coding          personal        research
       cluster           cluster         cluster
          │                │               │
     conductance      conductance     conductance
          │                │               │
          └────────────────┼───────────────┘
                           ▼
                    context budget
```

If one cluster floods the system, its resistance can increase without suppressing unrelated memories.

This looks promising for million-token memory.

---

# 19. Retrieval entropy

Modus contains a deterministic entropy component:

```text
crates/compiler/src/entropy.rs
```

Use Shannon entropy:

\[
H(X)=-\sum_i p_i\log_2p_i
\]

over competing memory candidates.

Interpretation:

```text
low entropy
→ clear retrieval winner
→ proceed

high entropy
→ multiple plausible contexts
→ retrieve more / ask / search / verify
```

This gives the neural epistemic controller an external ambiguity signal.

---

# 20. Context packing and MMR

Modus already contains a context compiler with MMR-style diversity selection:

```text
crates/compiler/src/pack.rs
crates/compiler/src/scoring.rs
crates/compiler/src/prefilter.rs
crates/compiler/src/activation.rs
```

The intended logic:

```text
activate task
    ↓
prefilter
    ↓
privacy / contradiction / taint gates
    ↓
score relevance
    ↓
diversity selection
    ↓
entropy check
    ↓
context packet
```

This is directly reusable as a conceptual precursor to demand-paged long context.

### Important implementation warning

Static inspection of the uploaded `crates/compiler/src/pack.rs` shows a likely bug in the current bag-of-words cosine implementation.

`norm_b` is accumulated only for tokens **not** present in `a`.

For identical non-empty vectors, this can leave `norm_b == 0`, producing similarity 0 despite the function comment defining identical vectors as 1000.

Do **not** lift this implementation unchanged.

Add explicit tests:

```text
cos(x, x) == 1
cos(x, disjoint) == 0
symmetry
boundedness
known partial-overlap cases
```

---

# 21. Procedural lifecycle and offline evaluation

A procedure must not be promoted because it is frequent. Promotion uses hard gates, held-out counterfactual evaluation, Pareto comparison, and parsimony.

Recommended lifecycle:

```text
candidate creation
→ shadow mode
→ replay
→ held-out counterfactual A/B
→ effect-sensitive safety checks
→ promotion threshold
→ live observation
→ Kalman/Bayes quality tracking
→ quarantine on regression
→ retirement only with strong evidence
```

For a candidate skill/policy, use expensive offline Monte Carlo shadow evaluation where appropriate. Sample tool/network failures, changed schemas, ambiguous memory, cost variation, adversarial observations, and user behaviour; measure success, latency, unsafe outcomes, and fallback rate before promotion.

Use expensive offline oracles to supervise cheap runtime heuristics for:

- context packing;
- memory retention;
- tool choice;
- skill selection;
- chunk selection.

This preserves the Modus philosophy that costly search/optimisation belongs offline when possible rather than on the user-facing hot path.

---

# 22. Context compiler policy

The substrate's context compiler starts with hard gates and a deliberately small interpretable ranking baseline.

## 22.1 Hard gates

Before ranking, reject candidates that violate:

```text
privacy / confidentiality
permission / authority
known contradiction/supersession policy
taint / untrusted-source policy
incompatible task/state scope
invalid provenance
```

## 22.2 Minimal ranking baseline

Prefer a small number of independently interpretable factors before large weighted sums:

```text
semantic relevance
task/state fit
freshness / supersession status
quality / provenance confidence
```

Then apply diversity/MMR only where redundant retrieval is a measured problem.

Compare:

```text
semantic-only
simple deterministic hybrid
learned reranker
neural-only retrieval
hybrid neural + deterministic
```

Use the offline oracle as supervision where available. Do not repeatedly tune a large coefficient vector against one small gauntlet.

## 22.3 Retrieval ambiguity

If retrieval entropy is high:

```text
retrieve more
OR switch retrieval mode
OR ask user
OR search externally
OR escalate
```

If entropy is low but evidence confidence is poor, search/verify rather than answer merely because one candidate won the ranking.

---

# 23. Memory write policy and anti-self-poisoning

Do not write every model thought into semantic memory.

Separate:

```text
RAW TRACE
append-only observation/log

EVENT
structured, append-only

CLAIM
requires evidence/confidence state

DECISION
requires provenance

SKILL
requires validation

LONG-TERM MEMORY
requires retention policy
```

A model generation is not automatically a fact. Promotion into claims, decisions, or skills needs external evidence, deterministic validation, user confirmation, or observed outcome signal as appropriate.

Exploration candidates should be evaluated in shadow rather than being allowed to cause random live side effects.

---

# 24. Substrate-specific training interfaces

The substrate can generate supervision that teaches the model how to operate it without asking the model to implement the substrate internally.

```text
SKILL SELECTION
task + primitive tools + validated skills
→ best capability

EFFECT REASONING
workflow
→ which branches may safely parallelise / retry / cache?

CACHE REASONING
node + environment
→ cacheable / not cacheable

EPISTEMIC INTERPRETATION
confidence + entropy + freshness + evidence
→ answer / search / ask / escalate

PROCEDURAL FALLBACK
skill failed precondition
→ expand back to primitive reasoning

PROVENANCE
claim
→ retrieve supporting evidence closure
```

---

# 25. Implementation sequence

## Phase B — minimal substrate bridge

1. event ledger adapter;
2. canonical structural representation;
3. dual structural/execution identity;
4. trusted operation registry;
5. effect classes;
6. capability contracts;
7. provenance;
8. minimal skill registry;
9. simple context compiler;
10. runtime enrichment of model-emitted intents;
11. post-generation deterministic verification path.

**Gate:** substrate overhead must fit the frozen research-contract budget and improve at least one pre-registered safety/reliability/state axis without violating task-retention constraints.

## Phase D — procedural learning

1. capture execution DAGs;
2. contiguous skill miner;
3. DAG/subgraph miner;
4. interface inference;
5. runtime attachment of effects/permissions;
6. replay validator;
7. failure-derived guards;
8. held-out counterfactual promotion;
9. resonance + quality separation;
10. hysteresis;
11. shadow exploration / counterfactual retrieval replay.

**Gate:** promoted skills must improve fresh held-out tasks, not merely compress frequent traces.

## Model-agnostic validation requirement

The substrate is not considered validated solely because it helps MiniCPM5. The research contract requires testing it under at least:

```text
S1 = MiniCPM5-1B + validated substrate
S2 = strong ~4B model + same validated substrate
```

This separates the value of the substrate from the small-executive hypothesis.

---

# 26. Substrate gauntlets

```text
M01 — structural identity
Equivalent renamed/reformatted procedures collapse correctly.

M02 — execution identity
Different semantic arguments never collide merely because structure matches.

M03 — skill mining
Recover planted reusable procedures.

M04 — harmful frequency
Reject frequent loops that are useless or harmful.

M05 — replay
Promoted pure skills replay exactly.

M06 — effect safety
Prevent duplicate irreversible actions and unauthorised retries.

M07 — failure-aware skill
Negative traces produce required guards/fallbacks.

M08 — hysteresis
Noisy quality does not create promote/demote oscillation.

M09 — resonance
Useful recurrence remains retrievable without locking out better alternatives.

M10 — context compiler
Hybrid retrieval beats cosine-only on protected stateful tasks.

M11 — entropy
High ambiguity triggers retrieve/search/ask behaviour appropriately.

M12 — conductance
One noisy cluster can be throttled without suppressing unrelated memory.
```

---

# 27. Implementation invariants

The trusted substrate should preserve these invariants:

1. **Structural identity is never used as an execution cache key.**
2. **The model cannot mint authority tokens.**
3. **Irreversible effects are never deduplicated/replayed solely from structural similarity.**
4. **Every promoted claim/decision/skill resolves to provenance.**
5. **Every effectful operation has explicit idempotency/retry semantics.**
6. **Every promoted skill has a validator and failure/fallback model.**
7. **Frequency and quality remain separate state variables.**
8. **Live memory retrieval may exploit resonance; exploration occurs in shadow.**
9. **Context ranking is allowed to simplify itself if a feature adds no held-out value.**
10. **The substrate may be rejected for latency/memory overhead even if its algorithms are individually interesting.**

---

# 28. References and Modus implementation map

## User-provided Modus source archive

Especially relevant files:

```text
crates/lexicon/src/ir.rs
crates/lexicon/src/normalise.rs

crates/praxis/src/resonance.rs
crates/praxis/src/stigmergy.rs

crates/skills/src/extract.rs
crates/skills/src/interface.rs
crates/skills/src/verify.rs
crates/skills/src/promote.rs
crates/skills/src/graph.rs

crates/compiler/src/activation.rs
crates/compiler/src/entropy.rs
crates/compiler/src/gates.rs
crates/compiler/src/pack.rs
crates/compiler/src/prefilter.rs
crates/compiler/src/scoring.rs

crates/governance/src/kalman.rs
crates/governance/src/bayes_reest.rs
crates/governance/src/centrality.rs
crates/governance/src/conductance.rs
crates/governance/src/hysteresis.rs
crates/governance/src/lifecycle.rs
crates/governance/src/parsimony.rs
```

**Implementation warning:** the reviewed bag-of-words cosine implementation in `crates/compiler/src/pack.rs` appeared to accumulate `norm_b` incorrectly for overlapping tokens. Do not copy it unchanged. Keep explicit tests for identical vectors, disjoint vectors, symmetry, boundedness, and known partial-overlap cases.

## Prior art that calibrates claims

- MemGPT: https://arxiv.org/abs/2310.08560
- HippoRAG: https://arxiv.org/abs/2405.14831
- RETRO: https://arxiv.org/abs/2112.04426
- Reflexion: https://arxiv.org/abs/2303.11366

Gen-2's substrate claim is not that graph memory, PageRank, reflection, or retrieval are individually novel. The research contribution is the **integrated effect-aware, provenance-preserving, continually validated procedural substrate** around a small local executive.

---

# 29. Compact thesis

> **The model should choose and explain; the substrate should remember exact state, enforce authority, execute safely, validate outcomes, and turn repeated successful workflows into procedures only after evidence says they help.**
