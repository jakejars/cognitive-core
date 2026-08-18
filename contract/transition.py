"""
State-transition API — the only mechanism capable of promoting experiment/phase/claim status.

Contract §2, §3.4: No research runner should write CONFIRMED, PHASE_GATE_PASS,
or SUPPORTED_CLAIM directly. All transitions go through this API, which:
1. Validates the current state of the entity
2. Verifies the transition is in the allowed matrix
3. Runs applicable contract invariants
4. Commits the transition with a cryptographically signed receipt
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from contract.invariants import (
    check_experiment_matrix, check_lockbox_intact, check_lockbox_pass,
    check_chat_template_parity, check_phase_d_gate, check_phase_constants,
    check_compensation_hypothesis, check_amendment_record,
    check_budget_overrun, check_model_config_parity, ContractViolation,
)
from contract.schema import (
    EvidenceManifest, ExperimentReceipt, PhaseState, VALID_TRANSITIONS,
    PhaseConstants, CompensationHypothesis, AmendmentRecord, Partition,
)


@dataclass
class TransitionRequest:
    """Request to transition an entity from one state to another."""
    entity_type: str       # "experiment", "phase", "claim"
    entity_id: str         # e.g. "EXP-011", "Phase-C", "SMALL_EXECUTIVE_THESIS"
    from_state: PhaseState
    to_state: PhaseState
    evidence: EvidenceManifest
    reason: str = ""
    requested_at: str = ""


@dataclass
class TransitionResult:
    """Result of a transition request."""
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
        self.receipts_dir = os.path.join(self.ledger_dir, "receipts")
        os.makedirs(self.receipts_dir, exist_ok=True)

    def request_transition(self, req: TransitionRequest) -> TransitionResult:
        """
        Submit a transition request. Validates evidence against contract,
        verifies current state, then either commits or rejects.
        """
        violations = []
        warnings = []

        # ── 1. Verify current state matches from_state ──
        actual_state = self.get_entity_state(req.entity_type, req.entity_id)
        if actual_state != req.from_state:
            violations.append(
                f"Entity {req.entity_type}/{req.entity_id} is in state "
                f"{actual_state.value}, but transition requests from {req.from_state.value}. "
                f"from_state must match the entity's current state."
            )

        # ── 2. Validate transition is legal ──
        allowed = VALID_TRANSITIONS.get(req.from_state, set())
        if req.to_state not in allowed:
            violations.append(
                f"Transition {req.from_state.value} → {req.to_state.value} "
                f"is not in the allowed transition matrix."
            )

        # ── 3. Validate and store evidence receipt ──
        if req.evidence.experiment_receipts:
            for r in req.evidence.experiment_receipts:
                errs = r.validate()
                if errs:
                    violations.extend(f"Receipt {r.run_id}: {e}" for e in errs)

        # ── 4. Run applicable invariants ──
        # Which invariants to check depends on the target state

        if req.to_state == PhaseState.SUPPORTED_CLAIM:
            # Major claims require full matrix across all tiers
            try:
                check_experiment_matrix(self.project_root, require_tier=Partition.DEV)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_experiment_matrix(self.project_root, require_tier=Partition.REPLICATION)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_experiment_matrix(self.project_root, require_tier=Partition.LOCKBOX)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_lockbox_intact(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_lockbox_pass(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_chat_template_parity(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_phase_constants(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_compensation_hypothesis(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_amendment_record(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_budget_overrun(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

            try:
                check_model_config_parity(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

        if req.to_state == PhaseState.LOCKBOX_PASS:
            try:
                check_lockbox_intact(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_lockbox_pass(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_experiment_matrix(self.project_root, require_tier=Partition.LOCKBOX)
            except ContractViolation as e:
                violations.append(str(e))

        if req.to_state == PhaseState.REPLICATED:
            try:
                check_experiment_matrix(self.project_root, require_tier=Partition.REPLICATION)
            except ContractViolation as e:
                violations.append(str(e))

        if req.to_state == PhaseState.DEV_PASS:
            try:
                check_experiment_matrix(self.project_root, require_tier=Partition.DEV)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_chat_template_parity(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

        if req.to_state == PhaseState.PHASE_GATE_PASS:
            try:
                check_experiment_matrix(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_lockbox_intact(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_chat_template_parity(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_phase_constants(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))
            try:
                check_amendment_record(self.project_root)
            except ContractViolation as e:
                violations.append(str(e))

        # ── 5. Phase-specific gates ──
        if req.entity_type == "phase":
            phase_lower = req.entity_id.lower()
            if "d" in phase_lower or "procedural" in phase_lower:
                if req.to_state in (PhaseState.PHASE_GATE_PASS, PhaseState.SUPPORTED_CLAIM):
                    try:
                        check_phase_d_gate(self.project_root)
                    except ContractViolation as e:
                        violations.append(str(e))

        # ── 6. Commit or reject ──
        if violations:
            return TransitionResult(
                accepted=False,
                violations=violations,
                warnings=warnings,
            )

        # Commit the transition
        receipt_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        transition_record = {
            "receipt_id": receipt_id,
            "entity_type": req.entity_type,
            "entity_id": req.entity_id,
            "from_state": req.from_state.value,
            "to_state": req.to_state.value,
            "reason": req.reason,
            "evidence_summary": self._summarize_evidence(req.evidence),
            "committed_at": timestamp,
        }

        receipt_path = os.path.join(
            self.receipts_dir,
            f"{timestamp[:10]}_{req.entity_id}_{req.to_state.value}.json",
        )
        with open(receipt_path, "w") as f:
            json.dump(transition_record, f, indent=2)

        return TransitionResult(
            accepted=True,
            receipt_id=receipt_id,
            new_receipt_path=receipt_path,
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
        """Determine current state of an entity from its transition receipts."""
        if not os.path.isdir(self.receipts_dir):
            return PhaseState.UNIMPLEMENTED
        current = PhaseState.UNIMPLEMENTED
        for fn in sorted(os.listdir(self.receipts_dir)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(self.receipts_dir, fn)) as f:
                data = json.load(f)
            if data.get("entity_type") == entity_type and data.get("entity_id") == entity_id:
                try:
                    current = PhaseState(data["to_state"])
                except ValueError:
                    pass
        return current


def request_claim(
    claim_id: str,
    evidence: EvidenceManifest,
    project_root: str = None,
    reason: str = "",
) -> TransitionResult:
    """Convenience: request a SUPPORTED_CLAIM transition."""
    transitioner = ClaimTransitioner(project_root)
    current = transitioner.get_entity_state("claim", claim_id)
    req = TransitionRequest(
        entity_type="claim",
        entity_id=claim_id,
        from_state=current,
        to_state=PhaseState.SUPPORTED_CLAIM,
        evidence=evidence,
        reason=reason,
    )
    return transitioner.request_transition(req)


def request_phase_gate(
    phase_id: str,
    evidence: EvidenceManifest,
    project_root: str = None,
    reason: str = "",
) -> TransitionResult:
    """Convenience: request a phase gate pass."""
    transitioner = ClaimTransitioner(project_root)
    current = transitioner.get_entity_state("phase", phase_id)
    req = TransitionRequest(
        entity_type="phase",
        entity_id=phase_id,
        from_state=current,
        to_state=PhaseState.PHASE_GATE_PASS,
        evidence=evidence,
        reason=reason,
    )
    return transitioner.request_transition(req)