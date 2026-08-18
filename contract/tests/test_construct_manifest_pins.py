import json
from pathlib import Path

from contract.evidence import hash_taskset
from contract.schema import Partition
from harness.experiment_support import load_partition_tasks


def test_construct_ledger_hashes_match_materialised_pilot_and_dev_manifests():
    project = Path(__file__).resolve().parents[2]
    record = json.loads((project / "ledger" / "construct-validity.json").read_text())

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
    expected = (
        record["pilot_taskset_hash"],
        record["dev_taskset_hash"],
        record["pilot"]["materialised_taskset_hash"],
        record["final_dev"]["materialised_taskset_hash"],
    )
    actual = (actual_pilot, actual_dev, actual_pilot, actual_dev)
    assert expected == actual, f"pilot={actual_pilot} dev={actual_dev}"
