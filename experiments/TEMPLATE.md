# Experiment Template

Use this template for each new experiment. See Research Contract §3.4.

```
## EXP-{NNN} — {Title}

- **Date:** YYYY-MM-DD
- **Phase:** {A/B/C/D/E/F/G}
- **Experimenter:** {agent or human}

### Hypothesis
{What question does this experiment answer?}

### Motivation
{Why do we need to answer this? Which bottleneck or assumption is being tested?}

### Config Diff
{Link to config file or inline diff showing exactly what changed}

### Dataset / Task Slice
{Which gauntlets, data sources, or task families are used}

### Seed
{seed value}

### Budget Consumed
{wall-clock time, compute, researcher time}

### Results

| Metric | Before | After | Delta |
|---|---|---|---|
| ... | ... | ... | ... |

### Analysis
{What did we learn? Was the hypothesis supported? Any surprises?}

### Decision
keep / revert / modify / investigate further

### Rationale
{Why this decision? Link to rune-log decision if applicable.}

### Links
- Session: {link}
- Rune-log: {link}
- Config: {link}
```