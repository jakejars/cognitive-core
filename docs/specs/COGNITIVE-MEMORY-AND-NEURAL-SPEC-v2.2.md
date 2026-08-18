# Cognitive Core Gen-2 — Memory and Neural Specification v2.2
## MiniCPM Executive, Conditional Depth Expansion, Retrieval Heads, and Million-Token Addressable Memory

**Status:** Authoritative architecture/training reference  
**Date:** 2026-08-18  
**Scope:** Neural executive, training recipe, context compiler interface, exact long-memory hierarchy, and optional long-context research  
**Default strategy:** stock MiniCPM5-1B + native 131K + external exact memory before neural surgery  

> **Thesis:** One million tokens are primarily an **exact historical address space**, not one million simultaneously active Transformer positions. Neural expansion and native >131K context are conditional experiments, not assumptions.

> **Document set:** This file is one of three authoritative Gen-2 v2.2 specifications.
> 1. `COGNITIVE-CORE-RESEARCH-CONTRACT-v2.2.md` — falsifiable thesis, baselines, gates, budgets, kill rules.
> 2. `COGNITIVE-SUBSTRATE-SPEC-v2.2.md` — trusted runtime, effect/provenance system, procedural cortex.
> 3. `COGNITIVE-MEMORY-AND-NEURAL-SPEC-v2.2.md` — MiniCPM, training, retrieval, and long-memory architecture.

# 1. Default architecture

The default system intentionally begins simpler than the original sandwich proposal:

```text
STOCK MiniCPM5-1B
        │
        ├─ grammar-constrained semantic intent
        ├─ optional retrieval / epistemic heads after ablation
        │
        ▼
TRUSTED SUBSTRATE
        │
        ├─ exact event/history tape
        ├─ structured state/provenance
        ├─ procedural cortex
        └─ context compiler
        │
        ▼
ACTIVE FRONTIER
~8K–64K typical
up to native 131K when justified
        │
        ▼
PASS 1 GENERATION
        │
        ▼
DETERMINISTIC VERIFICATION
        │
        └─ optional neural pass-2 critique
```

Only after measured bottlenecks appear should the programme add:

```text
identity-preserving depth expansion
specialised scaffold-trained blocks
native >131K positional extension
sparse-attention surgery
```

---

# 2. Neural core: MiniCPM5 baseline, but expansion is conditional

The recommended base remains MiniCPM5-1B because it is a standard `LlamaForCausalLM` checkpoint with a conventional hidden-state interface and strong small-model agentic intent.

Verified base properties:

```text
parameters:                1,080,632,832 total
non-embedding parameters:   679,552,512
layers:                     24
hidden size:                1536
attention:                  16 Q heads / 2 KV heads
head dimension:             128
native context:             131,072 tokens
architecture:               LlamaForCausalLM
```

**Attention-dimension note:** MiniCPM5 explicitly sets `head_dim: 128` independently of the `hidden_size: 1536` residual stream. Therefore `16 × 128 = 2048` attention projection width does not need to equal the residual width. KV-cache calculations in this specification use the explicit `2 KV heads × 128 head_dim`, not `hidden_size / num_attention_heads`.

References:

- https://huggingface.co/openbmb/MiniCPM5-1B
- https://huggingface.co/openbmb/MiniCPM5-1B/blob/main/config.json
- https://github.com/OpenBMB/MiniCPM

## 2.1 Stock model is a first-class baseline

Do **not** assume expansion helps.

Run all early tasks against:

```text
M0 stock MiniCPM5-1B
M1 stock MiniCPM5-1B + substrate
M2 expanded MiniCPM5 candidate + same substrate
```

If M2 cannot show repeatable improvement beyond M1 after accounting for extra latency and resident memory, abandon the sandwich.

## 2.2 Experimental expanded architecture

If expansion survives the gate, the current candidate remains:

```text
Embedding
   ↓
Original MiniCPM layers 0–7
   ↓
Reasoning-pressure block — 8 layers
   ↓
Original MiniCPM layers 8–15
   ↓
Control / action-selection block — 4 layers
   ↓
Critique / evidence-integrity block — 4 layers
   ↓
Original MiniCPM layers 16–23
   ↓
LM head
```

Approximate total size remains ~1.5B parameters.

The labels describe **training pressure and intended functional bias**, not hard symbolic organs.

## 2.3 Specialisation must be demonstrated

Add explicit tests:

```text
swap reasoning ↔ critique blocks
remove one inserted block
probe hidden-state separability
measure effect on reasoning-only tasks
measure effect on action-selection tasks
measure effect on evidence/critique tasks
```

A named cartridge that can be swapped without predicted degradation is not meaningfully specialised and should be renamed or removed.

## 2.4 Base behaviour is the comparison point

MiniCPM5 already advertises strong tool-use and reasoning behaviour for its size class and already has native long context. New epistemic, retrieval, and abstention mechanisms must therefore report **delta against the actual base checkpoint**, not absolute scores that the base may already achieve.

---

# 3. Depth expansion and scaffolded cartridge training

Depth expansion now has a hierarchy of controls.

## 3.1 Control A — identity-preserving block expansion

Use LLaMA-Pro-style identity-preserving insertion as the primary safe baseline.

The key idea is to initialise newly inserted residual blocks so that their contribution is initially zero, preserving the pretrained network's input-output function at insertion time.

For a standard attention/MLP residual block, candidate implementation:

```text
new attention block:
    ordinary copied/compatible internal weights
    output projection initialised to zero

new FFN block:
    ordinary copied/compatible internal weights
    final/down projection initialised to zero
```

This should be tested against exact function-preservation checks before training.

Reference:

- LLaMA-Pro: https://arxiv.org/abs/2401.02415

## 3.2 Control B — conventional depth up-scaling

SOLAR is the relevant baseline for simple depth expansion / layer duplication strategies.

Reference:

- SOLAR 10.7B: https://arxiv.org/abs/2312.15166

Use this to calibrate whether the purported value comes from specialised scaffold training or merely from adding depth.

## 3.3 Experimental branch — Mixture of Training

Mixture of Training (MoT) proposes:

```text
frozen lower aligner scaffold
        ↓
trainable contiguous layer slice
        ↓
frozen upper aligner scaffold
        ↓
frozen LM head
        ↓
loss
```

and then recomposes independently trained slices with an optional short end-to-end adaptation pass.

Reference:

- https://arxiv.org/abs/2608.13277

Because the work is extremely recent, Gen-2 must first run a **small replication** before committing the main 1.5B experiment.

Suggested replication gate:

```text
100M–300M-class scaffold
2–4 independently trained slices
small controlled corpus
cold recomposition
short adaptation
compare against jointly trained depth-matched control
```

Proceed to MiniCPM surgery only if recomposition reproduces the claimed qualitative effect.

## 3.4 Initialisation matrix

Test:

1. identity-preserving / zero-output insertion;
2. copied neighbouring-layer initialisation;
3. repeated-block initialisation;
4. random initialisation;
5. conventional SOLAR-style duplicated depth;
6. MoT-style independent scaffold training.

For MoT variants also test:

- no interface loss;
- RMS-normalised boundary loss;
- cosine boundary loss.

## 3.5 Mandatory measurements

Every depth experiment reports:

```text
pre-training function drift at step 0
training stability
held-out task gain
generic capability retention
TTFT / decode impact
resident memory impact
second-seed replication
```

The default should be the simplest method that preserves function and wins on held-out tasks.

---

# 4. Neural confidence and retrieval interface

The neural model may expose learned signals such as:

```text
model_self_confidence
evidence_sufficiency
needs_search
needs_escalation
capability/memory retrieval query
```

The substrate supplies external signals such as:

```text
source reliability
claim/evidence posterior
retrieval entropy
skill quality/support
freshness / supersession state
provenance validity
```

Final policy consumes both. A high model confidence with poor evidence or stale state should lead to search/verification rather than an answer.

The retrieval head is optional and must beat simple deterministic retrieval. Candidate flow:

```text
hidden-state probe
      ↓
contrastive query projection
      ↓
ANN retrieval
      ↓
Top-N candidates
      ↓
trusted deterministic gates/reranker
      ↓
context compiler
```

Test separate versus shared embedding spaces for tools, skills, chunks, claims, evidence, and documents.

---

# 5. Million-token memory: define the target correctly

The target is **not**:

```text
max_position_embeddings = 1_048_576
```

The primary target is:

> **The system can accurately use information located anywhere within at least a one-million-token exact history while keeping neural working context, memory, and compute practical on the target Mac.**

MiniCPM5 already provides a native 131,072-token neural context window.

Therefore separate four capacities:

```text
NEURAL POSITIONAL WINDOW
native 131,072 by default

COLD EXACT HISTORY / ADDRESS SPACE
≥ 1,048,576 tokens or equivalent exact event history

RESIDENT STRUCTURED / INDEXED MEMORY
large but bounded

ACTIVE COGNITIVE FRONTIER
normally ~8K–64K
may expand toward native 131K when the task justifies it
```

## 5.1 Historical address is metadata

If an item originally occurred at token 873,221, preserve that fact as metadata:

```yaml
historical_token_start: 872960
historical_token_end: 873472
logical_time: 18421
source_event: evt_...
supersedes: ...
provenance: ...
```

When retrieved, the content may be serialised at ordinary local positions inside the active frontier.

This means **one-million-token historical addressability does not automatically require one-million-position RoPE**.

## 5.2 1M is a research target, not a sacred number

The gauntlet should measure capability as history length scales:

```text
131K
200K
256K
512K
1M
```

If performance saturates and real workloads do not benefit beyond a lower history size, the product requirement should follow evidence rather than the slogan.

---

# 6. Positional extension is optional, not Phase-E step one

LongRoPE demonstrates that pretrained models can be extended to very large positional ranges through non-uniform interpolation and long-context adaptation.

Reference:

- LongRoPE: https://arxiv.org/abs/2402.13753

This establishes that a 1M positional address space is technically plausible.

It does **not** establish that Gen-2 needs one.

## 6.1 Default policy

Start with native MiniCPM5 positions:

```text
0 ... 131,071
```

Retrieve historical information into that working space with explicit historical metadata.

Only train longer positional support if a protected gauntlet demonstrates a class of tasks where:

```text
external retrieval/materialisation fails
AND
longer simultaneous token-level attention plausibly fixes the failure
AND
the latency/memory cost is acceptable
```

## 6.2 Positional-extension branch

If that gate is met, test progressively:

```text
P0 native 131K
P1 256K
P2 512K
P3 1M
```

Every step must compare against the cheaper native-window + external-memory control.

---

# 7. Dense 1M attention is explicitly out of scope

At one million tokens, ordinary dense attention is computationally prohibitive for the target local system even if storage can be engineered.

The desired architecture therefore uses:

```text
native local/dense attention over hot context
+
external exact history
+
structured memory
+
sparse retrieval/materialisation
+
optional compressed or cached historical representations
```

The research target is **effective use of distant state**, not bragging rights for a dense advertised context window.

---

# 8. Native Sparse Attention: stretch research branch, not retrofit assumption

DeepSeek's **Native Sparse Attention (NSA)** combines:

- coarse-grained compressed global context;
- fine-grained selected tokens;
- local sliding-window context.

Reference:

- https://arxiv.org/abs/2502.11089

The paper presents NSA as a **natively trainable sparse attention mechanism** and evaluates models trained with it.

Therefore Gen-2 must not describe NSA as if it were an ordinary layer pattern that can simply replace selected attention layers in a pretrained dense MiniCPM checkpoint.

## 8.1 Research status

```text
status: stretch / architecture-surgery branch
prerequisite: external-memory baseline exhausted or clearly insufficient
cost: potentially substantial retraining + kernel/runtime work
```

If pursued, test small-scale architectural prototypes first.

## 8.2 Alternative sparse-adaptation prior art

InfLLM-V2 is also relevant because it explicitly studies dense/sparse switchable attention for short-to-long adaptation and highlights the adaptation difficulty of natively sparse methods.

Reference:

- https://arxiv.org/abs/2509.24663

This should be reviewed before committing to an NSA-derived implementation.

---

# 9. External exact memory is the first long-context baseline

InfLLM stores distant context in external memory units and retrieves token-relevant units for attention.

Its paper reports effective operation at sequence lengths up to 1,024K without requiring long-context fine-tuning of the base model.

References:

- https://arxiv.org/abs/2402.04617
- https://github.com/thunlp/InfLLM

This is now the **first long-context research baseline**, not a later add-on.

## 9.1 LC0 definition

```text
LC0
MiniCPM5 native 131K positional window
+
external raw-history store
+
chunk index
+
InfLLM-style token/chunk memory retrieval baseline
```

The exact implementation need not copy InfLLM internally; the baseline question is whether a training-free external-memory strategy already solves most of the one-million-token requirement.

## 9.2 RETRO lineage

RETRO is also relevant prior art for external retrieval augmenting a pretrained Transformer rather than forcing all useful information into model weights.

Reference:

- https://arxiv.org/abs/2112.04426

Gen-2 extends the concept toward stateful agent history, provenance, procedures, and effect-aware dependency materialisation.

---

# 10. Proposed one-million-token memory hierarchy

```text
LEVEL 0 — HOT WORKING CONTEXT
~8K–16K typical
highest precision
ordinary local/dense attention

LEVEL 1 — MATERIALISED HISTORICAL CONTEXT
~8K–48K selected old content
raw text and/or recomputed/cached representation
inserted into native working context

LEVEL 2 — CHUNK / EVENT INDEX
256–1024 token chunks or event-aligned units
semantic key
task key
time range / historical position
importance / resonance
quality / confidence
provenance / supersession state

LEVEL 3 — MODUS STRUCTURED MEMORY
claims
events
decisions
evidence
skills
dependencies
effect state

LEVEL 4 — RAW EXACT HISTORY
≥ 1,048,576 exact tokens / events
cold but addressable
append-only where appropriate
```

The hierarchy deliberately does **not** require a permanent 1M-token KV cache.

An old chunk can be:

```text
re-tokenised / recomputed on demand
OR
served from a bounded compressed KV cache
OR
served from a learned compressed representation
```

depending on which variant wins quality-per-GB tests.

---

# 11. Chunk representation

For each historical chunk store:

```yaml
token_start:
token_end:

content_hash:

semantic_key:
retrieval_key:

summary_embedding:
importance:

resonance:
recency:
centrality:
confidence:
conductance_cluster:

provenance:
source_refs:

compressed_kv_ref:
raw_text_ref:
```

The neural retrieval head should operate over learned embeddings.

Modus deterministic priors then rerank / gate the candidates.

---

# 12. Demand-paged cognition

The central long-memory idea is:

> **Do not keep the entire past cognitively active. Keep it exact, addressable, structured, and materialise the relevant working set on demand.**

Analogy:

```text
virtual memory:
large address space
small physical working set

cognitive memory:
large historical address space
small neural working set
```

Example:

```text
current task
    ↓
requires(project_decision_381)
    ↓
resolve structural/content identity
    ↓
follow current-state + provenance edges
    ↓
retrieve exact memory + evidence
    ↓
materialise into native context window
    ↓
continue reasoning
```

## 12.1 MemGPT prior art

MemGPT is essential prior art because it explicitly frames LLM context management using a virtual-memory analogy and hierarchical memory tiers.

Reference:

- https://arxiv.org/abs/2310.08560

Gen-2 should therefore avoid claiming virtual-memory context management itself as novel.

The proposed extension is the combination of:

```text
virtualised historical memory
+
content-addressed identity
+
effect-aware execution state
+
provenance dependency closure
+
validated procedural skills
+
continual governance / lifecycle
```

The scientific question is whether these additional structures improve a small executive beyond ordinary memory paging.

---

# 13. Lazy context evaluation

Modus-style dependency graphs allow something stronger than semantic retrieval.

If an old decision depends on:

```text
claim
→ evidence
→ file version
→ tool result
```

the system can materialise exactly that dependency closure.

Instead of:

```text
"find vaguely similar old prose"
```

we can ask:

```text
"materialise the evidence graph supporting this state"
```

That may be especially powerful for:

- coding;
- research;
- long projects;
- agent state;
- multi-day workflows.

---

# 14. Working-memory packet

The context compiler should emit a typed packet, not a flat blob.

Example:

```yaml
goal:
constraints:

recent_dialogue:

relevant_claims:
relevant_evidence:

active_skills:

open_questions:
contradictions:

tool_state:
side_effect_state:

retrieval_entropy:
confidence_summary:

historical_chunks:
```

Then serialize into model tokens.

This helps the small model understand why material was retrieved.

---

# 15. Neural retrieval head

Generalize Needle's contrastive tool retrieval idea into a shared cognitive retrieval space.

The model query can retrieve:

```text
tools
skills
memory chunks
claims
evidence
documents
```

Candidate architecture:

```text
hidden-state probes
      ↓
contrastive query projection
      ↓
ANN retrieval
      ↓
Top-N candidates
      ↓
Modus deterministic reranker
      ↓
context compiler
```

Test separate vs shared embedding spaces.

---

# 16. Long-context storage arithmetic and cache policy

MiniCPM5 uses GQA with 2 KV heads and head dimension 128, which makes its KV cache cheaper than full multi-head KV—but not free.

For a conventional BF16 KV cache, approximate bytes are:

\[
Bytes = Tokens \times Layers \times 2_{K,V} \times KVHeads \times HeadDim \times BytesPerElement
\]

For the proposed 40-layer expanded model at 1,048,576 tokens:

```text
1,048,576 tokens
× 40 layers
× 2 (K + V)
× 2 KV heads
× 128 dimensions
× 2 bytes BF16
≈ 40 GiB
```

Approximate full-history KV storage if naively retained:

```text
40-layer Gen-2
BF16  ~40 GiB
INT8  ~20 GiB
4-bit ~10 GiB   [ignoring packing/scales/metadata overhead]
```

The 24-layer stock MiniCPM5 equivalent is roughly 24 GiB in BF16 at one million tokens.

By contrast, one million 32-bit token IDs are only about 4 MiB before text/index/metadata overhead.

Therefore distinguish:

```text
RAW TOKEN / EVENT TAPE       cheap enough to retain
STRUCTURED MEMORY            moderate
EMBEDDINGS / INDEX           moderate
HOT KV                       expensive but bounded
COLD FULL-HISTORY KV         very expensive
```

Research variants:

```text
BF16 hot KV only
INT8 bounded historic KV cache
4-bit bounded historic KV cache
compressed latent memory
recompute-on-demand chunks
hybrid cache with eviction
```

The target metric is:

> **effective held-out context capability per resident GB and per unit latency**

not maximum advertised context or maximum cached tokens.

---

# 17. RULER-style effective-context gauntlet

RULER shows why simple needle retrieval is inadequate: models that perform well on basic retrieval still degrade on multi-hop and aggregation as context grows.

Reference:

- https://arxiv.org/abs/2404.06654

The private 1M-context gauntlet should include:

## Retrieval
Recover several exact facts at different depths.

## Multi-hop
```text
A → B → C
```
distributed hundreds of thousands of tokens apart.

## Aggregation
Combine many distributed facts.

## Temporal state
Track the **latest** value after many updates.

## Supersession
Old information is explicitly replaced by new information.

## Provenance
Identify which observation supports a claim.

## Procedure recall
Recover a learned skill used 600K+ tokens ago.

## Tool side effects
Remember which actions actually occurred.

## Distractor resistance
Thousands of semantically similar decoys.

## Structured-memory recovery
Answer after source prose has been compacted into Modus claims/DAGs.

---

# 18. Long-memory autoresearch campaign — reordered

The campaign now starts with the cheapest hypothesis and escalates only when a protected gauntlet exposes a real bottleneck.

```text
LC0  native 131K + external exact history + simple chunk retrieval

LC1  + InfLLM-style external memory baseline

LC2  + Modus structural / temporal metadata reranking

LC3  + dependency-closure materialisation

LC4  + neural retrieval head

LC5  + bounded compressed / quantized historic KV cache

LC6  + learned retention / eviction

LC7  + conductance cluster budgets

LC8  optional positional extension to 256K

LC9  optional positional extension to 512K / 1M

LC10 optional sparse-attention architecture branch
      NSA / InfLLM-V2-inspired only after separate prototype validation
```

At every stage compare against:

```text
B1 MiniCPM5 + vanilla RAG/tools
B2 strong ~4B model + same vanilla RAG/tools
```

Metrics:

```text
retrieval exactness
multi-hop success
aggregation
latest-state tracking
supersession handling
provenance accuracy
procedure recall
distractor resistance
effective context length
context compile p50 / p95
TTFT p50 / p95
decode throughput
peak resident memory
historic bytes/token
successful-task latency
successful-task energy/cost where measurable
```

## 18.1 Positional-extension kill gate

Do not enter LC8 merely because LC7 works.

Enter LC8 only if a meaningful residual error category appears to require more simultaneous token-level neural context rather than better retrieval or structure.

---

# 19. Autoresearch interface for neural and memory experiments

The immutable Research Contract owns the factorial baseline and lockbox rules. This specification must not redefine them.

For neural/memory work, the minimum relevant comparisons are:

```text
B1  MiniCPM5-1B + vanilla tools/RAG
S1  MiniCPM5-1B + validated substrate

B2  strong ~4B + vanilla tools/RAG
S2  strong ~4B + the same validated substrate
```

Neural modifications are then tested **inside S1** against stock MiniCPM5 using the same substrate. The 4B + substrate cell remains visible so a neural improvement cannot be mistaken for a substrate effect or vice versa.

Experiment classes:

```text
MEMORY
Does external exact memory improve latest-state/provenance tasks over native context alone?

RETRIEVAL
Does the learned retrieval head beat the deterministic substrate baseline?

NEURAL DEPTH
Does expansion improve protected stateful task success after latency/memory accounting?

POSITIONAL
Does >131K native context add value beyond demand-paged external memory?

SPARSE ATTENTION
Does architectural surgery beat external-memory controls enough to justify retraining complexity?
```

All material claims require development, replication, and untouched lockbox separation as defined in the Research Contract.

---

# 20. Training curriculum and data governance

The curriculum remains cognition-heavy, but the mixture is an experimental variable.

## 20.1 Starting mixture family

```text
20–25% agent / tool trajectories
15–20% verifiable reasoning + tool-integrated reasoning
10–15% epistemic / abstention / clarification
10–12% terminal / harness operation
 5–10% search / research
 5–10% failure / critique / verification
10–30% general instruction / broad replay
remainder targeted gap-fill
```

Explicitly test general replay at approximately:

```text
10%
20%
30%
```

Material broad-capability regression is a kill signal for the specialised recipe.

## 20.2 Data provenance tiers

### Tier A — trusted / auditable

Candidate sources already identified:

- NVIDIA Nemotron Agentic SFT / RL tool data;
- When2Call;
- NVIDIA QA Abstention;
- ToolMind;
- OpenResearcher;
- NVIDIA Terminal Corpus;
- OpenR1 Math;
- OpenMathReasoning TIR;
- Tracebench.

### Tier B — understood but restricted

Use only within source licence/terms and keep restricted derived checkpoints separated where needed.

### Tier C — frontier-model trace reservoirs / uncertain redistribution rights

Quarantine by default:

- `saidutta69/fable-5-premium`;
- `r0b0tlab/qwen3.8-max-glm5.2-kimi-k3-distillation`;
- `saidutta69/GPT-5.5-Gemini-3.1-Pro-Grok-4-Claude-Fable-Mythos-5-Qwen-3.7-Max-Distillation-Cleaned`.

Before any use:

```text
inspect upstream provenance
inspect licences / usage restrictions
run benchmark-contamination checks
hash/search against protected gauntlets
exclude from final-lockbox construction
run clean-data ablations
```

### Tier D — contaminated / untraceable / incompatible

Reject.

## 20.3 Contamination firewall

Protected gauntlets never enter:

- training mixtures;
- skill mining;
- retrieval indexes;
- synthetic-data prompts;
- reranker training;
- hyperparameter/coefficient sweeps.

## 20.4 VibeThinker implication

Keep VibeThinker-3B as prior art. Its existence means the project should **not** sell “small model punches above its weight on verifiable reasoning” as the core novelty. Its relevant role here is:

1. evidence that specialised post-training can make a ~3B model extremely strong on targeted verifiable reasoning benchmarks;
2. a calibration point for the amount of neural capability available without a substrate;
3. a reason to focus Gen-2 evaluation on persistent state, effects, provenance, memory and procedural reuse.

- https://huggingface.co/WeiboAI/VibeThinker-3B
- https://arxiv.org/abs/2606.16140

---

# 21. Implementation sequence

## Phase C — external memory before long-positional training

1. raw exact history tape;
2. event/chunk index;
3. native 131K + simple external retrieval;
4. InfLLM-style external-memory control;
5. temporal / supersession metadata;
6. provenance-aware retrieval;
7. dependency-closure materialisation;
8. bounded hot context packet;
9. RULER-style + state/provenance gauntlets.

**Gate:** establish how far external memory can scale before changing positional architecture.

## Phase E0 — retrieval / epistemic heads

1. capability / memory retrieval head;
2. evidence-sufficiency head;
3. abstain/search/ask/escalate policy;
4. compare against deterministic-only substrate.

## Phase E1 — depth expansion controls

1. LLaMA-Pro-style identity-preserving expansion;
2. SOLAR-style depth-scaling control;
3. generic expanded-depth SFT;
4. measure gain versus latency/resident memory.

## Phase E2 — Mixture of Training

1. reproduce at 100M–300M scale;
2. only if successful, scaffold-train MiniCPM blocks;
3. cold compose;
4. short interface adaptation;
5. joint SFT / verifiable post-training;
6. swap/probe specialisation gauntlets.

**Gate:** keep expansion only if it beats stock MiniCPM + the same substrate after systems-cost accounting.

## Phase F — optional native long-context research

Enter only if Phase C exposes a failure plausibly caused by insufficient simultaneous neural context.

1. positional extension to 256K;
2. compare with native 131K + external memory;
3. only then consider 512K / 1M;
4. independently prototype sparse-attention adaptation;
5. review NSA / InfLLM-V2-style methods;
6. integrate only after small-scale evidence.

## Phase G — deployment

1. 4-bit MLX;
2. bounded KV-cache policy;
3. Cactus feasibility after architecture stabilises;
4. larger local model as escalation;
5. remote frontier model only as policy-controlled escalation;
6. performance tuning only after capability/safety are stable.

---

# 22. Long-memory gauntlets

```text
LCTX01 — one needle
sanity only

LCTX02 — many needles
multiple exact items

LCTX03 — multi-hop
evidence chain distributed across history

LCTX04 — latest state
hundreds of updates; return current value

LCTX05 — contradictions / supersession
old claims explicitly replaced later

LCTX06 — procedural recall
recover a procedure introduced far earlier

LCTX07 — file evolution
reason about changing versions across a long trace

LCTX08 — provenance
find exact support for a current claim

LCTX09 — distractors
thousands of near-semantic decoys

LCTX10 — compression parity
raw history and compressed structured memory yield the same selected answers
```

RULER-style retrieval/multi-hop/aggregation tasks are necessary but not sufficient; Gen-2 additionally cares about latest-state correctness, effects, provenance, and procedure recall.

---

# 23. Neural-ablation requirements

No neural component is accepted merely because its name sounds cognitively plausible.

For expanded blocks, test:

```text
remove inserted block
swap reasoning ↔ critique blocks
probe hidden-state separability
reasoning-only tasks
action-selection tasks
evidence/critique tasks
pre-training function drift
second-seed replication
```

For retrieval/epistemic heads, compare against:

```text
no head
simple deterministic substrate signal
learned head only
hybrid head + deterministic signal
```

For all modifications report:

```text
task delta
broad-capability retention
TTFT / decode delta
resident-memory delta
calibration delta
replication result
```

---

# 24. Key references

## MiniCPM5

- https://huggingface.co/openbmb/MiniCPM5-1B
- https://huggingface.co/openbmb/MiniCPM5-1B/blob/main/config.json
- https://github.com/OpenBMB/MiniCPM

Key properties used here:

```text
LlamaForCausalLM
24 layers
hidden_size 1536
16 query heads / 2 KV heads
explicit head_dim 128
131,072 native context
```

`head_dim` is explicitly decoupled from `hidden_size / num_attention_heads`; KV arithmetic uses the declared 2 KV heads × 128 dimensions.

## Depth expansion / modular training

- LLaMA-Pro: https://arxiv.org/abs/2401.02415
- SOLAR: https://arxiv.org/abs/2312.15166
- Mixture of Training: https://arxiv.org/abs/2608.13277

LLaMA-Pro/SOLAR are controls; MoT is an experimental hypothesis requiring replication.

## Memory / retrieval

- MemGPT: https://arxiv.org/abs/2310.08560
- HippoRAG: https://arxiv.org/abs/2405.14831
- RETRO: https://arxiv.org/abs/2112.04426
- InfLLM: https://arxiv.org/abs/2402.04617
- InfLLM code: https://github.com/thunlp/InfLLM

## Long context / sparse attention

- LongRoPE: https://arxiv.org/abs/2402.13753
- Native Sparse Attention: https://arxiv.org/abs/2502.11089
- InfLLM-V2: https://arxiv.org/abs/2509.24663
- RULER: https://arxiv.org/abs/2404.06654

## Needle / SAN

- https://github.com/cactus-compute/needle
- https://cactuscompute.com/needle
- https://github.com/cactus-compute/needle/blob/main/needle/model/architecture.py
- https://arxiv.org/abs/2607.18363

## VibeThinker

- https://huggingface.co/WeiboAI/VibeThinker-3B
- https://arxiv.org/abs/2606.16140

## Deployment

- Cactus: https://github.com/cactus-compute/cactus
- Colibri: https://github.com/JustVugg/colibri

---

# 25. Compact thesis

> **Start with stock MiniCPM5 and native 131K. Put the million-token ambition into exact external history, structured state, and demand-paged materialisation. Add neural retrieval heads, depth expansion, positional extension, or sparse attention only when a measured bottleneck proves that the simpler system is insufficient.**
