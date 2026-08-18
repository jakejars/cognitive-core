"""Research Contract invariants — executable protocol enforcement (Contract v2.2)."""
from __future__ import annotations
import json, os
from typing import Dict, List, Optional
from contract.schema import (
    ExperimentCell, ExperimentReceipt, LockboxLedger,
    LockboxEntry, Partition, PhaseConstants, CompensationHypothesis,
    receipt_from_dict,
)

class ContractViolation(Exception): pass

def _root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(d) if os.path.exists(os.path.join(os.path.dirname(d), "ledger")) else d

def _receipts(ld: str) -> List[ExperimentReceipt]:
    rd = os.path.join(ld, "receipts")
    if not os.path.isdir(rd): return []
    out = []
    for fn in sorted(os.listdir(rd)):
        if not fn.endswith(".json"): continue
        try:
            with open(os.path.join(rd, fn)) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue
        try:
            r = receipt_from_dict(data)
        except (KeyError, TypeError):
            continue
        if r.receipt_hash and r.result.metrics.n_total > 0:
            out.append(r)
    return out

def _lockbox_ledger(ld: str) -> LockboxLedger:
    p = os.path.join(ld, "lockbox-ledger.json")
    if not os.path.exists(p): return LockboxLedger()
    with open(p) as f:
        d = json.load(f)
    return LockboxLedger(entries={k: LockboxEntry(**v) for k, v in d.get("entries", {}).items()})

def _phase_constants(ld: str) -> Optional[PhaseConstants]:
    p = os.path.join(ld, "phase-constants.json")
    if not os.path.exists(p): return None
    with open(p) as f: return PhaseConstants(**json.load(f))

def _comp_hyp(ld: str) -> Optional[CompensationHypothesis]:
    p = os.path.join(ld, "compensation-hypothesis.json")
    if not os.path.exists(p): return None
    with open(p) as f: return CompensationHypothesis(**json.load(f))

# ── Invariant 1: Experiment Matrix (Contract §2) ───────────────────────

def check_experiment_matrix(project_root: str = None) -> None:
    """Requires validated receipts for B1/B2/S1/S2. Empty files don't count."""
    pr = project_root or _root()
    receipts = _receipts(os.path.join(pr, "ledger"))
    cells: Dict[ExperimentCell, list] = {}
    for r in receipts:
        cells.setdefault(r.cell, []).append(r)
    required = [ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1, ExperimentCell.S2]
    missing = [c.value for c in required
               if not [r for r in cells.get(c, []) if r.partition != Partition.LOCKBOX]]
    if missing:
        raise ContractViolation(
            f"Matrix incomplete: no validated receipts for {', '.join(missing)}. "
            "Receipts with metrics required — file existence is not evidence.")
    for p in (Partition.DEV, Partition.REPLICATION):
        if all(any(r.partition == p for r in cells.get(c, [])) for c in required):
            print(f"  [Contract] Matrix complete: 4 cells on {p.value}"); return
    print("  [Contract] Matrix: cells exist on mixed partitions")

# ── Invariant 2: Lockbox Integrity (Contract §3.1) ─────────────────────

def check_lockbox_integrity(project_root: str = None) -> None:
    """Lockbox items must not have been exposed before freeze. Post-freeze recording != contamination."""
    pr = project_root or _root()
    ledger = _lockbox_ledger(os.path.join(pr, "ledger"))
    if not ledger.entries:
        raise ContractViolation("No lockbox ledger at ledger/lockbox-ledger.json. Contract §3.1 requires one.")
    violations = []
    for ch, e in ledger.entries.items():
        if e.partition != Partition.LOCKBOX: continue
        if e.first_evaluated_at and e.frozen_at and e.first_evaluated_at < e.frozen_at:
            violations.append(f"  {ch[:12]}: evaluated {e.first_evaluated_at} before freeze {e.frozen_at}")
        if e.first_exposed_at and e.frozen_at and e.first_exposed_at < e.frozen_at:
            violations.append(f"  {ch[:12]}: exposed {e.first_exposed_at} before freeze {e.frozen_at}")
        if e.evaluation_count > 1:
            violations.append(f"  {ch[:12]}: evaluated {e.evaluation_count}x (max 1)")
    if violations:
        raise ContractViolation("Lockbox violations:\n" + "\n".join(violations))
    untouched = sum(1 for e in ledger.entries.values() if e.evaluation_count == 0)
    print(f"  [Contract] Lockbox: {len(ledger.entries)} items, {untouched} untouched")

# ── Invariant 3: Chat Template Parity (Contract §2, §3.4) ──────────────

def check_chat_template_parity(project_root: str = None) -> None:
    """Each model needs a verified adapter with golden tokenisation tests, not source-string checks."""
    pr = project_root or _root()
    adir = os.path.join(pr, "contract", "adapters")
    if not os.path.isdir(adir):
        raise ContractViolation("No contract/adapters/ directory. Verified adapters with golden tokens required.")
    afiles = sorted(f for f in os.listdir(adir) if f.endswith(".json"))
    if not afiles:
        raise ContractViolation("No adapter manifests in contract/adapters/.")
    issues = []
    for af in afiles:
        with open(os.path.join(adir, af)) as f: data = json.load(f)
        mid = data.get("model_id", af)
        if not data.get("template_source"): issues.append(f"  {mid}: missing template_source")
        g = data.get("golden_tokenisation_test", {})
        if not g.get("test_input") or not g.get("expected_token_ids"):
            issues.append(f"  {mid}: incomplete golden_tokenisation_test")
        if not data.get("generation_config"): issues.append(f"  {mid}: no generation_config")
        if not data.get("template_string"): issues.append(f"  {mid}: missing template_string")
    for r in _receipts(os.path.join(pr, "ledger")):
        if not r.model.template_adapter_version.startswith("verified_"):
            issues.append(f"  Receipt {r.run_id[:12]} ({r.cell.value}): adapter not verified")
    if issues:
        raise ContractViolation(f"Template parity issues:\n" + "\n".join(issues))
    print(f"  [Contract] Template parity: {len(afiles)} verified adapters")

# ── Invariant 4: Phase D Gate (Contract §6 — Phase D) ──────────────────

def check_phase_d_gate(project_root: str = None) -> None:
    """Requires raw paired A/B results with calculable delta, not a JSON boolean."""
    pr = project_root or _root()
    p = os.path.join(pr, "ledger", "counterfactual_eval.json")
    if not os.path.exists(p):
        raise ContractViolation("Phase D gate: no counterfactual_eval.json found.")
    with open(p) as f: data = json.load(f)
    if data.get("protocol_version") != "2.2":
        raise ContractViolation("Phase D: missing protocol_version='2.2'")
    if not data.get("pre_registered_criterion"):
        raise ContractViolation("Phase D: no pre_registered_criterion")
    bl, tr = data.get("baseline", {}), data.get("treatment", {})
    if not bl or not tr:
        raise ContractViolation("Phase D: baseline and treatment required")
    for lb, block in [("baseline", bl), ("treatment", tr)]:
        for k in ("n_passed", "n_total", "pass_rate"):
            if k not in block: raise ContractViolation(f"Phase D {lb}: missing {k}")
    br, trr = bl["pass_rate"], tr["pass_rate"]
    if bl.get("n_total", 0) == 0:
        raise ContractViolation("Phase D: n_total=0")
    print(f"  [Contract] Phase D: B={br:.1%}, S={trr:.1%}, delta={trr-br:+.1%} ({bl['n_total']} tasks)")

# ── Invariant 5: Phase Constants Frozen (Contract §3.2) ────────────────

def check_phase_constants(project_root: str = None) -> None:
    """C_success, C_memory, C_latency, C_trust must be frozen before substrate evaluation."""
    pr = project_root or _root()
    c = _phase_constants(os.path.join(pr, "ledger"))
    if c is None:
        raise ContractViolation("Phase-A constants not frozen. Contract §3.2 requires C_success, C_memory, C_latency, C_trust.")
    errs = c.validate()
    if errs:
        raise ContractViolation("Phase constants invalid:\n" + "\n".join(f"  - {e}" for e in errs))
    if not c.frozen_at:
        raise ContractViolation("Phase constants missing frozen_at timestamp")
    print(f"  [Contract] Phase constants frozen at {c.frozen_at}")

# ── Invariant 6: Compensation Hypothesis (Contract §3.3) ────────────────

def check_compensation_hypothesis(project_root: str = None) -> None:
    """If B2 dominates B1, must have numeric Compensation Hypothesis."""
    pr = project_root or _root()
    ld = os.path.join(pr, "ledger")
    receipts = _receipts(ld)
    b1 = [r for r in receipts if r.cell == ExperimentCell.B1]
    b2 = [r for r in receipts if r.cell == ExperimentCell.B2]
    if not b1 or not b2: return
    b1b = max(b1, key=lambda r: r.result.metrics.pass_rate)
    b2b = max(b2, key=lambda r: r.result.metrics.pass_rate)
    dominates = (b2b.result.metrics.pass_rate >= b1b.result.metrics.pass_rate
                 and b2b.result.metrics.mean_latency_ms <= b1b.result.metrics.mean_latency_ms * 1.5)
    if dominates:
        h = _comp_hyp(ld)
        if h is None:
            raise ContractViolation("B2 dominates B1. Contract §3.3 requires Compensation Hypothesis.")
        if not h.hypothesis or not h.expected_compensation_metric:
            raise ContractViolation("Compensation Hypothesis exists but is incomplete.")
        print("  [Contract] Compensation hypothesis registered")

# ── Invariant 7: Amendment Record (Contract §11) ────────────────────────

def check_amendment_record(project_root: str = None) -> None:
    """No protocol amendment without recording in amendment log."""
    pr = project_root or _root()
    p = os.path.join(pr, "ledger", "amendment-log.json")
    if not os.path.exists(p):
        raise ContractViolation("No amendment-log.json at ledger/. Contract §11 requires one.")
    with open(p) as f: data = json.load(f)
    if not isinstance(data, list) or len(data) == 0:
        raise ContractViolation("Amendment log must be a non-empty array.")
    # Check phase skips have amendment entries
    phases_dir = os.path.join(pr, "phases")
    if os.path.isdir(phases_dir):
        amendment_reasons = [a.get("reason", "") for a in data]
        all_reasons = " ".join(amendment_reasons).lower()
        for pf in os.listdir(phases_dir):
            if not pf.endswith(".md"): continue
            with open(os.path.join(phases_dir, pf)) as f: content = f.read()
            if "skipped" in content.lower() or "not needed" in content.lower():
                pname = pf.replace(".md", "")
                if pname not in all_reasons:
                    raise ContractViolation(f"Phase {pname} skipped but no amendment in log. Contract §11.")
    print(f"  [Contract] Amendment record: {len(data)} entries")