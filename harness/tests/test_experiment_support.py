import json
from pathlib import Path

import pytest

from contract.schema import ExperimentCell, Partition
from harness.experiment_support import (
    load_partition_tasks,
    validate_lockbox_taskset,
    mark_lockbox_evaluated,
)


def test_replication_requires_explicit_task_file(tmp_path):
    with pytest.raises(ValueError, match=r"task[- ]file"):
        load_partition_tasks(str(tmp_path), Partition.REPLICATION, task_file=None)


def test_lockbox_task_file_must_be_outside_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    task_file = project / "lockbox.json"
    task_file.write_text(json.dumps([{"id": "x", "prompt": "secret", "expected": "a"}]))

    with pytest.raises(ValueError, match="outside"):
        load_partition_tasks(str(project), Partition.LOCKBOX, task_file=str(task_file))


def test_lockbox_taskset_must_match_frozen_hashes(tmp_path):
    project = tmp_path / "project"
    (project / "ledger").mkdir(parents=True)
    tasks = [{"id": "L1", "prompt": "secret", "expected": "a"}]
    (project / "ledger" / "lockbox-ledger.json").write_text(json.dumps({
        "entries": {
            "L1": {
                "content_hash": "wrong",
                "partition": "lockbox",
                "created_at": "2026-08-18T00:00:00+00:00",
                "frozen_at": "2026-08-18T01:00:00+00:00",
                "authorised_release_at": "2026-08-18T02:00:00+00:00",
                "authorised_cells": ["B1"],
                "cell_evaluations": {}
            }
        }
    }))

    with pytest.raises(ValueError, match="content hash"):
        validate_lockbox_taskset(str(project), tasks, ExperimentCell.B1, now="2026-08-18T03:00:00+00:00")


def test_lockbox_accounting_is_per_cell(tmp_path):
    project = tmp_path / "project"
    (project / "ledger").mkdir(parents=True)
    tasks = [{"id": "L1", "prompt": "secret", "expected": "a"}]

    from contract.evidence import hash_task
    ledger_path = project / "ledger" / "lockbox-ledger.json"
    ledger_path.write_text(json.dumps({
        "entries": {
            "L1": {
                "content_hash": hash_task(tasks[0]),
                "partition": "lockbox",
                "created_at": "2026-08-18T00:00:00+00:00",
                "frozen_at": "2026-08-18T01:00:00+00:00",
                "authorised_release_at": "2026-08-18T02:00:00+00:00",
                "authorised_cells": ["B1", "B2"],
                "cell_evaluations": {}
            }
        }
    }))

    validate_lockbox_taskset(str(project), tasks, ExperimentCell.B1, now="2026-08-18T03:00:00+00:00")
    mark_lockbox_evaluated(str(project), "L1", ExperimentCell.B1, timestamp="2026-08-18T03:01:00+00:00")
    validate_lockbox_taskset(str(project), tasks, ExperimentCell.B2, now="2026-08-18T03:02:00+00:00")

    with pytest.raises(ValueError, match="already evaluated"):
        validate_lockbox_taskset(str(project), tasks, ExperimentCell.B1, now="2026-08-18T03:03:00+00:00")
