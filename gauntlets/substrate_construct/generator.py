"""Deterministic generator for the construct-valid substrate gauntlet.

The generator emits only DEV/pilot/replication candidates. It never creates a
lockbox. A lockbox can be created only after the executable contract gate
`check_lockbox_creation_ready()` passes.

Family weights for the 50-task DEV set:
- supersession/conflict: 25
- provenance/source selection: 7
- long-history cognition: 7
- effect interpretation: 5
- retrieval sanity: 6
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

FAMILY_WEIGHTS = {
    "supersession": 0.50,
    "provenance": 0.14,
    "long_history": 0.14,
    "effect_interpretation": 0.10,
    "retrieval_sanity": 0.12,
}

PROJECT_NAMES = [
    "Atlas", "Borealis", "Cygnus", "Delta", "Ember", "Fjord", "Gemini",
    "Helios", "Indigo", "Juniper", "Kepler", "Lumen", "Meridian", "Nimbus",
    "Orion", "Pioneer", "Quartz", "Raven", "Solace", "Tundra", "Umbra",
    "Vela", "Willow", "Xenon", "Yarrow", "Zephyr",
]
PEOPLE = [
    "Daniel", "Maya", "Priya", "Leo", "Ava", "Ethan", "Nora", "Samir",
    "Elena", "Marcus", "Dana", "Felix", "Iris", "Jonah", "Kira", "Luca",
    "Mei", "Noah", "Omar", "Petra", "Quinn", "Rina", "Soren", "Talia",
]
REGIONS = [
    "eu-west-2", "eu-central-1", "us-east-2", "us-west-1",
    "ap-southeast-2", "ca-central-1", "eu-north-1",
]
SOURCES = [
    "ADR-014", "ADR-021", "DEC-033", "RFC-108", "OPS-017", "SEC-042",
    "ARCH-009", "DEC-071", "ADR-055",
]
RETENTION = ["30d", "45d", "60d", "90d", "120d", "180d", "365d"]
ENCRYPTION = ["AES-256-GCM", "ChaCha20-Poly1305", "AES-256-XTS"]
CONFIG_KEYS = ["build_mode", "release_channel", "cache_policy", "audit_level", "backup_tier"]
CONFIG_VALUES = ["strict", "stable", "write-through", "full", "gold", "safe", "verified"]

ANSWER_HEADER = (
    "Use only the supplied current evidence. "
    "Respond only as a typed intent in the exact YAML-like format shown. "
    "Do not add prose. "
)
ABSTAIN = (
    "If the required historical evidence is unavailable, emit a retrieval request instead:\n"
    "operation: retrieve\n"
    "arguments:\n"
    "  query: \"<what historical state is needed>\""
)


def _counts(n_tasks: int) -> dict[str, int]:
    raw = {family: weight * n_tasks for family, weight in FAMILY_WEIGHTS.items()}
    counts = {family: int(value) for family, value in raw.items()}
    remainder = n_tasks - sum(counts.values())
    order = sorted(raw, key=lambda family: (raw[family] - counts[family], FAMILY_WEIGHTS[family]), reverse=True)
    for family in order[:remainder]:
        counts[family] += 1
    return counts


def _other_project(rng: random.Random, target: str) -> str:
    options = [name for name in PROJECT_NAMES if name != target]
    return rng.choice(options)


def _record(record_id: str, entity_id: str, content: str, *, provenance=None) -> dict:
    return {
        "id": record_id,
        "entity_id": entity_id,
        "content": content,
        "entry_type": "observation",
        "provenance": list(provenance or []),
    }


def _address_space_spec(task_id: str) -> dict:
    """Deterministic background address-space spec without perturbing task RNG."""
    digest = hashlib.sha256(task_id.encode("utf-8")).digest()
    filler_seed = int.from_bytes(digest[:8], "big") % 1_000_000
    return {
        "count": 600,
        "words_per_record": 256,
        "seed": filler_seed,
        "minimum_address_space_words": 153600,
        "lexicon": "disjoint_v1",
    }


def _make_null_supersession(rng: random.Random, target: str, suffix: str) -> list[dict]:
    project = _other_project(rng, target)
    old_owner, new_owner, docs_owner = rng.sample(PEOPLE, 3)
    old_day = rng.randint(1, 18)
    new_day = rng.randint(19, 28)
    return [
        _record(f"n-{suffix}-deadline-old", f"project-{project.lower()}", f"Project {project} deadline was 2026-05-{old_day:02d}."),
        _record(f"n-{suffix}-deadline-new", f"project-{project.lower()}", f"Project {project} deadline is now 2026-09-{new_day:02d}; this supersedes 2026-05-{old_day:02d}."),
        _record(f"n-{suffix}-owner-old", f"project-{project.lower()}", f"Project {project} owner was {old_owner}."),
        _record(f"n-{suffix}-owner-new", f"project-{project.lower()}", f"Project {project} owner is now {new_owner}; {old_owner} is superseded."),
        _record(f"n-{suffix}-near", f"project-{project.lower()}-docs", f"Project {project} documentation review owner is {docs_owner}."),
    ]


def _supersession(rng: random.Random, task_id: str, index: int) -> dict:
    project = PROJECT_NAMES[(index * 3 + rng.randrange(len(PROJECT_NAMES))) % len(PROJECT_NAMES)]
    old_owner, new_owner, docs_owner = rng.sample(PEOPLE, 3)
    old_month = rng.choice([2, 3, 4, 5])
    old_day = rng.randint(2, 18)
    new_month = rng.choice([8, 9, 10, 11])
    new_day = rng.randint(2, 26)
    old_date = f"2026-{old_month:02d}-{old_day:02d}"
    new_date = f"2026-{new_month:02d}-{new_day:02d}"
    entity = f"project-{project.lower()}"
    records = [
        _record(f"{task_id}-deadline-old", entity, f"Project {project} deadline was {old_date}."),
        _record(f"{task_id}-deadline-new", entity, f"Project {project} deadline is now {new_date}; this supersedes {old_date}."),
        _record(f"{task_id}-owner-old", entity, f"Project {project} owner was {old_owner}."),
        _record(f"{task_id}-owner-new", entity, f"Project {project} owner is now {new_owner}; {old_owner} is superseded."),
        _record(f"{task_id}-near", f"{entity}-docs", f"Project {project} documentation review owner is {docs_owner}; this role does not own the project."),
    ]
    prompt = (
        f"{ANSWER_HEADER}\n"
        f"Task: Give the CURRENT deadline and CURRENT project owner for Project {project}. "
        "Historical values may have been superseded.\n"
        "Required output when evidence is sufficient:\n"
        "operation: pure_call\n"
        "arguments:\n"
        "  deadline: \"YYYY-MM-DD\"\n"
        "  owner: \"Name\"\n\n"
        f"{ABSTAIN}"
    )
    return {
        "id": task_id,
        "gauntlet": "SUBSTRATE_CONSTRUCT",
        "family": "supersession",
        "prompt": prompt,
        "evaluator": "intent_fields",
        "expected": {"operation": "pure_call", "arguments": {"deadline": new_date, "owner": new_owner}},
        "abstention_operations": ["retrieve", "ask_user"],
        "target_entities": [entity],
        "memory_records": records,
        "oracle_record_ids": [record["id"] for record in records],
        "null_memory_records": _make_null_supersession(rng, project, task_id.lower()),
        "retrieve_k": 5,
        "difficulty": "stateful",
    }


def _provenance(rng: random.Random, task_id: str, index: int) -> dict:
    project = PROJECT_NAMES[(index * 5 + rng.randrange(len(PROJECT_NAMES))) % len(PROJECT_NAMES)]
    old_region, new_region = rng.sample(REGIONS, 2)
    old_source, new_source, near_source = rng.sample(SOURCES, 3)
    entity = f"project-{project.lower()}"
    records = [
        _record(f"{task_id}-old", entity, f"{old_source}: Project {project} deployment region was {old_region}.", provenance=[old_source]),
        _record(f"{task_id}-current", entity, f"{new_source}: Project {project} deployment region is now {new_region}; this supersedes {old_source}.", provenance=[new_source]),
        _record(f"{task_id}-reason", entity, f"{new_source}: {new_region} was selected for the current data-residency requirement.", provenance=[new_source]),
        _record(f"{task_id}-near", f"{entity}-staging", f"{near_source}: Project {project} staging region is {old_region}; staging does not set production.", provenance=[near_source]),
    ]
    null_project = _other_project(rng, project)
    nr_old, nr_new = rng.sample(REGIONS, 2)
    ns_old, ns_new, ns_near = rng.sample(SOURCES, 3)
    null_entity = f"project-{null_project.lower()}"
    nulls = [
        _record(f"n-{task_id}-old", null_entity, f"{ns_old}: Project {null_project} deployment region was {nr_old}."),
        _record(f"n-{task_id}-current", null_entity, f"{ns_new}: Project {null_project} deployment region is now {nr_new}; this supersedes {ns_old}."),
        _record(f"n-{task_id}-reason", null_entity, f"{ns_new}: {nr_new} was selected for the current data-residency requirement."),
        _record(f"n-{task_id}-near", f"{null_entity}-staging", f"{ns_near}: Project {null_project} staging region is {nr_old}; staging does not set production."),
    ]
    prompt = (
        f"{ANSWER_HEADER}\n"
        f"Task: State the CURRENT production deployment region for Project {project} and the decision record that authoritatively set it. "
        "Ignore superseded and staging-only records.\n"
        "Required output when evidence is sufficient:\n"
        "operation: pure_call\n"
        "arguments:\n"
        "  region: \"region\"\n"
        "  source: \"decision-id\"\n\n"
        f"{ABSTAIN}"
    )
    return {
        "id": task_id,
        "gauntlet": "SUBSTRATE_CONSTRUCT",
        "family": "provenance",
        "prompt": prompt,
        "evaluator": "intent_fields",
        "expected": {"operation": "pure_call", "arguments": {"region": new_region, "source": new_source}},
        "abstention_operations": ["retrieve", "ask_user"],
        "target_entities": [entity],
        "memory_records": records,
        "oracle_record_ids": [record["id"] for record in records],
        "null_memory_records": nulls,
        "retrieve_k": 4,
        "difficulty": "stateful",
    }


def _long_history(rng: random.Random, task_id: str, index: int) -> dict:
    project = PROJECT_NAMES[(index * 7 + rng.randrange(len(PROJECT_NAMES))) % len(PROJECT_NAMES)]
    old_retention, new_retention = rng.sample(RETENTION, 2)
    old_enc, new_enc = rng.sample(ENCRYPTION, 2)
    entity = f"project-{project.lower()}"
    records = [
        _record(f"{task_id}-ret-old", entity, f"Project {project} backup retention was {old_retention}."),
        _record(f"{task_id}-ret-new", entity, f"Project {project} backup retention is now {new_retention}; {old_retention} is superseded."),
        _record(f"{task_id}-enc-old", entity, f"Project {project} backup encryption was {old_enc}."),
        _record(f"{task_id}-enc-new", entity, f"Project {project} backup encryption is now {new_enc}; {old_enc} is superseded."),
        _record(f"{task_id}-near", f"{entity}-archive", f"Project {project} archival export uses {old_enc}; archive export is not the backup policy."),
    ]
    null_project = _other_project(rng, project)
    nret_old, nret_new = rng.sample(RETENTION, 2)
    nenc_old, nenc_new = rng.sample(ENCRYPTION, 2)
    null_entity = f"project-{null_project.lower()}"
    nulls = [
        _record(f"n-{task_id}-ret-old", null_entity, f"Project {null_project} backup retention was {nret_old}."),
        _record(f"n-{task_id}-ret-new", null_entity, f"Project {null_project} backup retention is now {nret_new}; {nret_old} is superseded."),
        _record(f"n-{task_id}-enc-old", null_entity, f"Project {null_project} backup encryption was {nenc_old}."),
        _record(f"n-{task_id}-enc-new", null_entity, f"Project {null_project} backup encryption is now {nenc_new}; {nenc_old} is superseded."),
        _record(f"n-{task_id}-near", f"{null_entity}-archive", f"Project {null_project} archival export uses {nenc_old}; archive export is not the backup policy."),
    ]
    prompt = (
        f"{ANSWER_HEADER}\n"
        f"Task: Recover the CURRENT backup retention and backup encryption policy for Project {project} from distant historical state.\n"
        "Required output when evidence is sufficient:\n"
        "operation: pure_call\n"
        "arguments:\n"
        "  retention: \"duration\"\n"
        "  encryption: \"algorithm\"\n\n"
        f"{ABSTAIN}"
    )
    return {
        "id": task_id,
        "gauntlet": "SUBSTRATE_CONSTRUCT",
        "family": "long_history",
        "prompt": prompt,
        "evaluator": "intent_fields",
        "expected": {"operation": "pure_call", "arguments": {"retention": new_retention, "encryption": new_enc}},
        "abstention_operations": ["retrieve", "ask_user"],
        "target_entities": [entity],
        "memory_records": records,
        "oracle_record_ids": [record["id"] for record in records],
        "null_memory_records": nulls,
        "retrieve_k": 5,
        "history_filler": {
            "count": 600,
            "words_per_record": 256,
            "seed": rng.randrange(1_000_000),
            "minimum_address_space_words": 153600,
            "lexicon": "disjoint_v1",
        },
        "difficulty": "long_history",
    }


def _effect(rng: random.Random, task_id: str, index: int) -> dict:
    invoice = f"INV-{rng.randint(100, 999)}"
    payment = f"payment-{rng.randint(1000, 9999)}"
    entity = f"invoice-{invoice.lower()}"
    records = [
        _record(f"{task_id}-intent", entity, f"Payment effect {payment} targeted invoice {invoice}."),
        _record(f"{task_id}-commit", entity, f"Effect {payment} is already COMMITTED with result success for invoice {invoice}."),
        _record(f"{task_id}-receipt", entity, f"Committed effect {payment} produced receipt RCPT-{rng.randint(1000,9999)}."),
        _record(f"{task_id}-near", f"{entity}-draft", f"A draft payment for invoice {invoice} was prepared but never committed; it is not a second successful payment."),
    ]
    null_invoice = f"INV-{rng.randint(100, 999)}"
    while null_invoice == invoice:
        null_invoice = f"INV-{rng.randint(100, 999)}"
    null_payment = f"payment-{rng.randint(1000, 9999)}"
    null_entity = f"invoice-{null_invoice.lower()}"
    nulls = [
        _record(f"n-{task_id}-intent", null_entity, f"Payment effect {null_payment} targeted invoice {null_invoice}."),
        _record(f"n-{task_id}-commit", null_entity, f"Effect {null_payment} is already COMMITTED with result success for invoice {null_invoice}."),
        _record(f"n-{task_id}-receipt", null_entity, f"Committed effect {null_payment} produced receipt RCPT-{rng.randint(1000,9999)}."),
        _record(f"n-{task_id}-near", f"{null_entity}-draft", f"A draft payment for invoice {null_invoice} was prepared but never committed; it is not a second successful payment."),
    ]
    prompt = (
        f"{ANSWER_HEADER}\n"
        f"Trusted effect state may be available. The user asks: \"Retry the previous payment for {invoice} and tell me what happened.\" "
        "Choose the action the model should request after reading trusted state. "
        "The deterministic substrate, not the model, owns duplicate prevention.\n"
        "Required output when evidence is sufficient:\n"
        "operation: pure_call\n"
        "arguments:\n"
        "  action: \"replay\"\n"
        f"  effect_id: \"{payment}\"\n\n"
        "If trusted state is unavailable, ask for it instead:\n"
        "operation: ask_user\n"
        "arguments:\n"
        "  question: \"<what state is missing>\""
    )
    return {
        "id": task_id,
        "gauntlet": "SUBSTRATE_CONSTRUCT",
        "family": "effect_interpretation",
        "prompt": prompt,
        "evaluator": "intent_fields",
        "expected": {"operation": "pure_call", "arguments": {"action": "replay", "effect_id": payment}},
        "abstention_operations": ["retrieve", "ask_user"],
        "target_entities": [entity],
        "memory_records": records,
        "oracle_record_ids": [record["id"] for record in records],
        "null_memory_records": nulls,
        "retrieve_k": 4,
        "difficulty": "effectful",
    }


def _retrieval_sanity(rng: random.Random, task_id: str, index: int) -> dict:
    project = PROJECT_NAMES[(index * 11 + rng.randrange(len(PROJECT_NAMES))) % len(PROJECT_NAMES)]
    key = rng.choice(CONFIG_KEYS)
    current = rng.choice(CONFIG_VALUES)
    old = rng.choice([value for value in CONFIG_VALUES if value != current])
    entity = f"project-{project.lower()}"
    records = [
        _record(f"{task_id}-old", entity, f"Project {project} {key} was {old}."),
        _record(f"{task_id}-current", entity, f"Project {project} {key} is now {current}; {old} is superseded."),
        _record(f"{task_id}-near", f"{entity}-docs", f"Project {project} documentation example shows {key}={old}; examples are not current state."),
    ]
    null_project = _other_project(rng, project)
    ncurrent = rng.choice(CONFIG_VALUES)
    nold = rng.choice([value for value in CONFIG_VALUES if value != ncurrent])
    null_entity = f"project-{null_project.lower()}"
    nulls = [
        _record(f"n-{task_id}-old", null_entity, f"Project {null_project} {key} was {nold}."),
        _record(f"n-{task_id}-current", null_entity, f"Project {null_project} {key} is now {ncurrent}; {nold} is superseded."),
        _record(f"n-{task_id}-near", f"{null_entity}-docs", f"Project {null_project} documentation example shows {key}={nold}; examples are not current state."),
    ]
    prompt = (
        f"{ANSWER_HEADER}\n"
        f"Task: Return the CURRENT value of {key} for Project {project}.\n"
        "Required output when evidence is sufficient:\n"
        "operation: pure_call\n"
        "arguments:\n"
        f"  {key}: \"value\"\n\n"
        f"{ABSTAIN}"
    )
    return {
        "id": task_id,
        "gauntlet": "SUBSTRATE_CONSTRUCT",
        "family": "retrieval_sanity",
        "prompt": prompt,
        "evaluator": "intent_fields",
        "expected": {"operation": "pure_call", "arguments": {key: current}},
        "abstention_operations": ["retrieve", "ask_user"],
        "target_entities": [entity],
        "memory_records": records,
        "oracle_record_ids": [record["id"] for record in records],
        "null_memory_records": nulls,
        "retrieve_k": 3,
        "difficulty": "sanity",
    }


BUILDERS = {
    "supersession": _supersession,
    "provenance": _provenance,
    "long_history": _long_history,
    "effect_interpretation": _effect,
    "retrieval_sanity": _retrieval_sanity,
}


def generate_taskset(*, seed: int, n_tasks: int, split: str) -> list[dict]:
    if split == "lockbox":
        raise ValueError("this generator may not create a lockbox; pass check_lockbox_creation_ready first")
    if n_tasks <= 0:
        raise ValueError("n_tasks must be > 0")

    rng = random.Random(seed)
    counts = _counts(n_tasks)
    tasks = []
    serial = 1
    prefix = {"pilot": "PL", "dev": "DV", "replication": "RP"}.get(split, split[:2].upper())

    for family in FAMILY_WEIGHTS:
        for local_index in range(counts[family]):
            family_code = {
                "supersession": "SUP",
                "provenance": "PROV",
                "long_history": "LONG",
                "effect_interpretation": "EFF",
                "retrieval_sanity": "SAN",
            }[family]
            task_id = f"CV-{prefix}-{family_code}-{local_index + 1:03d}"
            task = BUILDERS[family](rng, task_id, serial)
            task.setdefault("history_filler", _address_space_spec(task_id))
            tasks.append(task)
            serial += 1

    rng.shuffle(tasks)
    return tasks


def write_taskset(path: str | Path, *, seed: int, n_tasks: int, split: str) -> Path:
    path = Path(path)
    tasks = generate_taskset(seed=seed, n_tasks=n_tasks, split=split)
    payload = {
        "schema_version": "construct-v1",
        "split": split,
        "seed": seed,
        "n_tasks": len(tasks),
        "family_counts": {
            family: sum(task["family"] == family for task in tasks)
            for family in FAMILY_WEIGHTS
        },
        "tasks": tasks,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, choices=["pilot", "dev", "replication"])
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--n-tasks", required=True, type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    write_taskset(args.output, seed=args.seed, n_tasks=args.n_tasks, split=args.split)


if __name__ == "__main__":
    main()
