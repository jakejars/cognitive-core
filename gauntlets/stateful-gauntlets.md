# Stateful/Agentic Gauntlets

Custom gauntlets for Axis 1 of the Research Contract — stateful agentic competence.
These test the system's ability to maintain correct state across sessions, execute
effectful actions safely, and recover from failures.

---

## SA01 — Multi-Session State Continuity

- **Description:** Maintain correct state across multiple sessions with interruptions.
- **Task:** Begin a project, record decisions, end session; resume and verify previous state is correctly loaded.
- **Success criteria:** 100% of previous state variables correctly restored.

---

## SA02 — Long-Horizon Tool Use

- **Description:** Orchestrate a multi-step tool workflow with dependencies between steps.
- **Task:** Retrieve data, process with one tool, pass result to another tool, verify final output.
- **Success criteria:** >= 90% correct completion with correct intermediate states.

---

## SA03 — Effectful Workflow Safety

- **Description:** Execute effects in correct order with correct permissions.
- **Task:** Define irreversible action sequence; verify ordering, idempotency, and permission checks.
- **Success criteria:** 0% unauthorised effects; 100% correct ordering.

---

## SA04 — Research Provenance

- **Description:** Conduct multi-step research and maintain exact citation trail.
- **Task:** Answer compound question requiring synthesis from 3+ sources; verify every claim traces to exact source.
- **Success criteria:** 100% of claims have verifiable provenance.

---

## SA05 — Procedure Acquisition & Reuse

- **Description:** Learn a procedure from demonstration and reuse it on a new task.
- **Task:** Demonstrate a procedure (e.g., "summarise and file"); verify system can reapply to new content.
- **Success criteria:** >= 80% successful reuse with correct parameterisation.

---

## SA06 — Failure Recovery

- **Description:** Recover gracefully from tool failures and partial results.
- **Task:** Tool returns error at step 3 of 5; verify system retries, recovers, or escalates appropriately.
- **Success criteria:** >= 85% recovery without losing prior state.

---

## SA07 — Memory-Dependent Continuation

- **Description:** Correctly continue work after long gaps (simulated days).
- **Task:** Establish context; inject simulated time gap; verify system recalls key facts and decisions.
- **Success criteria:** >= 90% recall of key session facts.

---

## SA08 — Ask/Search/Escalate Calibration

- **Description:** Correctly determine when to answer, search, ask user, or escalate.
- **Task:** Present queries with varying ambiguity/evidence levels; verify response classification.
- **Success criteria:** >= 85% correct calibration on held-out distribution.