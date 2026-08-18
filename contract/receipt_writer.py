"""
Receipt Writer — the sole mechanism for recording experiment runs.

Research Contract §2, §3.4: No research runner should write receipt files
directly. All runs go through ReceiptWriter, which:
1. Constructs a properly hashed ExperimentReceipt
2. Verifies artifact hashes where available
3. Saves to ledger/receipts/ with cryptographic integrity
4. Returns the receipt for further use

The research agent cannot modify this writer — it is in the contract/
package which is read-only to the researcher in production.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from contract.schema import (
    ExperimentCell, ExperimentReceipt, GenerationManifest, ModelManifest,
    Partition, ProtocolInfo, RunMetrics, RunResult, SubstrateManifest,
    TaskManifest,
)


class ReceiptWriter:
    """Constructs and persists cryptographically hashed experiment receipts."""

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
        """
        Construct, hash, persist, and return a receipt.

        This is the ONLY sanctioned way to record an experiment run.
        """
        run_id = f"{cell.value}-{partition.value}-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()

        # Set hypothesis and code_diff_hash on protocol
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

        # Finalize: compute cryptographic hash
        receipt.finalize()

        # Validate before persisting
        errors = receipt.validate()
        if errors:
            raise ValueError(
                f"Receipt validation failed for {run_id}:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        # Save
        os.makedirs(self.receipts_dir, exist_ok=True)
        path = os.path.join(
            self.receipts_dir,
            f"{created_at[:10]}_{run_id}.json",
        )
        with open(path, "w") as f:
            json.dump(asdict(receipt), f, indent=2, default=str)

        return receipt

    @staticmethod
    def verify_receipt_hash(receipt: ExperimentReceipt) -> Tuple[bool, str]:
        """
        Static: verify that a receipt's hash matches its recomputed hash.
        Returns (True, "") or (False, reason).
        """
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
        """
        Verify a file's SHA-256 hash matches the claimed value.
        Returns (True, "") or (False, reason).
        """
        if not claimed_hash:
            return True, ""  # No hash claimed — skip (may not be available)
        if not os.path.exists(artifact_path):
            return False, f"{label} not found at {artifact_path}"
        with open(artifact_path, "rb") as f:
            actual = hashlib.sha256(f.read()).hexdigest()[:32]
        if actual != claimed_hash:
            return False, (
                f"{label} hash mismatch: "
                f"claimed={claimed_hash[:16]}... actual={actual[:16]}..."
            )
        return True, ""