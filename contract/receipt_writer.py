"""Receipt Writer — the sole sanctioned mechanism for recording experiment runs.

DEV receipts may omit expensive checkpoint provenance, but they must still bind the
actual task set and raw/result outputs. REPLICATION and LOCKBOX receipts are
confirmatory evidence and therefore require the full provenance bundle.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from contract.schema import (
    ExperimentCell,
    ExperimentReceipt,
    GenerationManifest,
    ModelManifest,
    Partition,
    ProtocolInfo,
    RunResult,
    SubstrateManifest,
    TaskManifest,
)


class ReceiptWriter:
    """Constructs, validates, hashes, and persists experiment receipts."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.receipts_dir = os.path.join(project_root, "ledger", "receipts")

    def write_run(
        self,
        *,
        cell: ExperimentCell,
        partition: Partition,
        model: ModelManifest,
        generation: GenerationManifest,
        tasks: TaskManifest,
        result: RunResult,
        protocol: ProtocolInfo,
        substrate: Optional[SubstrateManifest] = None,
        hypothesis: str = "",
        code_diff_hash: str = "",
        budget_consumed: Optional[Dict[str, float]] = None,
    ) -> ExperimentReceipt:
        run_id = f"{cell.value}-{partition.value}-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()
        protocol.hypothesis = hypothesis or protocol.hypothesis
        protocol.code_diff_hash = code_diff_hash or protocol.code_diff_hash

        receipt = ExperimentReceipt(
            run_id=run_id,
            cell=cell,
            partition=partition,
            created_at=created_at,
            model=model,
            generation=generation,
            tasks=tasks,
            substrate=substrate,
            result=result,
            protocol=protocol,
            budget_consumed=budget_consumed or {},
        )
        receipt.finalize()
        return self.persist(receipt)

    def persist(self, receipt: ExperimentReceipt) -> ExperimentReceipt:
        """Validate and atomically persist a pre-built receipt.

        A failed validation writes no authoritative receipt. Callers should treat the
        exception as a failed experiment-recording step and must not silently fall
        back to a legacy result as confirmation evidence.
        """
        errors = receipt.validate() + self._evidence_binding_errors(receipt)
        if errors:
            raise ValueError(
                f"Receipt validation failed for {receipt.run_id}:\n" +
                "\n".join(f"  - {error}" for error in errors)
            )

        os.makedirs(self.receipts_dir, exist_ok=True)
        final_path = os.path.join(
            self.receipts_dir,
            f"{receipt.created_at[:10]}_{receipt.run_id}.json",
        )
        tmp_path = final_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(asdict(receipt), f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, final_path)
        return receipt

    @staticmethod
    def _evidence_binding_errors(receipt: ExperimentReceipt) -> list[str]:
        errors: list[str] = []

        if receipt.tasks.partition != receipt.partition:
            errors.append("task partition does not match receipt partition")
        if receipt.tasks.n_tasks != len(receipt.tasks.task_ids):
            errors.append("TaskManifest.n_tasks does not match task_ids length")
        if not receipt.tasks.content_hash:
            errors.append("tasks.content_hash is required")
        if not receipt.result.result_hash:
            errors.append("result.result_hash is required")
        if not receipt.result.raw_output_hash:
            errors.append("result.raw_output_hash is required")
        if not receipt.protocol.hypothesis:
            errors.append("protocol.hypothesis is required")
        if receipt.generation.seed is None:
            errors.append("generation.seed is required")
        if not receipt.model.applied_template:
            errors.append("model.applied_template must bind the adapter used")
        if not receipt.budget_consumed:
            errors.append("budget_consumed is required")

        metrics = receipt.result.metrics
        if metrics.n_total <= 0:
            errors.append("metrics.n_total must be > 0")
        else:
            expected_rate = metrics.n_passed / metrics.n_total
            if abs(metrics.pass_rate - expected_rate) > 1e-6:
                errors.append(
                    f"metrics.pass_rate={metrics.pass_rate} does not equal "
                    f"n_passed/n_total={expected_rate}"
                )

        # Confirmation evidence has stricter provenance requirements than DEV.
        if receipt.partition in (Partition.REPLICATION, Partition.LOCKBOX):
            if not receipt.model.weights_hash:
                errors.append("confirmatory receipt requires model.weights_hash")
            if not receipt.model.tokenizer_hash:
                errors.append("confirmatory receipt requires model.tokenizer_hash")
            if not receipt.protocol.preregistration_hash:
                errors.append("confirmatory receipt requires protocol.preregistration_hash")
            if not receipt.protocol.amendment_log_hash:
                errors.append("confirmatory receipt requires protocol.amendment_log_hash")
            if not receipt.protocol.code_diff_hash:
                errors.append("confirmatory receipt requires protocol.code_diff_hash")

        return errors

    @staticmethod
    def verify_receipt_hash(receipt: ExperimentReceipt) -> Tuple[bool, str]:
        if not receipt.receipt_hash:
            return False, "receipt_hash is empty"
        if not receipt.verify_hash():
            return False, (
                f"hash mismatch: stored={receipt.receipt_hash[:16]}... "
                f"expected={receipt._compute_hash()[:16]}..."
            )
        return True, ""

    @staticmethod
    def verify_artifact_hash(
        artifact_path: str,
        claimed_hash: str,
        label: str = "artifact",
    ) -> Tuple[bool, str]:
        if not claimed_hash:
            return False, f"{label} has no claimed hash"
        if not os.path.exists(artifact_path):
            return False, f"{label} not found at {artifact_path}"
        h = hashlib.sha256()
        with open(artifact_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        actual = h.hexdigest()
        if actual != claimed_hash:
            return False, (
                f"{label} hash mismatch: "
                f"claimed={claimed_hash[:16]}... actual={actual[:16]}..."
            )
        return True, ""
