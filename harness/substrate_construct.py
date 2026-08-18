"""Construct-valid substrate controls shared by the confirmation runner.

S0: same substrate/context path, but only off-topic same-schema records.
O1: perfect recall of a frozen relevant *set* by record ID; no ranking/selection.
S1: real retrieval over the pre-existing task memory.

The current task prompt is never stored before retrieval.
"""

from __future__ import annotations

import random

from contract.schema import ExperimentCell
from substrate.context_compiler import MemoryEntry
from substrate.runtime import SubstrateRuntime


CONSTRUCT_ARMS = ("B1", "B2", "S0", "O1", "S1")

ARM_TO_CELL = {
    "B1": ExperimentCell.B1,
    "B2": ExperimentCell.B2,
    "S0": ExperimentCell.S0,
    "O1": ExperimentCell.O1,
    "S1": ExperimentCell.S1,
}

ARM_MODEL = {
    "B1": "MiniCPM5-1B",
    "B2": "Qwen3.5-4B",
    "S0": "MiniCPM5-1B",
    "O1": "MiniCPM5-1B",
    "S1": "MiniCPM5-1B",
}

SUBSTRATE_ARMS = {"S0", "O1", "S1"}
ABSTENTION_ALLOWED_ARMS = {"B1", "B2", "S0"}

# Consonant-heavy alphabet used to synthesize scorer-neutral opaque words.
# Words are rejected if any actual query token is a substring, matching the
# current ContextCompiler scorer exactly (`word in content_lower`).
_FILLER_ALPHABET = "bcdfghjklmnpqstvwxyz"


def _record_words(records: list[dict]) -> int:
    return sum(len(str(record.get("content", "")).split()) for record in records)


def validate_construct_task(task: dict) -> None:
    """Validate the task can support B1/B2/S0/O1/S1 without leakage."""
    required = (
        "id",
        "prompt",
        "memory_records",
        "null_memory_records",
        "oracle_record_ids",
        "target_entities",
    )
    missing = [key for key in required if not task.get(key)]
    if missing:
        raise ValueError(f"construct task missing required fields: {missing}")

    memory = list(task["memory_records"])
    null_memory = list(task["null_memory_records"])
    memory_ids = {str(record.get("id", "")) for record in memory}
    oracle_ids = [str(record_id) for record_id in task["oracle_record_ids"]]
    missing_oracle = [record_id for record_id in oracle_ids if record_id not in memory_ids]
    if missing_oracle:
        raise ValueError(f"O1 oracle IDs missing from memory_records: {missing_oracle}")
    if len(oracle_ids) < 2:
        raise ValueError("O1 must expose a relevant set, not a single answer record")

    targets = {str(entity) for entity in task["target_entities"]}
    null_entities = {str(record.get("entity_id", "")) for record in null_memory}
    overlap = targets & null_entities
    if overlap:
        raise ValueError(
            f"S0 null records must be off-topic entities; leaked target entities: {sorted(overlap)}"
        )

    if len(null_memory) != len(memory):
        raise ValueError("S0 must contain the same number of same-schema memory records as S1")

    real_words = _record_words(memory)
    null_words = _record_words(null_memory)
    if real_words and not (0.80 <= null_words / real_words <= 1.20):
        raise ValueError(
            f"S0 token/word load must be length matched within 20%; real={real_words}, null={null_words}"
        )

    filler = task.get("history_filler")
    if filler:
        count = int(filler.get("count", 0))
        words = int(filler.get("words_per_record", 0))
        minimum = int(filler.get("minimum_address_space_words", 0))
        if count <= 0 or words <= 0 or count * words < minimum:
            raise ValueError(
                "history filler must meet its declared minimum external address-space word proxy"
            )
        if filler.get("lexicon") not in (None, "disjoint_v1"):
            raise ValueError("unsupported construct filler lexicon")


def _entry(record: dict) -> MemoryEntry:
    return MemoryEntry(
        id=str(record["id"]),
        content=str(record["content"]),
        entry_type=str(record.get("entry_type", "observation")),
        freshness=float(record.get("freshness", 1.0)),
        confidence=float(record.get("confidence", 1.0)),
        provenance=list(record.get("provenance", [])),
        metadata={
            "source": record.get("source", "task_history"),
            "entity_id": record.get("entity_id", ""),
            **dict(record.get("metadata", {})),
        },
    )


def _neutral_filler_pool(task: dict, rng: random.Random, size: int = 64) -> list[str]:
    """Create opaque words with zero overlap under the actual substring scorer."""
    forbidden = {word for word in str(task["prompt"]).casefold().split() if word}
    pool: list[str] = []
    seen = set()
    attempts = 0
    while len(pool) < size and attempts < 10000:
        attempts += 1
        candidate = "".join(rng.choice(_FILLER_ALPHABET) for _ in range(12))
        if candidate in seen:
            continue
        if any(word in candidate for word in forbidden):
            continue
        seen.add(candidate)
        pool.append(candidate)
    if len(pool) < size:
        raise ValueError("could not construct query-disjoint filler vocabulary")
    return pool


def _history_filler(task: dict) -> list[MemoryEntry]:
    spec = task.get("history_filler")
    if not spec:
        return []

    rng = random.Random(int(spec["seed"]))
    count = int(spec["count"])
    words_per_record = int(spec["words_per_record"])
    vocabulary = _neutral_filler_pool(task, rng)
    entries = []
    for index in range(count):
        tokens = [rng.choice(vocabulary) for _ in range(words_per_record)]
        entity_id = f"filler-space-{int(spec['seed'])}-{index:04d}"
        entries.append(MemoryEntry(
            id=f"filler-{int(spec['seed'])}-{index:04d}",
            content=" ".join(tokens),
            entry_type="observation",
            freshness=1.0,
            confidence=1.0,
            metadata={"source": "synthetic_history_filler", "entity_id": entity_id},
        ))
    return entries


def prepare_substrate(rt: SubstrateRuntime, task: dict, *, arm: str) -> None:
    """Load only pre-existing history appropriate for the requested arm."""
    if arm not in SUBSTRATE_ARMS:
        return
    validate_construct_task(task)

    # The same deterministic background address space is present for S0/O1/S1.
    filler = _history_filler(task)
    if filler:
        rt.compiler.store_many(filler)

    records = task["null_memory_records"] if arm == "S0" else task["memory_records"]
    rt.compiler.store_many([_entry(record) for record in records])


def build_model_prompt(rt: SubstrateRuntime | None, task: dict, *, arm: str) -> str:
    """Build the model prompt without ever inserting the current turn first."""
    if arm not in SUBSTRATE_ARMS:
        return str(task["prompt"])
    if rt is None:
        raise ValueError(f"{arm} requires a substrate runtime")

    if arm == "O1":
        packet = rt.compiler.compile_by_ids([str(x) for x in task["oracle_record_ids"]])
    else:
        packet = rt.compiler.compile(str(task["prompt"]), k=int(task.get("retrieve_k", 3)))

    return f"{packet.serialize()}\n\n{task['prompt']}"


def allow_abstention(arm: str) -> bool:
    return arm in ABSTENTION_ALLOWED_ARMS
