# Long-Memory Gauntlets — LCTX01 through LCTX10

From Memory Spec §22 and Research Contract §9. These gauntlets test the
million-token addressable memory hierarchy.

---

## LCTX01 — One Needle (sanity only)

- **Source:** Memory Spec §22
- **Description:** Sanity check — recover one exact fact buried in long context.
- **Task:** Place one target fact at a known depth (e.g. 50%, 90% of history); verify retrieval.
- **Success criteria:** 100% recall at any single depth up to 131K.

---

## LCTX02 — Many Needles

- **Source:** Memory Spec §22
- **Description:** Multiple exact items distributed across history.
- **Task:** Place 5-10 target facts at various depths; verify all are retrievable.
- **Success criteria:** >= 90% recall at 131K; >= 80% at 512K; >= 70% at 1M.

---

## LCTX03 — Multi-Hop

- **Source:** Memory Spec §22, RULER reference
- **Description:** Evidence chain A → B → C distributed hundreds of thousands of tokens apart.
- **Task:** Answer a question requiring linking facts A, B, C across distant context.
- **Success criteria:** >= 80% correct chain reconstruction.

---

## LCTX04 — Latest State

- **Source:** Memory Spec §22, Research Contract §9
- **Description:** Track the latest value after many updates.
- **Task:** Distribute 100+ updates to a variable across history; query the latest value.
- **Success criteria:** >= 95% latest-value correctness.

---

## LCTX05 — Supersession / Contradictions

- **Source:** Memory Spec §22, Research Contract §9
- **Description:** Old information explicitly replaced by new information.
- **Task:** Place claim, then superseding claim later; verify system uses superseding.
- **Success criteria:** >= 95% correct supersession handling.

---

## LCTX06 — Distant Procedure Recall

- **Source:** Memory Spec §22, Research Contract §9
- **Description:** Recover a learned skill or procedure used 600K+ tokens ago.
- **Task:** Introduce a procedure early in context; require its use much later.
- **Success criteria:** >= 80% correct procedure recall and execution.

---

## LCTX07 — File/Version Evolution

- **Source:** Memory Spec §22
- **Description:** Reason about changing versions across a long trace.
- **Task:** Show evolving file contents across history; ask about specific version state.
- **Success criteria:** >= 85% correct version identification.

---

## LCTX08 — Exact Provenance Recovery

- **Source:** Memory Spec §22, Research Contract §9
- **Description:** Find exact support for a current claim in distant history.
- **Task:** Make a claim that depends on evidence far back; verify evidence retrieval.
- **Success criteria:** >= 90% exact provenance recovery.

---

## LCTX09 — Near-Semantic Distractors

- **Source:** Memory Spec §22, RULER reference
- **Description:** Thousands of semantically similar decoys.
- **Task:** Insert target fact among thousands of semantically similar distractors; verify retrieval.
- **Success criteria:** >= 75% recall with 5000+ distractors.

---

## LCTX10 — Compression Parity

- **Source:** Memory Spec §22
- **Description:** Raw history and compressed structured memory yield the same selected answers.
- **Task:** Answer questions from raw history vs from Modus-structured memory of same content.
- **Success criteria:** >= 90% answer agreement between raw and compressed forms.