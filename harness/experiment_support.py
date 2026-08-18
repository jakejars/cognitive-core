"""Shared experiment support for confirmation and construct-validity runners."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from contract.evidence import hash_task
from contract.schema import ExperimentCell, Partition


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_time(value: str) -> datetime:
    if not value:
        raise ValueError("required protocol timestamp is missing")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _materialize_generator_spec(data: dict, manifest_path: Path) -> list[dict]:
    spec = data.get("generator_spec")
    if not isinstance(spec, dict):
        raise ValueError(f"task file {manifest_path} has no tasks or generator_spec")

    module_name = spec.get("module")
    function_name = spec.get("function")
    if module_name != "gauntlets.substrate_construct.generator" or function_name != "generate_taskset":
        raise ValueError("only the pinned substrate_construct generator is allowed in task manifests")

    module = importlib.import_module(module_name)
    module_path = Path(module.__file__).resolve()
    expected_sha = str(spec.get("generator_sha256", ""))
    if not expected_sha:
        raise ValueError("generator_spec.generator_sha256 is required")
    actual_sha = hashlib.sha256(module_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(
            f"construct generator hash mismatch: expected {expected_sha}, got {actual_sha}"
        )

    tasks = getattr(module, function_name)(
        seed=int(spec["seed"]),
        n_tasks=int(spec["n_tasks"]),
        split=str(spec["split"]),
    )
    expected_counts = data.get("family_counts")
    if expected_counts:
        actual_counts = {
            family: sum(task.get("family") == family for task in tasks)
            for family in expected_counts
        }
        if actual_counts != expected_counts:
            raise ValueError(
                f"generated family counts differ from frozen manifest: {actual_counts} != {expected_counts}"
            )
    return tasks


def _load_json_tasks(path: Path) -> list[dict]:
    with path.open() as f:
        data = json.load(f)

    if isinstance(data, dict) and "generator_spec" in data:
        tasks = _materialize_generator_spec(data, path)
    else:
        tasks = data.get("tasks") if isinstance(data, dict) else data

    if not isinstance(tasks, list) or not tasks:
        raise ValueError(f"task file {path} must materialise a non-empty task list")
    if any(not isinstance(task, dict) or not task.get("id") or not task.get("prompt") for task in tasks):
        raise ValueError(f"task file {path} contains malformed tasks")
    ids = [str(task["id"]) for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"task file {path} contains duplicate task IDs")
    return tasks


def load_partition_tasks(
    project_root: str,
    partition: Partition,
    *,
    task_file: Optional[str] = None,
    gauntlet_filter: Optional[str] = None,
) -> list[dict]:
    """Load the actual evaluation partition.

    DEV may use historical gauntlets for exploratory work. REPLICATION and
    LOCKBOX require an explicit frozen task file. LOCKBOX plaintext must remain
    outside the project/research workspace. Construct generator manifests may be
    used for pilot/DEV/replication, but the generator itself refuses lockbox.
    """
    root = Path(project_root).resolve()

    if task_file:
        path = Path(task_file).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"task file does not exist: {path}")
        if partition == Partition.LOCKBOX and path.is_relative_to(root):
            raise ValueError(
                "lockbox plaintext task file must live outside the research project workspace"
            )
        tasks = _load_json_tasks(path)
    else:
        if partition != Partition.DEV:
            raise ValueError(
                f"{partition.value} evaluation requires an explicit frozen --task-file"
            )
        from gauntlets.gauntlet_tasks import all_tasks
        tasks = all_tasks()

    if gauntlet_filter:
        tasks = [task for task in tasks if task.get("gauntlet") == gauntlet_filter]
        if not tasks:
            raise ValueError(f"no tasks matched gauntlet {gauntlet_filter!r}")
    return tasks


def _ledger_path(project_root: str) -> Path:
    return Path(project_root) / "ledger" / "lockbox-ledger.json"


def _load_lockbox(project_root: str) -> tuple[Path, dict]:
    path = _ledger_path(project_root)
    if not path.is_file():
        raise ValueError("ledger/lockbox-ledger.json is required for lockbox evaluation")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data.get("entries"), dict):
        raise ValueError("lockbox ledger must contain an 'entries' object keyed by task ID")
    return path, data


def _atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def validate_lockbox_taskset(
    project_root: str,
    tasks: list[dict],
    cell: ExperimentCell,
    *,
    now: Optional[str] = None,
) -> None:
    _, data = _load_lockbox(project_root)
    entries = data["entries"]
    now_dt = _parse_time(now or _utc_now())

    for task in tasks:
        task_id = str(task["id"])
        entry = entries.get(task_id)
        if not entry:
            raise ValueError(f"lockbox task {task_id} is absent from the frozen exposure ledger")
        if entry.get("partition") != Partition.LOCKBOX.value:
            raise ValueError(f"lockbox task {task_id} is not frozen as LOCKBOX")
        actual_hash = hash_task(task)
        if entry.get("content_hash") != actual_hash:
            raise ValueError(
                f"lockbox task {task_id} content hash differs from the frozen manifest"
            )

        release = entry.get("authorised_release_at")
        if not release or now_dt < _parse_time(release):
            raise ValueError(f"lockbox task {task_id} has not reached authorised_release_at")

        authorised = set(entry.get("authorised_cells", []))
        if cell.value not in authorised:
            raise ValueError(f"cell {cell.value} is not authorised for lockbox task {task_id}")
        count = int(entry.get("cell_evaluations", {}).get(cell.value, 0))
        if count != 0:
            raise ValueError(
                f"lockbox task {task_id} was already evaluated by cell {cell.value}"
            )

        for exposure in entry.get("exposure_history", []):
            if exposure.get("type") in {"training", "retrieval", "skill_mining"}:
                raise ValueError(
                    f"lockbox task {task_id} has prohibited exposure {exposure.get('type')}"
                )


def mark_lockbox_exposed(
    project_root: str,
    tasks: list[dict],
    *,
    timestamp: Optional[str] = None,
) -> None:
    path, data = _load_lockbox(project_root)
    ts = timestamp or _utc_now()
    for task in tasks:
        entry = data["entries"][str(task["id"])]
        entry.setdefault("first_exposed_at", ts)
        entry.setdefault("first_researcher_exposure_at", ts)
        entry.setdefault("exposure_history", []).append(
            {"type": "authorised_evaluation", "timestamp": ts}
        )
    _atomic_write_json(path, data)


def mark_lockbox_evaluated(
    project_root: str,
    task_id: str,
    cell: ExperimentCell,
    *,
    timestamp: Optional[str] = None,
) -> None:
    path, data = _load_lockbox(project_root)
    entry = data["entries"].get(str(task_id))
    if not entry:
        raise ValueError(f"lockbox task {task_id} is absent from ledger")

    evaluations = entry.setdefault("cell_evaluations", {})
    evaluations[cell.value] = int(evaluations.get(cell.value, 0)) + 1
    entry["evaluation_count"] = int(entry.get("evaluation_count", 0)) + 1
    ts = timestamp or _utc_now()
    entry.setdefault("first_evaluated_at", ts)
    entry.setdefault("exposure_history", []).append(
        {"type": f"evaluation:{cell.value}", "timestamp": ts}
    )
    _atomic_write_json(path, data)
