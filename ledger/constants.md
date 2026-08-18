# Frozen Constants

These constants are frozen at Phase-A exit and govern all subsequent evaluation. They are **not** to be changed after substrate results are observed, except via the amendment process (Research Contract §11).

## Target Constants

| Constant | Symbol | Value | Notes |
|---|---|---|---|
| Task retention/superiority | C_success | 0.95 | S1 task success ≥ 0.95 × S2 task success |
| Model-memory advantage | C_memory | 0.50 | S1 model-resident memory ≤ 0.50 × S2 model-resident memory |
| Substrate latency overhead | C_latency | 0.20 | Substrate p95 latency ≤ (1 + 0.20) × vanilla baseline latency |
| Trust advantage | C_trust | 0.50 | Effect/provenance/state error rate ≤ 0.50 × vanilla baseline |

## Calibration Basis (Phase A)

Measured B1 vs B2 on 4 representative prompts (factual, reasoning, coding, explanation):

| Metric | B1 (MiniCPM5-1B) | B2 (Qwen3.5-4B) | Ratio |
|---|---|---|---|
| Params | 1.08B | ~4B | 3.7× |
| Layers | 24 | 32 | 1.3× |
| Model memory est. | ~2.0 GB | ~8.0 GB | 4× |
| Load time | 0.34s | 0.57s | 1.7× |
| Mean inference | 1.36s | 7.79s | 5.7× |
| Mean tok/s | 102.5 | 29.2 | 0.28× |

**Preliminary assessment:** B1 is substantially faster but less verbose. B2 includes thinking/chain-of-thought tokens. Proper comparison on gauntlet tasks (not free-form prompts) is needed to calibrate C_success.

## Process

1. Measure during Phase A to calibrate realistic ranges ✅
2. Freeze exact values **before** Phase B substrate evaluation begins ⬜
3. Record the freeze date and session here

## Amendments

| Date | Constant | Old Value | New Value | Reason | Session |
|---|---|---|---|---|---|
| | | | | | |