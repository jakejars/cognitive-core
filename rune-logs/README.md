# Rune Logs — Training Runs, Experiments & Resumption Checkpoints

Rune logs are the **operational memory** of the project. They capture what was actually done, what the results were, and — crucially — the *why* behind each decision so work can resume after any gap.

## Types of Rune Entry

### 1. Training Runs
Every training, fine-tuning, or adaptation run gets a file:

```
rune-logs/train/TRAIN-001--identity-preserving-depth-expansion.md
```

Contents:
- **Hypothesis:** what question this run answers
- **Config:** hyperparameters, model, data slice
- **Command / reproduction:** exact command or config diff
- **Results:** metrics, losses, screenshots/links
- **Analysis:** what we learned
- **Decision:** promote / revert / modify / investigate further
- **Link to session:** which session(s) created this run

### 2. Decision Records
Architectural or procedural decisions that don't involve training:

```
rune-logs/decisions/DEC-001--use-infllm-as-first-long-context-baseline.md
```

Contents:
- **Context:** what prompted the decision
- **Options considered:** at least two
- **Chosen path:** with rationale
- **Trade-offs acknowledged:** what was deprioritised
- **Link to session:** which session(s)

### 3. Resumption Checkpoints
Written at the end of each session, these explain how to pick up:

```
rune-logs/checkpoints/2026-08-18--session-resumption.md
```

Contents:
- **Situation summary:** one paragraph
- **Last operations:** what was being built/tested
- **Blockers:** anything waiting on tooling, data, or human input
- **Suggested first action:** the next concrete step
- **Active branches:** any parallel workstreams

## File Naming

```
rune-logs/train/TRAIN-{NNN}--{short-kebab-description}.md
rune-logs/decisions/DEC-{NNN}--{short-kebab-description}.md
rune-logs/checkpoints/YYYY-MM-DD--session-resumption.md
```

## Index File

The `rune-logs/INDEX.md` file tracks all rune entries in reverse chronological order so you can find anything quickly.