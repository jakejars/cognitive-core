# Amendment Log

Any change to the Research Contract or frozen constants must be recorded here before the affected evaluation. See Research Contract §11.

## Format

```
## AMEND-{NNN}

- **Date:** YYYY-MM-DD
- **Author:** {who proposed the change}
- **Reason:** {why the change is needed}
- **Observed results motivating change:** {specific results that prompted this}
- **Affected metrics/thresholds/gauntlets:** {what changes}
- **Previously viewed data invalidated?:** yes/no — if yes, specify
- **New untouched evaluation source:** {how we ensure uncontaminated evaluation}
- **Session link:** {link to session entry}
- **Approved by:** {human sign-off}
```

## Index

| # | Date | Summary | Affects |
|---|---|---|---|
| | | | |
## AMEND-003 — Phase C positional extension skip (DEC-001)

- **Date:** 2026-08-18
- **Author:** Cognitive Core protocol ledger
- **Reason:** phase-c--external-memory LongRoPE positional extension not needed (DEC-001: external memory dominates native attention; 100% retrieval at 1M tokens vs 20% native at 100K)
- **Observed results motivating change:** External memory achieves 100% retrieval at 1M tokens; native attention collapses to 20% at 100K
- **Affected metrics/thresholds/gauntlets:** Phase C work item 7 (LongRoPE) not needed; Phase F deferred
- **Previously viewed data invalidated?:** no
- **New untouched evaluation source:** Fresh confirmation campaign matrix; LCTX capability curve re-tests the ceiling
- **Session link:** local M5 Pro calibration session
- **Approved by:** (pending supervisor sign-off)

## AMEND-004 — Local adapter calibration (M5 Pro)

- **Date:** 2026-08-18
- **Author:** Cognitive Core protocol ledger
- **Reason:** MiniCPM5-1B switched from hardcoded MiniCPM3-format template to native apply_chat_template (im_start format, built-in <think> template); Qwen3.5-4B revision pinned to 851bf6e8; golden fixtures recalibrated to actual local pinned checkpoints (hash-verified)
- **Observed results motivating change:** Committed golden token IDs did not match local tokenizers (MiniCPM3/Qwen3-era vocab); Qwen adapter left revision: main
- **Affected metrics/thresholds/gauntlets:** Adapter golden fixtures; Qwen stop tokens 151645/151643 → 248046/248044; MiniCPM template_source → apply_chat_template
- **Previously viewed data invalidated?:** no (no confirmatory receipts existed before calibration)
- **New untouched evaluation source:** Calibrated adapters gate the fresh confirmation campaign
- **Session link:** local M5 Pro calibration session
- **Approved by:** (pending supervisor sign-off)

## AMEND-005 — Phase G Cactus feasibility (not needed)

- **Date:** 2026-08-18
- **Author:** Cognitive Core protocol ledger
- **Reason:** phase-g--deployment Cactus assessed, not needed — MLX is superior on Apple Silicon; 4-bit quantisation delivers 2GB → 580MB (3.4×) with quality preserved
- **Observed results motivating change:** Cactus runtime would duplicate MLX-native quantisation path without benefit on the local stack
- **Affected metrics/thresholds/gauntlets:** Phase G work item 3 (Cactus) not needed
- **Previously viewed data invalidated?:** no
- **New untouched evaluation source:** Re-confirmed against fresh confirmation matrix once available
- **Session link:** local M5 Pro calibration session
- **Approved by:** (pending supervisor sign-off)
