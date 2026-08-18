# Substrate Gauntlets — M01 through M12

From Substrate Spec §26 and Research Contract §9. These gauntlets test the
deterministic cognitive substrate components.

---

## M01 — Structural Identity

- **Source:** Substrate Spec §6.1, §27 invariant 1
- **Description:** Equivalent renamed/reformatted procedures collapse to the same structural identity.
- **Task:** Given pairs of semantically equivalent but cosmetically different procedures, verify structural identity matches.
- **Success criteria:** 100% correct collapse; 0% false positives for semantically different procedures.
- **Provenance:** Not applicable (deterministic check).

---

## M02 — Execution Identity

- **Source:** Substrate Spec §6.2, §27 invariant 1
- **Description:** Different semantic arguments never collide merely because structure matches.
- **Task:** Given structurally similar procedures with different actual arguments, verify execution hashes differ.
- **Success criteria:** 100% correct separation; structural hash may match but execution hash must differ.

---

## M03 — Skill Mining

- **Source:** Substrate Spec §8
- **Description:** Recover planted reusable procedures from execution traces.
- **Task:** Inject known procedure patterns into trace corpus; verify miner extracts them.
- **Success criteria:** Recall >= 0.9, Precision >= 0.8.

---

## M04 — Harmful Frequency

- **Source:** Substrate Spec §9
- **Description:** Reject frequent loops that are useless or harmful.
- **Task:** Inject high-frequency but low-value traces; verify promotion pipeline rejects them.
- **Success criteria:** 0% harmful promotion; useful infrequent procedures not suppressed.

---

## M05 — Exact Replay

- **Source:** Substrate Spec §6.2
- **Description:** Promoted pure skills replay exactly.
- **Task:** Execute promoted skill twice with same arguments; verify identical outputs.
- **Success criteria:** 100% bit-exact replay for pure skills.

---

## M06 — Effect Safety

- **Source:** Substrate Spec §4, §27 invariant 3
- **Description:** Prevent duplicate irreversible actions and unauthorised retries.
- **Task:** Attempt to replay/retry an irreversible effect; verify substrate blocks it.
- **Success criteria:** 100% block rate for unauthorised replays.

---

## M07 — Failure-Aware Skill

- **Source:** Substrate Spec §11
- **Description:** Negative traces produce required guards/fallbacks.
- **Task:** Feed failure traces into skill refinement; verify guard conditions are produced.
- **Success criteria:** >= 80% of guardable failure modes are captured.

---

## M08 — Lifecycle Hysteresis

- **Source:** Substrate Spec §15
- **Description:** Noisy quality does not create promote/demote oscillation.
- **Task:** Apply noisy quality signal; verify skill does not rapidly promote/demote.
- **Success criteria:** < 2 state changes per 100 observations at noise amplitude = ±0.2.

---

## M09 — Resonance Without Lock-In

- **Source:** Substrate Spec §12, §12.1
- **Description:** Useful recurrence remains retrievable without locking out better alternatives.
- **Task:** Seed retrieval with frequent but suboptimal candidate; introduce better alternative; verify both remain discoverable.
- **Success criteria:** Better alternative discoverable within top-5 after 1000 reuses of inferior candidate.

---

## M10 — Context Compiler vs Cosine-Only

- **Source:** Substrate Spec §20, §22
- **Description:** Hybrid retrieval beats cosine-only on protected stateful tasks.
- **Task:** Compare cosine-only vs hybrid context compilation on memory tasks.
- **Success criteria:** Hybrid achieves >= 15% relative improvement on latest-state and provenance tasks.

---

## M11 — Retrieval Ambiguity Policy

- **Source:** Substrate Spec §19, §22.3
- **Description:** High ambiguity triggers retrieve/search/ask behaviour appropriately.
- **Task:** Present ambiguous queries with varying entropy levels; verify policy response.
- **Success criteria:** Entropy > threshold triggers non-answer (search/ask/escalate) >= 90% of the time.

---

## M12 — Conductance / Local Overload

- **Source:** Substrate Spec §18
- **Description:** One noisy cluster can be throttled without suppressing unrelated memory.
- **Task:** Flood one memory cluster with requests; verify other clusters' retrieval unaffected.
- **Success criteria:** Suppressed cluster recall drops >= 50%; other clusters recall drops < 10%.