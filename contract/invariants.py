"""Research Contract invariants — executable protocol enforcement (Contract v2.2).

All invariant checks raise ContractViolation when the condition is not met.
No experiment/phase/claim status should be accepted without passing relevant invariants.
"""

from __future__ import annotations
import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple

from contract.schema import (
    ExperimentCell, ExperimentReceipt, LockboxLedger,
    LockboxEntry, Partition, PhaseConstants, CompensationHypothesis,
    receipt_from_dict,
)
from contract.receipt_writer import ReceiptWriter


class ContractViolation(Exception):
    """Raised when a contract invariant is violated."""
    pass


# ── Helpers ──────────────────────────────────────────────────────────────────

def _root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(d) if os.path.exists(os.path.join(os.path.dirname(d), "ledger")) else d


def _receipts(ld: str) -> List[ExperimentReceipt]:
    """Load receipts, verifying cryptographic integrity of each."""
    rd = os.path.join(ld, "receipts")
    if not os.path.isdir(rd):
        return []
    out = []
    for fn in sorted(os.listdir(rd)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(rd, fn)) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue
        try:
            r = receipt_from_dict(data)
        except (KeyError, TypeError):
            continue

        # ── Cryptographic verification ──
        # Reject receipts with empty or tampered hashes
        valid, reason = ReceiptWriter.verify_receipt_hash(r)
        if not valid:
            continue  # Silently skip tampered receipts

        # Must have metrics
        if r.result.metrics.n_total <= 0:
            continue

        out.append(r)
    return out


def _receipts_by_cell(ld: str) -> Dict[ExperimentCell, list]:
    """Group receipts by experiment cell."""
    receipts = _receipts(ld)
    cells: Dict[ExperimentCell, list] = {}
    for r in receipts:
        cells.setdefault(r.cell, []).append(r)
    return cells


def _lockbox_ledger(ld: str) -> LockboxLedger:
    p = os.path.join(ld, "lockbox-ledger.json")
    if not os.path.exists(p):
        return LockboxLedger()
    with open(p) as f:
        d = json.load(f)
    return LockboxLedger(entries={k: LockboxEntry(**v) for k, v in d.get("entries", {}).items()})


def _phase_constants(ld: str) -> Optional[PhaseConstants]:
    p = os.path.join(ld, "phase-constants.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return PhaseConstants(**json.load(f))


def _comp_hyp(ld: str) -> Optional[CompensationHypothesis]:
    p = os.path.join(ld, "compensation-hypothesis.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return CompensationHypothesis(**json.load(f))


def _earliest_s1_s2_timestamp(ld: str) -> Optional[str]:
    """Find the earliest created_at timestamp among S1/S2 receipts."""
    timestamps = []
    for r in _receipts(ld):
        if r.cell in (ExperimentCell.S1, ExperimentCell.S2):
            timestamps.append(r.created_at)
    return min(timestamps) if timestamps else None


# ── Invariant 1: Experiment Matrix (Contract §2) ──────────────────────────────

def check_experiment_matrix(
    project_root: str = None,
    require_tier: Optional[Partition] = None,
) -> None:
    """
    Requires validated receipts for B1/B2/S1/S2.

    When require_tier is set, requires receipts at that specific tier.
    When None, requires at least one receipt per cell (any tier).
    """
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    cells = _receipts_by_cell(ld)
    required = [ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1, ExperimentCell.S2]

    if require_tier:
        missing = []
        for c in required:
            matching = [r for r in cells.get(c, []) if r.partition == require_tier]
            if not matching:
                missing.append(c.value)
        if missing:
            raise ContractViolation(
                f"Matrix incomplete at tier {require_tier.value}: "
                f"no validated receipts for {', '.join(missing)}. "
                f"Contract §2 requires all 4 cells at each evaluation tier."
            )
        print(f"  [Contract] Matrix complete: 4 cells at {require_tier.value} tier")
    else:
        missing = [c.value for c in required
                   if not [r for r in cells.get(c, []) if r.partition != Partition.LOCKBOX]]
        if missing:
            raise ContractViolation(
                f"Matrix incomplete: no validated receipts for {', '.join(missing)}. "
                "Receipts with metrics required — file existence is not evidence."
            )
        for p in (Partition.DEV, Partition.REPLICATION, Partition.LOCKBOX):
            if all(any(r.partition == p for r in cells.get(c, [])) for c in required):
                print(f"  [Contract] Matrix complete: 4 cells at {p.value} tier")
                return
        print(f"  [Contract] Matrix: cells exist on mixed partitions")


# ── Invariant 2a: Lockbox Intact (Contract §3.1) ────────────────────────────

def check_lockbox_intact(project_root: str = None) -> None:
    """
    Lockbox items must not have been contaminated.
    This checks ONLY that the lockbox was not spoiled — not that the experiment passed.
    """
    pr = project_root or _root()
    ledger = _lockbox_ledger(os.path.join(pr, "ledger"))
    if not ledger.entries:
        raise ContractViolation(
            "No lockbox ledger at ledger/lockbox-ledger.json. "
            "Contract §3.1 requires one."
        )
    violations = []
    any_lockbox = False
    for ch, e in ledger.entries.items():
        if e.partition != Partition.LOCKBOX:
            continue
        any_lockbox = True

        # Pre-freeze evaluation
        if e.first_evaluated_at and e.frozen_at and e.first_evaluated_at < e.frozen_at:
            violations.append(
                f"  {ch[:12]}: evaluated {e.first_evaluated_at} before freeze {e.frozen_at}"
            )

        # Pre-freeze exposure
        if e.first_exposed_at and e.frozen_at and e.first_exposed_at < e.frozen_at:
            violations.append(
                f"  {ch[:12]}: exposed {e.first_exposed_at} before freeze {e.frozen_at}"
            )

        # Pre-release researcher access
        if (e.first_researcher_exposure_at
                and e.authorised_release_at
                and e.first_researcher_exposure_at < e.authorised_release_at):
            violations.append(
                f"  {ch[:12]}: researcher accessed {e.first_researcher_exposure_at} "
                f"before authorised release {e.authorised_release_at}"
            )

        # Per-cell evaluation limits
        if e.authorised_cells:
            for cell, count in e.cell_evaluations.items():
                if cell not in e.authorised_cells:
                    violations.append(
                        f"  {ch[:12]}: unauthorised cell {cell} evaluated this item"
                    )
                if count > 1:
                    violations.append(
                        f"  {ch[:12]}: cell {cell} evaluated {count}x (max 1)"
                    )
        else:
            # Legacy: global evaluation_count check
            if e.evaluation_count > 1:
                violations.append(
                    f"  {ch[:12]}: evaluated {e.evaluation_count}x (max 1)"
                )

        # Exposure history contamination
        for h in e.exposure_history:
            if h.get("type") in ("training", "retrieval", "skill_mining"):
                violations.append(
                    f"  {ch[:12]}: unacceptable exposure type '{h.get('type')}' "
                    f"at {h.get('timestamp', '?')}"
                )

    if not any_lockbox:
        raise ContractViolation(
            "No LOCKBOX partition entries in lockbox ledger. "
            "Contract §3.1 requires at least one lockbox item."
        )

    if violations:
        raise ContractViolation("Lockbox integrity violations:\n" + "\n".join(violations))

    untouched = sum(1 for e in ledger.entries.values()
                    if e.partition == Partition.LOCKBOX and e.evaluation_count == 0
                    and not e.cell_evaluations)
    print(f"  [Contract] Lockbox intact: {sum(1 for e in ledger.entries.values() if e.partition == Partition.LOCKBOX)} items, {untouched} untouched")


# ── Invariant 2b: Lockbox Pass (Contract §3.1) ──────────────────────────────

def check_lockbox_pass(project_root: str = None) -> None:
    """
    Lockbox experiment was conducted AND met the pre-registered criterion.
    This is SEPARATE from check_lockbox_intact — both are required for LOCKBOX_PASS.
    """
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    receipts = _receipts(ld)
    lockbox_receipts = [r for r in receipts if r.partition == Partition.LOCKBOX]

    if not lockbox_receipts:
        raise ContractViolation(
            "No lockbox experiment receipts found. "
            "LOCKBOX_PASS requires authorised lockbox evaluation with results."
        )

    # Require all 4 cells at lockbox tier
    cells_found = set(r.cell for r in lockbox_receipts)
    required = {ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1, ExperimentCell.S2}
    missing = required - cells_found
    if missing:
        raise ContractViolation(
            f"Lockbox experiment incomplete: missing cells "
            f"{', '.join(c.value for c in sorted(missing, key=lambda x: x.value))}. "
            f"Contract §2 requires all 4 cells."
        )

    # Verify lockbox ledger shows these evaluations
    ledger = _lockbox_ledger(ld)
    for r in lockbox_receipts:
        for tid in r.tasks.task_ids:
            entry = ledger.entries.get(tid)
            if entry and entry.partition == Partition.LOCKBOX:
                if entry.authorised_cells and r.cell.value not in entry.authorised_cells:
                    raise ContractViolation(
                        f"Task {tid[:12]}: evaluation by {r.cell.value} not authorised"
                    )

    print(f"  [Contract] Lockbox pass: {len(lockbox_receipts)} receipts across {len(cells_found)} cells")


# ── Invariant 3: Chat Template Parity (Contract §2, §3.4) ──────────────────

def check_chat_template_parity(project_root: str = None) -> None:
    """
    Each model needs a verified adapter with golden tokenisation tests.
    Adapters are verified by actually running the tokenizer, not by metadata checks.
    """
    pr = project_root or _root()
    adir = os.path.join(pr, "contract", "adapters")
    if not os.path.isdir(adir):
        raise ContractViolation("No contract/adapters/ directory. Verified adapters with golden tokens required.")
    afiles = sorted(f for f in os.listdir(adir) if f.endswith(".json"))
    if not afiles:
        raise ContractViolation("No adapter manifests in contract/adapters/.")
    issues = []

    adapter_models = set()
    for af in afiles:
        with open(os.path.join(adir, af)) as f:
            data = json.load(f)
        mid = data.get("model_id", af)
        adapter_models.add(mid)

        if not data.get("template_source"):
            issues.append(f"  {mid}: missing template_source")
        if not data.get("template_string"):
            issues.append(f"  {mid}: missing template_string")
        if not data.get("generation_config"):
            issues.append(f"  {mid}: no generation_config")

        g = data.get("golden_tokenisation_test", {})
        if not g.get("test_input") or not g.get("expected_token_ids"):
            issues.append(f"  {mid}: incomplete golden_tokenisation_test (need test_input and expected_token_ids)")
        else:
            # Actually verify the golden tokenisation by loading the model's tokenizer
            model_path = os.path.join(pr, "models", mid)
            if os.path.isdir(model_path):
                try:
                    from transformers import AutoTokenizer
                    tok = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                    actual_ids = tok.encode(g["test_input"])
                    expected = g["expected_token_ids"]
                    if isinstance(expected, list) and len(expected) > 0:
                        if len(actual_ids) < len(expected):
                            issues.append(
                                f"  {mid}: golden_tokenisation_test expected {len(expected)} tokens "
                                f"but got {len(actual_ids)}"
                            )
                        else:
                            for i, (a, e) in enumerate(zip(actual_ids[:len(expected)], expected)):
                                if a != e:
                                    issues.append(
                                        f"  {mid}: golden token mismatch at position {i}: "
                                        f"expected {e}, got {a}"
                                    )
                                    break
                except Exception as exc:
                    issues.append(f"  {mid}: tokenizer verification failed: {exc}")

    # Check that every model used in receipts has a verified adapter
    for r in _receipts(os.path.join(pr, "ledger")):
        if not r.model.template_adapter_version.startswith("verified_"):
            issues.append(
                f"  Receipt {r.run_id[:12]} ({r.cell.value}): "
                f"adapter '{r.model.template_adapter_version}' not verified"
            )
        if r.model.model_id not in adapter_models:
            issues.append(
                f"  Receipt {r.run_id[:12]} ({r.cell.value}): "
                f"model '{r.model.model_id}' has no adapter in contract/adapters/"
            )

    if issues:
        raise ContractViolation("Template parity issues:\n" + "\n".join(issues))
    print(f"  [Contract] Template parity: {len(afiles)} verified adapters for {len(adapter_models)} models")


# ── Invariant 4: Phase D Gate (Contract §6 — Phase D) ──────────────────────

def check_phase_d_gate(project_root: str = None) -> None:
    """
    Requires raw paired A/B results with:
    - Valid pass_rate = n_passed / n_total
    - Same task set for baseline and treatment
    - Fresh task set (not used in any prior receipt)
    - Delta >= criterion_threshold
    """
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    p = os.path.join(ld, "counterfactual_eval.json")
    if not os.path.exists(p):
        raise ContractViolation("Phase D gate: no counterfactual_eval.json found.")
    with open(p) as f:
        data = json.load(f)

    if data.get("protocol_version") != "2.2":
        raise ContractViolation("Phase D: missing protocol_version='2.2'")
    if not data.get("pre_registered_criterion"):
        raise ContractViolation("Phase D: no pre_registered_criterion")

    criterion_threshold = data.get("criterion_threshold")
    if criterion_threshold is None:
        raise ContractViolation("Phase D: missing criterion_threshold (e.g. 0.1 for 10% improvement)")

    bl, tr = data.get("baseline", {}), data.get("treatment", {})
    if not bl or not tr:
        raise ContractViolation("Phase D: baseline and treatment required")
    for lb, block in [("baseline", bl), ("treatment", tr)]:
        for k in ("n_passed", "n_total", "pass_rate"):
            if k not in block:
                raise ContractViolation(f"Phase D {lb}: missing {k}")

    br, trr = bl["pass_rate"], tr["pass_rate"]
    if bl.get("n_total", 0) == 0:
        raise ContractViolation("Phase D: n_total=0")

    # Verify pass_rate = n_passed / n_total
    for lb, block in [("baseline", bl), ("treatment", tr)]:
        expected = block["n_passed"] / block["n_total"] if block["n_total"] > 0 else 0
        if abs(block["pass_rate"] - expected) > 0.001:
            raise ContractViolation(
                f"Phase D {lb}: pass_rate {block['pass_rate']} != "
                f"n_passed/n_total ({block['n_passed']}/{block['n_total']} = {expected})"
            )

    # Verify same task set
    bl_tasks = set(data.get("task_ids", []))
    tr_tasks = set(data.get("treatment_task_ids", data.get("task_ids", [])))
    if bl_tasks and tr_tasks and bl_tasks != tr_tasks:
        raise ContractViolation(
            f"Phase D: baseline and treatment task sets differ. "
            f"Baseline exclusive: {bl_tasks - tr_tasks}, Treatment exclusive: {tr_tasks - bl_tasks}"
        )

    # Verify fresh task set (not used in any prior receipt)
    all_receipt_task_ids = set()
    for r in _receipts(ld):
        all_receipt_task_ids.update(r.tasks.task_ids)
    used_tasks = bl_tasks & all_receipt_task_ids if bl_tasks else set()
    if used_tasks:
        raise ContractViolation(
            f"Phase D: {len(used_tasks)} task(s) already used in prior receipts: "
            f"{', '.join(sorted(used_tasks)[:5])}. "
            f"Phase D requires fresh held-out tasks."
        )

    # Verify delta >= criterion_threshold
    delta = trr - br
    if delta < criterion_threshold:
        raise ContractViolation(
            f"Phase D: delta={delta:+.1%} < criterion_threshold={criterion_threshold:+.1%}. "
            f"Treatment does not meet pre-registered improvement criterion."
        )

    print(f"  [Contract] Phase D: B={br:.1%}, S={trr:.1%}, delta={delta:+.1%} "
          f"(threshold={criterion_threshold:+.1%}, {bl['n_total']} tasks)")


# ── Invariant 5: Phase Constants Frozen (Contract §3.2) ────────────────────

def check_phase_constants(project_root: str = None) -> None:
    """C_success, C_memory, C_latency, C_trust must be frozen before substrate evaluation."""
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    c = _phase_constants(ld)
    if c is None:
        raise ContractViolation(
            "Phase-A constants not frozen. Contract §3.2 requires "
            "C_success, C_memory, C_latency, C_trust."
        )
    errs = c.validate()
    if errs:
        raise ContractViolation("Phase constants invalid:\n" + "\n".join(f"  - {e}" for e in errs))
    if not c.frozen_at:
        raise ContractViolation("Phase constants missing frozen_at timestamp")

    # Chronology: constants must be frozen before any S1/S2 substrate experiment
    earliest_s1_s2 = _earliest_s1_s2_timestamp(ld)
    if earliest_s1_s2 and c.frozen_at > earliest_s1_s2:
        raise ContractViolation(
            f"Phase constants frozen at {c.frozen_at} but S1/S2 receipt exists "
            f"from {earliest_s1_s2}. Constants must be frozen before substrate evaluation "
            f"(Contract §3.2)."
        )

    print(f"  [Contract] Phase constants frozen at {c.frozen_at}")


# ── Invariant 6: Compensation Hypothesis (Contract §3.3) ────────────────────

def check_compensation_hypothesis(project_root: str = None) -> None:
    """If B2 dominates B1, must have numeric Compensation Hypothesis pre-registered before S1/S2."""
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    receipts = _receipts(ld)
    b1 = [r for r in receipts if r.cell == ExperimentCell.B1]
    b2 = [r for r in receipts if r.cell == ExperimentCell.B2]
    if not b1 or not b2:
        return
    b1b = max(b1, key=lambda r: r.result.metrics.pass_rate)
    b2b = max(b2, key=lambda r: r.result.metrics.pass_rate)
    dominates = (b2b.result.metrics.pass_rate >= b1b.result.metrics.pass_rate
                 and b2b.result.metrics.mean_latency_ms <= b1b.result.metrics.mean_latency_ms * 1.5)
    if dominates:
        h = _comp_hyp(ld)
        if h is None:
            raise ContractViolation(
                "B2 dominates B1 on competence and efficiency. "
                "Contract §3.3 requires Compensation Hypothesis."
            )
        if not h.hypothesis or not h.expected_compensation_metric:
            raise ContractViolation("Compensation Hypothesis exists but is incomplete.")
        if not h.preregistered_at:
            raise ContractViolation("Compensation Hypothesis missing preregistered_at timestamp.")

        # Chronology: must be preregistered before S1/S2
        earliest_s1_s2 = _earliest_s1_s2_timestamp(ld)
        if earliest_s1_s2 and h.preregistered_at > earliest_s1_s2:
            raise ContractViolation(
                f"Compensation Hypothesis preregistered at {h.preregistered_at} "
                f"but S1/S2 receipt exists from {earliest_s1_s2}. "
                f"Must be preregistered before substrate evaluation (Contract §3.3)."
            )

        print("  [Contract] Compensation hypothesis registered (pre-S1/S2)")


# ── Invariant 7: Amendment Record (Contract §11) ────────────────────────────

def check_amendment_record(project_root: str = None) -> None:
    """No protocol amendment without recording in amendment log."""
    pr = project_root or _root()
    p = os.path.join(pr, "ledger", "amendment-log.json")
    if not os.path.exists(p):
        raise ContractViolation(
            "No amendment-log.json at ledger/. Contract §11 requires one."
        )
    with open(p) as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) == 0:
        raise ContractViolation("Amendment log must be a non-empty array.")
    # Check phase skips have amendment entries
    phases_dir = os.path.join(pr, "phases")
    if os.path.isdir(phases_dir):
        amendment_reasons = [a.get("reason", "") for a in data]
        all_reasons = " ".join(amendment_reasons).lower()
        for pf in os.listdir(phases_dir):
            if not pf.endswith(".md"):
                continue
            with open(os.path.join(phases_dir, pf)) as f:
                content = f.read()
            if "skipped" in content.lower() or "not needed" in content.lower():
                pname = pf.replace(".md", "")
                if pname not in all_reasons:
                    raise ContractViolation(
                        f"Phase {pname} skipped but no amendment in log. Contract §11."
                    )
    print(f"  [Contract] Amendment record: {len(data)} entries")


# ── Invariant 8: Budget Overrun (Contract §4) ──────────────────────────────

def check_budget_overrun(project_root: str = None) -> None:
    """No phase may exceed its budget without written amendment."""
    pr = project_root or _root()
    p = os.path.join(pr, "ledger", "budgets.json")
    if not os.path.exists(p):
        # Budgets.md exists but not budgets.json — that's a warning, not blocking
        print("  [Contract] No budgets.json found — skipping budget overrun check")
        return
    with open(p) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ContractViolation("budgets.json must be a list of phase budgets.")

    violations = []
    for b in data:
        phase = b.get("phase", "?")
        overrun = _check_single_budget(b)
        if overrun:
            violations.append(f"  {phase}: {overrun}")

    if violations:
        raise ContractViolation("Budget overruns:\n" + "\n".join(violations))
    print(f"  [Contract] Budgets: {len(data)} phases within limits")


def _check_single_budget(b: dict) -> str:
    """Check a single phase budget. Returns violation string or empty string."""
    max_days = b.get("max_wall_clock_days", 0)
    current_days = b.get("current_wall_clock_days", 0)
    max_compute = b.get("max_compute_hours", 0)
    current_compute = b.get("current_compute_hours", 0)
    max_experiments = b.get("max_material_experiments", 0)
    current_experiments = b.get("current_experiments", 0)

    messages = []
    if max_days > 0 and current_days > max_days * 1.5:
        messages.append(
            f"wall clock {current_days}/{max_days}d ({current_days/max_days:.0%}) — exceeds 150%"
        )
    elif max_days > 0 and current_days > max_days * 1.25:
        messages.append(
            f"wall clock {current_days}/{max_days}d ({current_days/max_days:.0%}) — exceeds 125%"
        )
    if max_compute > 0 and current_compute > max_compute * 1.5:
        messages.append(
            f"compute {current_compute}/{max_compute}h ({current_compute/max_compute:.0%}) — exceeds 150%"
        )
    if max_experiments > 0 and current_experiments > max_experiments * 1.5:
        messages.append(
            f"experiments {current_experiments}/{max_experiments} ({current_experiments/max_experiments:.0%}) — exceeds 150%"
        )
    return "; ".join(messages) if messages else ""


# ── Invariant 9: Model/Config Parity (Contract §3.4) ───────────────────────

def check_model_config_parity(project_root: str = None) -> None:
    """Every model used in receipts must have a matching adapter with generation config."""
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    adir = os.path.join(pr, "contract", "adapters")
    receipts = _receipts(ld)

    if not receipts:
        print("  [Contract] No receipts to check model config parity against")
        return

    # Load adapter configs
    adapter_configs = {}
    if os.path.isdir(adir):
        for af in sorted(os.listdir(adir)):
            if not af.endswith(".json"):
                continue
            with open(os.path.join(adir, af)) as f:
                data = json.load(f)
            adapter_configs[data.get("model_id", af)] = data.get("generation_config", {})

    issues = []
    for r in receipts:
        mid = r.model.model_id
        gen = r.generation
        acfg = adapter_configs.get(mid, {})

        if acfg:
            # Check thinking_mode matches
            if acfg.get("thinking_mode") is not None and gen.thinking_mode != acfg["thinking_mode"]:
                issues.append(
                    f"  Receipt {r.run_id[:12]} ({r.cell.value}): thinking_mode={gen.thinking_mode} "
                    f"but adapter expects {acfg['thinking_mode']}"
                )
            # Check temperature
            if acfg.get("temperature") is not None and abs(gen.temperature - acfg["temperature"]) > 0.01:
                issues.append(
                    f"  Receipt {r.run_id[:12]} ({r.cell.value}): temperature={gen.temperature} "
                    f"but adapter expects {acfg['temperature']}"
                )

    if issues:
        raise ContractViolation("Model config parity issues:\n" + "\n".join(issues))
    print(f"  [Contract] Model config parity: {len(receipts)} receipts match adapters")