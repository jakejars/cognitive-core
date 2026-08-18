# Cactus Feasibility Assessment — Cognitive Core Gen-2

From Memory Spec §21 (Phase G — deployment):
  Item 3: Cactus feasibility after architecture stabilises

## What is Cactus?

Cactus (https://github.com/cactus-compute/cactus) is a cross-platform ML inference
engine by Cactus Compute. It provides:
- Quantisation, kernels, runtime and inference engine
- Targets: mobiles, wearables, smart home, robots
- 5.8k+ GitHub stars, C++ codebase
- Supports: LLM, speech, vision transformers
- Similar to llama.cpp but broader platform support

## Relevance to Cognitive Core Gen-2

| Factor | Assessment |
|---|---|
| **Platform** | Cactus targets edge/mobile; we target Mac (M5 Pro) |
| **Current runtime** | MLX is Apple-optimised and already running |
| **Model format** | Cactus uses GGML/GGUF; we use MLX/safetensors |
| **Quantisation** | Both support 4-bit; Cactus uses GGML format |
| **Performance** | MLX is highly optimised for Apple Silicon |
| **Substrate** | Python-based; Cactus is C++ (integration overhead) |

## Verdict: NOT RECOMMENDED at this stage

**Reasons:**
1. MLX is already highly optimised for Apple Silicon (Metal GPU)
2. Converting models to GGUF format would add overhead
3. The Python substrate would need a C++ bridge
4. Current performance (355 tok/s at 4-bit) is already excellent
5. Edge deployment is not a current target

## When to Revisit

- If targeting non-Apple hardware (Linux, Android, iOS)
- If needing CPU-only inference without Metal
- If Cactus releases an MLX-compatible backend

## Alternative: Pure MLX Deployment

The current MLX-based stack is already deployment-ready:
- **Model:** 4-bit quantised MiniCPM5-1B (580 MB)
- **Runtime:** MLX 0.32 with Metal GPU acceleration
- **Substrate:** Pure Python, no compilation needed
- **Memory:** < 1.2 GiB total
- **Speed:** 350+ tok/s on M5 Pro