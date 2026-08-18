# Cognitive Core Gen-2

**Small neural executive · Deterministic cognitive substrate · Million-token addressable memory**

---

## Quick Navigation

| Area | Path |
|---|---|
| **Specifications** | `docs/specs/` — three authoritative v2.2 docs |
| **Session Log** | `sessions/` — what happened each conversation |
| **Rune Logs** | `rune-logs/` — training runs, decisions, resumption checkpoints |
| **Research Ledger** | `ledger/` — pre-registrations, baselines, amendments |
| **Phases** | `phases/` — phase-specific workbooks and gates |
| **Experiments** | `experiments/` — experimental design and results |
| **Gauntlets** | `gauntlets/` — evaluation tasks and lockbox definitions |
| **Substrate** | `substrate/` — trusted runtime implementation |
| **Neural** | `neural/` — MiniCPM, training, retrieval work |
| **Contract** | `contract/` — executable research protocol invariants |
| **References** | `docs/references/` — prior art notes |

## Falsifiable Thesis

> A small neural executive can reach a better operating point than a substantially larger conventional local agent on **stateful, effectful, long-lived agentic work** when paired with deterministic effect handling, provenance, demand-paged exact memory, and validated reusable procedures.

## Models Used

Model weights are not included in this repository (see `.gitignore`). Download them separately:

| Model | Size | Source | Role |
|---|---|---|---|
| **MiniCPM5-1B** | ~1B params (~2GB FP16, ~580MB 4-bit) | [openbmb/MiniCPM5-1B](https://huggingface.co/openbmb/MiniCPM5-1B) | Small executive (B1, S1) |
| **Qwen3.5-4B** | ~4B params (~8GB) | [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | Strong ~4B control (B2, S2) |

Place downloaded models in `models/`:
```
models/
├── MiniCPM5-1B/        # Full-precision 1B model
├── MiniCPM5-1B-4bit/   # 4-bit quantised variant (580MB)
└── Qwen3.5-4B/         # ~4B baseline model
```

## Setup

```bash
# Python environment
python3 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install mlx mlx-lm

# Download models (or use huggingface-cli)
huggingface-cli download openbmb/MiniCPM5-1B --local-dir models/MiniCPM5-1B
huggingface-cli download Qwen/Qwen3.5-4B --local-dir models/Qwen3.5-4B

# Verify contract invariants
python3 check-invariants.py --summary
```

## Phase Sequence

```
Phase A — Baseline zero and measurement harness
Phase B — Minimal substrate bridge
Phase C — External memory
Phase D — Procedural learning
Phase E — Neural improvements
Phase F — Optional native long-context research
Phase G — Deployment optimisation
```

See [Research Contract](docs/specs/COGNITIVE-CORE-RESEARCH-CONTRACT-v2.2.md) for the complete rules.