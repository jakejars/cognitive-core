import json
from pathlib import Path

import pytest

from contract.evidence import hash_taskset
from contract.schema import Partition
from harness.experiment_support import load_partition_tasks


def _manifest(project: Path, name: str) -> dict:
    return json.loads((project / "gauntlets" / "substrate_construct" / name).read_text())


def test_construct_manifests_and_ledger_pin_materialised_tasksets():
    project = Path(__file__).resolve().parents[2]
    record = json.loads((project / "ledger" / "construct-validity.json").read_text())
    pilot_manifest = _manifest(project, "pilot-v1.json")
    dev_manifest = _manifest(project, "dev-v1.json")

    pilot = load_partition_tasks(
        str(project),
        Partition.DEV,
        task_file=str(project / "gauntlets" / "substrate_construct" / "pilot-v1.json"),
    )
    dev = load_partition_tasks(
        str(project),
        Partition.DEV,
        task_file=str(project / "gauntlets" / "substrate_construct" / "dev-v1.json"),
    )

    actual_pilot = hash_taskset(pilot)
    actual_dev = hash_taskset(dev)
    assert pilot_manifest["materialised_taskset_hash"] == actual_pilot
    assert dev_manifest["materialised_taskset_hash"] == actual_dev
    assert record["pilot_taskset_hash"] == actual_pilot
    assert record["dev_taskset_hash"] == actual_dev
    assert record["pilot"]["materialised_taskset_hash"] == actual_pilot
    assert record["final_dev"]["materialised_taskset_hash"] == actual_dev


def test_loader_rejects_manifest_with_wrong_materialised_hash(tmp_path):
    project = Path(__file__).resolve().parents[2]
    manifest = _manifest(project, "pilot-v1.json")
    manifest["materialised_taskset_hash"] = "0" * 64
    path = tmp_path / "pilot-bad-hash.json"
    path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="materialised taskset hash mismatch"):
        load_partition_tasks(str(project), Partition.DEV, task_file=str(path))
