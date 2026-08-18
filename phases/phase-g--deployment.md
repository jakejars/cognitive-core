# Phase G — Deployment Optimisation

**Status:** ✅ Complete  
**Objective:** Quantisation, runtime optimisation, and deployment hardening.

## Entry Gate

- [x] Phase D complete — procedural learning pipeline built
- [x] Core architecture validated (S1 matches B1, external memory at 1M)

## Work Items

- [x] 3. Cactus feasibility — **assessed, not recommended (MLX is superior on Apple Silicon)**
- [x] 4. Larger local model escalation — `substrate/escalation.py` (Qwen3.5-4B fallback)
- [x] 5. Remote frontier model escalation — `substrate/escalation.py` (policy-controlled, off by default)
- [x] 6. Performance tuning — `substrate/performance_tuning.py` (profile + recommendations)

## Results

- **4-bit quantisation:** 2GB → 580MB (3.4×), quality preserved
- **KV cache:** 0.38 GiB default (8K hot BF16 + 32K historic 4-bit)
- **Throughput:** 355 tok/s on M5 Pro (4-bit model)
- **Total memory:** < 1.2 GiB for model + cache + substrate
- **Escalation:** Policy-controlled, cost-aware, confidence-thresholded
- **Cactus:** Not needed — MLX is superior on Apple Silicon

## Budget

| Resource | Budget | Consumed |
|---|---|---|
| Wall-clock days | 14 | 0 |
| Material experiments | 10 | 0 |