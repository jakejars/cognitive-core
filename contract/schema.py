"""
Contract schema — data models for the Cognitive Core Research Contract v2.2.

These are the canonical types used by all invariant checks and the state-transition API.
No experiment/phase/claim status should be written except through this schema.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, fields, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ── Experiment Cell Identities ─────────────────────────────────────────────

class ExperimentCell(str, Enum):
    """Cells of the 2×2 factorial baseline (Contract §2)."""
    B1 = "B1"   # MiniCPM5-1B — vanilla
    B2 = "B2"   # Qwen3.5-4B — vanilla
    S1 = "S1"   # MiniCPM5-1B + Substrate
    S2 = "S2"   # Qwen3.5-4B + Substrate
    B3 = "B3"   # Optional: ~8B vanilla
    S3 = "S3"   # Optional: ~8B + Substrate


class Partition(str, Enum):
    """Protected evaluation tier (Contract §3.1)."""
    DEV = "dev"
    REPLICATION = "replication"
    LOCKBOX = "lockbox"


# ── Phase States — machine-readable, never inferred from execution ──────────

class PhaseState(str, Enum):
    """Explicit phase states. A script returning exit code 0 means RUN, not VALIDATED."""
    UNIMPLEMENTED = "UNIMPLEMENTED"
    IMPLEMENTED = "IMPLEMENTED"
    RUN = "RUN"
    DEV_PASS = "DEV_PASS"
    REPLICATED = "REPLICATED"
    LOCKBOX_PASS = "LOCKBOX_PASS"
    PHASE_GATE_PASS = "PHASE_GATE_PASS"
    SUPPORTED_CLAIM = "SUPPORTED_CLAIM"
    WITHDRAWN = "WITHDRAWN"


# ── Phase-A Frozen Constants (Contract §3.2) ──────────────────────────────

@dataclass
class PhaseConstants:
    """Frozen at Phase-A exit, before any substrate evaluation (Contract §3.2)."""
    C_success: float      # S1 task success >= C_success × S2 task success
    C_memory: float       # S1 model-resident memory <= C_memory × S2
    C_latency: float      # Substrate p95 latency overhead ratio
    C_trust: float        # Effect/provenance/state error rate ratio
    frozen_at: str = ""   # ISO timestamp
    calibration_basis: str = ""  # Which experiment established these values

    def validate(self) -> List[str]:
        errors = []
        if not (0 < self.C_success <= 1.5):
            errors.append(f"C_success={self.C_success} outside reasonable range (0, 1.5]")
        if not (0 < self.C_memory <= 2.0):
            errors.append(f"C_memory={self.C_memory} outside reasonable range (0, 2.0]")
        if not (0 <= self.C_latency <= 5.0):
            errors.append(f"C_latency={self.C_latency} outside reasonable range [0, 5.0]")
        if not (0 <= self.C_trust <= 5.0):
            errors.append(f"C_trust={self.C_trust} outside reasonable range [0, 5.0]")
        return errors


# ── Compensation Hypothesis (Contract §3.3) ───────────────────────────────

@dataclass
class CompensationHypothesis:
    """Pre-registered when B2 dominates B1 (Contract §3.3)."""
    hypothesis: str
    expected_compensation_metric: str
    expected_improvement_pct: float
    success_retention_threshold_pct: float
    preregistered_at: str = ""
    preregistration_hash: str = ""

    def hash(self) -> str:
        return hashlib.sha256(self.hypothesis.encode()).hexdigest()[:16]


# ── Model Configuration Manifest (Contract §3.4) ──────────────────────────

@dataclass
class ModelManifest:
    """Immutable record of a model's identity and configuration for a run."""
    model_id: str
    revision: str
    weights_hash: str
    tokenizer_id: str
    tokenizer_hash: str
    template_adapter_version: str  # e.g. "minicpm_v1", "qwen_apply_chat_template_v1"
    applied_template: str  # The actual template string or adapter name used


@dataclass
class GenerationManifest:
    """Runtime generation configuration, frozen per run (Contract §3.4)."""
    thinking_mode: bool
    max_total_tokens: int
    max_answer_tokens: int
    temperature: float
    top_p: float
    stop_policy: str  # e.g. "eos_only", "stop_strings", "eos_plus_stops"
    stop_tokens: List[int] = field(default_factory=list)


# ── Substrate Configuration (for S1, S2 runs) ────────────────────────────

@dataclass
class SubstrateManifest:
    revision: str
    config_hash: str
    modules: List[str] = field(default_factory=list)


# ── Task Manifest ──────────────────────────────────────────────────────────

@dataclass
class TaskManifest:
    """Describes which tasks were used in a run."""
    source: str           # e.g. "gauntlets/gauntlet_tasks.py"
    partition: Partition
    task_ids: List[str]
    content_hash: str     # SHA-256 of concatenated task prompts + expected outputs
    n_tasks: int
    n_turns: int = 0


# ── Run Result ─────────────────────────────────────────────────────────────

@dataclass
class RunMetrics:
    n_passed: int
    n_total: int
    pass_rate: float
    mean_score: float
    mean_latency_ms: float
    total_time_s: float

    # Axis 2: systems efficiency (Contract §5, Axis 2)
    model_resident_memory_gb: Optional[float] = None
    successful_tasks_per_gb: Optional[float] = None
    successful_tasks_per_second: Optional[float] = None

    # Axis 3: trustworthy stateful (Contract §5, Axis 3)
    effect_duplication_rate: Optional[float] = None
    provenance_error_rate: Optional[float] = None


@dataclass
class RunResult:
    result_hash: str
    completed_at: str
    metrics: RunMetrics
    raw_output_hash: str = ""


# ── Protocol Information ───────────────────────────────────────────────────

@dataclass
class ProtocolInfo:
    contract_version: str
    preregistration_hash: str  # Hash of the pre-registered plan
    amendment_log_hash: str    # Hash of amendments that apply


# ── Complete Experiment Receipt ────────────────────────────────────────────

@dataclass
class ExperimentReceipt:
    """
    Single immutable record of one experiment run.

    A cell (B1/B2/S1/S2) EXISTS only if a validated receipt exists for it.
    File existence does not constitute an experiment.
    """
    run_id: str
    cell: ExperimentCell
    partition: Partition
    created_at: str

    model: ModelManifest
    generation: GenerationManifest
    tasks: TaskManifest
    substrate: Optional[SubstrateManifest]  # None for B1/B2

    result: RunResult
    protocol: ProtocolInfo

    receipt_hash: str = ""  # Self-hash after construction

    def finalize(self) -> str:
        """Compute and store the receipt hash."""
        self.receipt_hash = self._compute_hash()
        return self.receipt_hash

    def _compute_hash(self) -> str:
        d = asdict(self)
        d.pop("receipt_hash", None)
        canonical = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    def validate(self) -> List[str]:
        """Structural validation — does the receipt make sense?"""
        errors = []
        if not self.run_id:
            errors.append("run_id is required")
        if not self.receipt_hash:
            errors.append("receipt not finalized (call finalize())")
        if self.cell in (ExperimentCell.S1, ExperimentCell.S2) and self.substrate is None:
            errors.append(f"{self.cell.value} requires substrate manifest")
        if self.result.metrics.n_total == 0:
            errors.append("n_total must be > 0")
        return errors


# ── Lockbox Exposure Ledger (Contract §3.1) ───────────────────────────────

@dataclass
class LockboxEntry:
    """Tracks exposure of a single protected task/lockbox item."""
    content_hash: str
    partition: Partition
    created_at: str
    frozen_at: str         # When it was frozen for lockbox use
    first_exposed_at: Optional[str] = None  # When first read by researcher/evaluator
    first_evaluated_at: Optional[str] = None  # When first evaluated by a model
    evaluation_count: int = 0
    exposure_history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class LockboxLedger:
    """Complete ledger of all lockbox and protected items."""
    entries: Dict[str, LockboxEntry] = field(default_factory=dict)

    def is_valid_lockbox(self, content_hash: str) -> bool:
        """A lockbox item is valid iff:
        1. Content hash matches frozen manifest
        2. No prior DEV/REPLICATION/training/retrieval/skill-mining exposure
        3. Evaluation count is within allowed limits
        """
        entry = self.entries.get(content_hash)
        if not entry:
            return False
        if entry.partition != Partition.LOCKBOX:
            return False
        if entry.first_exposed_at is not None and entry.evaluation_count == 0:
            return False  # Exposed but never evaluated — possible leak
        if entry.evaluation_count > 1:
            return False  # Lockbox items should be evaluated exactly once (or 0 if never used)
        return True


# ── Phase Budgets (Contract §4) ───────────────────────────────────────────

@dataclass
class PhaseBudget:
    phase: str
    max_wall_clock_days: int
    max_researcher_days: int
    max_compute_hours: int
    max_material_experiments: int
    entry_gate: str
    exit_gate: str
    current_wall_clock_days: float = 0
    current_experiments: int = 0
    current_compute_hours: float = 0

    def overrun_level(self) -> float:
        """Return current/max ratio. >= 1.0 means overrun."""
        ratios = []
        if self.max_wall_clock_days:
            ratios.append(self.current_wall_clock_days / self.max_wall_clock_days)
        if self.max_compute_hours:
            ratios.append(self.current_compute_hours / self.max_compute_hours)
        if self.max_material_experiments:
            ratios.append(self.current_experiments / self.max_material_experiments)
        return max(ratios) if ratios else 0.0


# ── Phase State Machine ────────────────────────────────────────────────────

# Valid transitions between phase states
VALID_TRANSITIONS: Dict[PhaseState, Set[PhaseState]] = {
    PhaseState.UNIMPLEMENTED: {PhaseState.IMPLEMENTED},
    PhaseState.IMPLEMENTED: {PhaseState.RUN, PhaseState.WITHDRAWN},
    PhaseState.RUN: {PhaseState.DEV_PASS, PhaseState.WITHDRAWN},
    PhaseState.DEV_PASS: {PhaseState.REPLICATED, PhaseState.WITHDRAWN},
    PhaseState.REPLICATED: {PhaseState.LOCKBOX_PASS, PhaseState.WITHDRAWN},
    PhaseState.LOCKBOX_PASS: {PhaseState.PHASE_GATE_PASS, PhaseState.WITHDRAWN},
    PhaseState.PHASE_GATE_PASS: {PhaseState.SUPPORTED_CLAIM, PhaseState.WITHDRAWN},
    PhaseState.SUPPORTED_CLAIM: {PhaseState.WITHDRAWN},
    PhaseState.WITHDRAWN: set(),
}


# ── Evidence Manifest ─────────────────────────────────────────────────────

@dataclass
class EvidenceManifest:
    """Evidence submitted for a state transition."""
    experiment_receipts: List[ExperimentReceipt] = field(default_factory=list)
    counterfactual_results: Optional[Dict[str, Any]] = None
    preregistration_hash: str = ""
    phase_constants: Optional[PhaseConstants] = None
    compensation_hypothesis: Optional[CompensationHypothesis] = None
    amendment_log_hash: str = ""


# ── Amendment Record (Contract §11) ───────────────────────────────────────

@dataclass
class AmendmentRecord:
    date: str
    reason: str
    observed_results: str
    affected_metrics: str
    invalidated_evidence: bool
    new_evaluation_source: str = ""
    amendment_hash: str = ""

    def finalize(self) -> str:
        d = asdict(self)
        d.pop("amendment_hash", None)
        canonical = json.dumps(d, sort_keys=True, default=str)
        self.amendment_hash = hashlib.sha256(canonical.encode()).hexdigest()[:32]
        return self.amendment_hash


# ── Serialization Helpers ─────────────────────────────────────────────────

def receipt_from_dict(d: dict) -> ExperimentReceipt:
    """Build an ExperimentReceipt from a dict (e.g. loaded from JSON)."""
    return ExperimentReceipt(
        run_id=d["run_id"],
        cell=ExperimentCell(d["cell"]),
        partition=Partition(d["partition"]),
        created_at=d["created_at"],
        model=ModelManifest(**d["model"]),
        generation=GenerationManifest(**d["generation"]),
        tasks=TaskManifest(
            source=d["tasks"]["source"],
            partition=Partition(d["tasks"]["partition"]),
            task_ids=d["tasks"]["task_ids"],
            content_hash=d["tasks"]["content_hash"],
            n_tasks=d["tasks"]["n_tasks"],
            n_turns=d["tasks"].get("n_turns", 0),
        ),
        substrate=SubstrateManifest(**d["substrate"]) if d.get("substrate") else None,
        result=RunResult(
            result_hash=d["result"]["result_hash"],
            completed_at=d["result"]["completed_at"],
            metrics=RunMetrics(**d["result"]["metrics"]),
            raw_output_hash=d["result"].get("raw_output_hash", ""),
        ),
        protocol=ProtocolInfo(**d["protocol"]),
        receipt_hash=d.get("receipt_hash", ""),
    )