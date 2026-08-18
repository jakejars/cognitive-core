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
    assert record["pilot_taskset_hash"] == actual_pilot, actual_pilot
    assert record["dev_taskset_hash"] == actual_dev, actual_dev
    assert record["pilot"]["materialised_taskset_hash"] == actual_pilot, actual_pilot
    assert record["final_dev"]["materialised_taskset_hash"] == actual_dev, actual_dev
