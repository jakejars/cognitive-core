"""
Cognitive Core — Research Contract v2.2
Executable protocol enforcement package.

This is the sole authoritative protocol package. The harness imports it, not vice versa.
"""

from contract.schema import (
    ExperimentCell, Partition, PhaseState,
    ExperimentReceipt, ModelManifest, GenerationManifest,
    TaskManifest, SubstrateManifest, RunMetrics, RunResult,
    PhaseConstants, CompensationHypothesis, AmendmentRecord,
    LockboxEntry, LockboxLedger, EvidenceManifest,
    receipt_from_dict,
)
from contract.invariants import (
    ContractViolation,
    check_experiment_matrix, check_lockbox_intact, check_lockbox_pass,
    check_chat_template_parity, check_phase_d_gate,
    check_phase_constants, check_compensation_hypothesis,
    check_amendment_record, check_budget_overrun, check_model_config_parity,
)
from contract.transition import (
    ClaimTransitioner, TransitionRequest, TransitionResult,
    request_claim, request_phase_gate,
)
from contract.receipt_writer import (
    ReceiptWriter,
)

__all__ = [
    # Schema
    "ExperimentCell", "Partition", "PhaseState",
    "ExperimentReceipt", "ModelManifest", "GenerationManifest",
    "TaskManifest", "SubstrateManifest", "RunMetrics", "RunResult",
    "PhaseConstants", "CompensationHypothesis", "AmendmentRecord",
    "LockboxEntry", "LockboxLedger", "EvidenceManifest",
    "receipt_from_dict",
    # Invariants
    "ContractViolation",
    "check_experiment_matrix", "check_lockbox_intact", "check_lockbox_pass",
    "check_chat_template_parity", "check_phase_d_gate",
    "check_phase_constants", "check_compensation_hypothesis",
    "check_amendment_record", "check_budget_overrun", "check_model_config_parity",
    # Transitions
    "ClaimTransitioner", "TransitionRequest", "TransitionResult",
    "request_claim", "request_phase_gate",
    # Receipt Writer
    "ReceiptWriter",
]