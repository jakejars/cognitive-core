# Cognitive Core Gen-2 v2.2 — Current Scientific Status

**Date:** 2026-08-18  
**Classification:** source of truth for current claim status  
**Supersedes:** prior statements that the fresh confirmation campaign was still pending

## Current state

The corrected B1/B2/S1/S2 campaign completed across DEV, replication and lockbox. The experiment machinery worked, but the benchmark did **not** exercise the headline thesis.

### Completed campaign

| Tier | B1 | B2 | S1 | S2 |
|---|---:|---:|---:|---:|
| DEV | 17/20 (85%) | 16/20 (80%) | 14/20 (70%) | 14/20 (70%) |
| Replication | 10/12 (83.3%) | 9/12 (75%) | 10/12 (83.3%) | 9/12 (75%) |
| Lockbox | 7/8 (87.5%) | 6/8 (75%) | 6/8 (75%) | 6/8 (75%) |

DEV S1/B1 latency was approximately **2.55x**, failing the frozen `C_latency=0.20` overhead criterion.

## What this supports

- adapter / model-specific evaluation plumbing works;
- the four-cell runner, receipts, partitions and lockbox accounting operated end-to-end;
- the tested substrate implementation imposed measurable context/latency cost;
- the old DEV treatment reduced MiniCPM task success by 15 percentage points and Qwen by 10 percentage points on that taskset.

Because the old treatment seeded the current prompt into memory before retrieving it, those regressions are retained as **initial null/context-injection tax observations**, not as evidence that useful external memory is harmful.

## Why the headline thesis remains untested

The old taskset did not require the substrate's unique capabilities. It contained no meaningful multi-session dependency, forced external-history dependency, effectful/idempotent cognition, tool use, or substantial supersession reasoning. The substrate could not add information that B1 lacked.

Therefore:

```text
HARNESS / PROTOCOL VALIDATION
SUPPORTED

HEADLINE COGNITIVE-CORE THESIS
UNTESTED

OLD LOCKBOX
CONSUMED / NON-DIAGNOSTIC / NOT REUSABLE
```

Old receipts are preserved. Their interpretation changes; the measurements are not deleted.

## Active experiment

The next experiment is construct validation, not model modification.

Arms:

```text
B1  MiniCPM5-1B bare
B2  Qwen3.5-4B bare size control
S0  MiniCPM + same-schema length-matched off-topic null retrieval
O1  MiniCPM + oracle perfect recall of the full relevant set
S1  MiniCPM + real retrieval
```

Primary decomposition:

```text
S0 - B1  = context/substrate tax
S1 - S0  = useful information value
O1 - S1  = retrieval-system loss
S1 - B1  = net substrate effect
```

The benchmark uses deterministic typed intent/field scoring with separate `supported_correct`, `correct_abstention`, and `confident_wrong` outcomes. Supersession/conflict is the dominant family.

Pilot and frozen final DEV are distinct generator samples:

- `gauntlets/substrate_construct/pilot-v1.json`
- `gauntlets/substrate_construct/dev-v1.json`

No replication sample is created until construct-valid DEV passes. No new lockbox may be created until independent replication also demonstrates the preregistered separation.

## Neural / dataset work

Paused. No cognitive-policy SFT, COGDATA curriculum, recurrent-depth conversion, adaptive halting, or DiffusionBlocks modification should begin until the prompted external-cognition/substrate experiments produce a real replicated signal.
