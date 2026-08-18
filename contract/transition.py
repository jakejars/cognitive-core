"""State-transition authority for Research Contract v2.2.

Transition records are integrity-hashed and stored separately from experiment
receipts. Authenticity still depends on the external/read-only supervisor trust
boundary described in SUPERVISOR.md.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from contract.evidence import hash_json
from contract.hardening import (
    ContractViolation,
    check_amendment_record,
    check_budget_overrun,
    check_chat_template_parity,
    check_compensation_hypothesis,
    check_experiment_matrix,
    check_lockbox_intact,
    check_lockbox_pass,
    check_model_config_parity,
    check_phase_constants,
    check_phase_d_gate,
)
from contract.schema import EvidenceManifest, Partition, PhaseState, VALID_TRANSITIONS


@dataclass
class TransitionRequest:
    entity_type: str
    entity_id: str
    from_state: PhaseState
    to_state: PhaseState
    evidence: EvidenceManifest
    reason: str = ""
    requested_at: str = ""


@dataclass
class TransitionResult:
    accepted: bool
    receipt_id: str = ""
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    new_receipt_path: str = ""

    @property
    def rejected(self) -> bool:
        return not self.accepted


class ClaimTransitioner:
    """Central state-transition authority. Only this may promote status."""

    def __init__(self, project_root: str = None):
        if project_root is None:
            from contract.invariants import _root
            project_root = _root()
        self.project_root = project_root
        self.ledger_dir = os.path.join(project_root, "ledger")
        self.transitions_dir = os.path.join(self.ledger_dir, "transitions")
        os.makedirs(self.transitions_dir, exist_ok=True)

    def request_transition(self, req: TransitionRequest) -> TransitionResult:
        violations: list[str] = []
        warnings: list[str] = []

        actual_state = self.get_entity_state(req.entity_type, req.entity_id)
        if actual_state != req.from_state:
            violations.append(
                f"Entity {req.entity_type}/{req.entity_id} is in state {actual_state.value}, "
                f"but transition requests from {req.from_state.value}."
            )

        allowed = VALID_TRANSITIONS.get(req.from_state, set())
        if req.to_state not in allowed:
            violations.append(
                f"Transition {req.from_state.value} → {req.to_state.value} is not in the allowed transition matrix."
            )

        for receipt in req.evidence.experiment_receipts:
            errors = receipt.validate()
            if errors:
                violations.extend(f"Receipt {receipt.run_id}: {error}" for error in errors)

        def run_check(fn, *args, **kwargs):
            try:
                fn(*args, **kwargs)
            except ContractViolation as exc:
                violations.append(str(exc))

        if req.to_state == PhaseState.SUPPORTED_CLAIM:
            run_check(check_experiment_matrix, self.project_root, require_tier=Partition.DEV)
            run_check(check_experiment_matrix, self.project_root, require_tier=Partition.REPLICATION)
            run_check(check_experiment_matrix, self.project_root, require_tier=Partition.LOCKBOX)
            run_check(check_lockbox_intact, self.project_root)
            run_check(check_lockbox_pass, self.project_root)
            run_check(check_chat_template_parity, self.project_root)
            run_check(check_phase_constants, self.project_root)
            run_check(check_compensation_hypothesis, self.project_root)
            run_check(check_amendment_record, self.project_root)
            run_check(check_budget_overrun, self.project_root)
            run_check(check_model_config_parity, self.project_root)

        if req.to_state == PhaseState.LOCKBOX_PASS:
            run_check(check_lockbox_intact, self.project_root)
            run_check(check_lockbox_pass, self.project_root)
            run_check(check_experiment_matrix, self.project_root, require_tier=Partition.LOCKBOX)
            run_check(check_model_config_parity, self.project_root)

        if req.to_state == PhaseState.REPLICATED:
            run_check(check_experiment_matrix, self.project_root, require_tier=Partition.REPLICATION)
            run_check(check_model_config_parity, self.project_root)

        if req.to_state == PhaseState.DEV_PASS:
            run_check(check_experiment_matrix, self.project_root, require_tier=Partition.DEV)
            run_check(check_chat_template_parity, self.project_root)
            run_check(check_model_config_parity, self.project_root)

        if req.to_state == PhaseState.PHASE_GATE_PASS:
            run_check(check_experiment_matrix, self.project_root)
            run_check(check_chat_template_parity, self.project_root)
            run_check(check_phase_constants, self.project_root)
            run_check(check_amendment_record, self.project_root)
            run_check(check_budget_overrun, self.project_root)
            run_check(check_model_config_parity, self.project_root)

        if req.entity_type == "phase":
            phase_id = req.entity_id.lower()
            if phase_id in {"phase-d", "d", "procedural"} or "procedural" in phase_id:
                if req.to_state in (PhaseState.PHASE_GATE_PASS, PhaseState.SUPPORTED_CLAIM):
                    run_check(check_phase_d_gate, self.project_root)

        if violations:
            return TransitionResult(False, violations=violations, warnings=warnings)

        receipt_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        record = {
            "receipt_id": receipt_id,
            "entity_type": req.entity_type,
            "entity_id": req.entity_id,
            "from_state": req.from_state.value,
            "to_state": req.to_state.value,
            "reason": req.reason,
            "evidence_summary": self._summarize_evidence(req.evidence),
            "committed_at": timestamp,
        }
        record["record_hash"] = hash_json(record)

        path = os.path.join(
            self.transitions_dir,
            f"{timestamp[:10]}_{req.entity_id}_{req.to_state.value}_{receipt_id[:8]}.json",
        )
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(record, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

        return TransitionResult(
            True,
            receipt_id=receipt_id,
            new_receipt_path=path,
            warnings=warnings,
        )

    def _summarize_evidence(self, evidence: EvidenceManifest) -> dict:
        return {
            "n_receipts": len(evidence.experiment_receipts),
            "has_counterfactual": evidence.counterfactual_results is not None,
            "has_phase_constants": evidence.phase_constants is not None,
            "has_compensation_hypothesis": evidence.compensation_hypothesis is not None,
            "preregistration_hash": evidence.preregistration_hash[:16] if evidence.preregistration_hash else "",
        }

    def get_entity_state(self, entity_type: str, entity_id: str) -> PhaseState:
        if not os.path.isdir(self.transitions_dir):
            return PhaseState.UNIMPLEMENTED
        current = PhaseState.UNIMPLEMENTED
        for filename in sorted(os.listdir(self.transitions_dir)):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.transitions_dir, filename)) as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            stored_hash = data.pop("record_hash", "")
            if not stored_hash or stored_hash != hash_json(data):
                continue
            if data.get("entity_type") == entity_type and data.get("entity_id") == entity_id:
                try:
                    current = PhaseState(data["to_state"])
                except (KeyError, ValueError):
                    continue
        return current


def request_claim(claim_id: str, evidence: EvidenceManifest, project_root: str = None, reason: str = "") -> TransitionResult:
    transitioner = ClaimTransitioner(project_root)
    current = transitioner.get_entity_state("claim", claim_id)
    return transitioner.request_transition(
        TransitionRequest("claim", claim_id, current, PhaseState.SUPPORTED_CLAIM, evidence, reason)
    )


def request_phase_gate(phase_id: str, evidence: EvidenceManifest, project_root: str = None, reason: str = "") -> TransitionResult:
    transitioner = ClaimTransitioner(project_root)
    current = transitioner.get_entity_state("phase", phase_id)
    return transitioner.request_transition(
        TransitionRequest("phase", phase_id, current, PhaseState.PHASE_GATE_PASS, evidence, reason)
    )
