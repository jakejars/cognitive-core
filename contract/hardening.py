"""Strict confirmation-time invariants layered over the v2.2 base checks."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from contract.adapter_verifier import AdapterVerifier
from contract.evidence import hash_json
from contract.invariants import (
    ContractViolation,
    _comp_hyp,
    _earliest_s1_s2_timestamp,
    _lockbox_ledger,
    _receipts,
    check_amendment_record,
    check_experiment_matrix,
    check_lockbox_intact,
    check_phase_constants,
)
from contract.model_adapter import ModelAdapter
from contract.schema import ExperimentCell, Partition


def _adapter_map(project_root: str) -> dict[str, ModelAdapter]:
    result = {}
    for path in sorted((Path(project_root) / "contract" / "adapters").glob("*.json")):
        with path.open() as f:
            data = json.load(f)
        adapter = ModelAdapter(data, str(path))
        result[adapter.model_id] = adapter
    return result


def check_chat_template_parity(project_root: str = None) -> None:
    pr = project_root or os.getcwd()
    issues = AdapterVerifier(pr).verify_all()
    if issues:
        raise ContractViolation("Adapter verification failed:\n  " + "\n  ".join(issues))

    adapters = _adapter_map(pr)
    for receipt in _receipts(os.path.join(pr, "ledger")):
        adapter = adapters.get(receipt.model.model_id)
        if adapter is None:
            raise ContractViolation(
                f"Receipt {receipt.run_id} uses model {receipt.model.model_id} with no adapter"
            )
        if receipt.model.applied_template != adapter.adapter_hash:
            raise ContractViolation(
                f"Receipt {receipt.run_id} adapter hash does not match current pinned adapter"
            )
    print(f"  [Contract] Adapter verification: {len(adapters)} pinned adapters verified")


def check_model_config_parity(project_root: str = None) -> None:
    pr = project_root or os.getcwd()
    receipts = _receipts(os.path.join(pr, "ledger"))
    if not receipts:
        print("  [Contract] No receipts to check model/config parity against")
        return

    adapters = _adapter_map(pr)
    issues = []
    expected_fields = (
        "thinking_mode",
        "max_total_tokens",
        "max_answer_tokens",
        "temperature",
        "top_p",
        "stop_policy",
        "stop_tokens",
    )

    for receipt in receipts:
        adapter = adapters.get(receipt.model.model_id)
        if adapter is None:
            issues.append(f"{receipt.run_id}: no adapter for {receipt.model.model_id}")
            continue
        expected = adapter.generation_manifest(seed=receipt.generation.seed)
        for field in expected_fields:
            if getattr(receipt.generation, field) != getattr(expected, field):
                issues.append(
                    f"{receipt.run_id}: generation.{field}={getattr(receipt.generation, field)!r} "
                    f"!= adapter {getattr(expected, field)!r}"
                )
        if receipt.model.applied_template != adapter.adapter_hash:
            issues.append(f"{receipt.run_id}: applied_template is not the pinned adapter hash")
        if receipt.partition in (Partition.REPLICATION, Partition.LOCKBOX):
            if not receipt.model.weights_hash or not receipt.model.tokenizer_hash:
                issues.append(f"{receipt.run_id}: confirmatory model/tokenizer hashes are missing")

    by_tier_and_taskset = {}
    for receipt in receipts:
        key = (receipt.partition, receipt.tasks.content_hash)
        by_tier_and_taskset.setdefault(key, []).append(receipt)

    required = {ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1, ExperimentCell.S2}
    for (partition, _), group in by_tier_and_taskset.items():
        by_cell = {receipt.cell: receipt for receipt in group}
        if not required.issubset(by_cell):
            continue
        selected = [by_cell[cell] for cell in sorted(required, key=lambda c: c.value)]
        task_ids = [tuple(r.tasks.task_ids) for r in selected]
        if len(set(task_ids)) != 1:
            issues.append(f"{partition.value}: factorial cells do not use identical ordered task IDs")
        seeds = {r.generation.seed for r in selected}
        if len(seeds) != 1:
            issues.append(f"{partition.value}: factorial cells use different seeds {sorted(seeds)}")
        answer_budgets = {r.generation.max_answer_tokens for r in selected}
        if len(answer_budgets) != 1:
            issues.append(
                f"{partition.value}: factorial cells use different answer budgets {sorted(answer_budgets)}"
            )
        s1, s2 = by_cell[ExperimentCell.S1], by_cell[ExperimentCell.S2]
        if not s1.substrate or not s2.substrate:
            issues.append(f"{partition.value}: S1/S2 substrate manifests are required")
        elif (
            s1.substrate.config_hash != s2.substrate.config_hash
            or s1.substrate.modules != s2.substrate.modules
        ):
            issues.append(f"{partition.value}: S1 and S2 do not use the same substrate config")

    if issues:
        raise ContractViolation("Model/config parity issues:\n  " + "\n  ".join(issues))
    print(f"  [Contract] Model/config parity: {len(receipts)} receipts consistent")


def check_lockbox_pass(project_root: str = None) -> None:
    pr = project_root or os.getcwd()
    check_lockbox_intact(pr)
    receipts = [
        receipt for receipt in _receipts(os.path.join(pr, "ledger"))
        if receipt.partition == Partition.LOCKBOX
    ]
    if not receipts:
        raise ContractViolation("No validated LOCKBOX receipts exist")

    groups = {}
    for receipt in receipts:
        groups.setdefault(receipt.tasks.content_hash, []).append(receipt)
    required = {ExperimentCell.B1, ExperimentCell.B2, ExperimentCell.S1, ExperimentCell.S2}
    complete = []
    for taskset_hash, group in groups.items():
        cells = {receipt.cell for receipt in group}
        if required.issubset(cells):
            complete.append((taskset_hash, group))
    if len(complete) != 1:
        raise ContractViolation(
            f"Expected exactly one complete B1/B2/S1/S2 lockbox taskset; found {len(complete)}"
        )

    taskset_hash, group = complete[0]
    by_cell = {}
    for receipt in group:
        if receipt.cell in by_cell:
            raise ContractViolation(
                f"Lockbox taskset has duplicate receipt for cell {receipt.cell.value}"
            )
        by_cell[receipt.cell] = receipt

    baseline_ids = tuple(by_cell[ExperimentCell.B1].tasks.task_ids)
    if any(tuple(by_cell[cell].tasks.task_ids) != baseline_ids for cell in required):
        raise ContractViolation("Lockbox factorial cells do not use the identical ordered taskset")

    ledger = _lockbox_ledger(os.path.join(pr, "ledger"))
    frozen_hashes = []
    for task_id in baseline_ids:
        entry = ledger.entries.get(task_id)
        if entry is None:
            raise ContractViolation(
                f"Lockbox task {task_id} has no frozen ledger entry keyed by task ID"
            )
        frozen_hashes.append(entry.content_hash)
        for cell in required:
            count = int(entry.cell_evaluations.get(cell.value, 0))
            if count != 1:
                raise ContractViolation(
                    f"Lockbox task {task_id}: expected exactly one {cell.value} evaluation, got {count}"
                )

    expected_taskset_hash = hash_json(frozen_hashes)
    if expected_taskset_hash != taskset_hash:
        raise ContractViolation(
            "Lockbox receipt taskset hash does not match the ordered frozen per-task hashes"
        )

    print(f"  [Contract] Lockbox complete: {len(baseline_ids)} tasks x 4 authorised cells")


def _matched_b1_b2(receipts):
    groups = {}
    for receipt in receipts:
        if receipt.partition != Partition.DEV or receipt.cell not in (ExperimentCell.B1, ExperimentCell.B2):
            continue
        groups.setdefault(receipt.tasks.content_hash, {})[receipt.cell] = receipt
    return [group for group in groups.values() if ExperimentCell.B1 in group and ExperimentCell.B2 in group]


def check_compensation_hypothesis(project_root: str = None) -> None:
    """Apply the Phase-A mechanical gate to matched B1/B2 evidence.

    B2 dominance means it is non-worse on task success and non-worse on both
    successful-tasks/GB and successful-tasks/second for the same frozen DEV taskset.
    """
    pr = project_root or os.getcwd()
    ld = os.path.join(pr, "ledger")
    matched = _matched_b1_b2(_receipts(ld))
    if not matched:
        return

    domination_observed = False
    for group in matched:
        b1, b2 = group[ExperimentCell.B1], group[ExperimentCell.B2]
        m1, m2 = b1.result.metrics, b2.result.metrics
        efficiency = (
            m1.successful_tasks_per_gb,
            m2.successful_tasks_per_gb,
            m1.successful_tasks_per_second,
            m2.successful_tasks_per_second,
        )
        if any(value is None for value in efficiency):
            raise ContractViolation(
                "Cannot evaluate B1/B2 mechanical gate: cost-adjusted efficiency metrics "
                "successful_tasks_per_gb and successful_tasks_per_second are required"
            )
        if (
            m2.pass_rate >= m1.pass_rate
            and m2.successful_tasks_per_gb >= m1.successful_tasks_per_gb
            and m2.successful_tasks_per_second >= m1.successful_tasks_per_second
        ):
            domination_observed = True

    if not domination_observed:
        return

    hypothesis = _comp_hyp(ld)
    if hypothesis is None:
        raise ContractViolation(
            "B2 dominates B1 on matched competence and cost-adjusted efficiency; "
            "a numeric Compensation Hypothesis is required before Phase B"
        )
    if not hypothesis.hypothesis or not hypothesis.expected_compensation_metric:
        raise ContractViolation("Compensation Hypothesis exists but is incomplete")
    if not hypothesis.preregistered_at:
        raise ContractViolation("Compensation Hypothesis missing preregistered_at timestamp")
    earliest_substrate = _earliest_s1_s2_timestamp(ld)
    if earliest_substrate and hypothesis.preregistered_at > earliest_substrate:
        raise ContractViolation(
            "Compensation Hypothesis was registered after S1/S2 substrate evaluation began"
        )
    print("  [Contract] Compensation hypothesis valid for observed B2 dominance")


def _one_sided_binomial_tail(successes: int, trials: int) -> float:
    if trials <= 0:
        return 1.0
    return sum(math.comb(trials, k) for k in range(successes, trials + 1)) / (2 ** trials)


def check_phase_d_gate(project_root: str = None) -> None:
    """Require fresh paired counterfactual evidence and the preregistered delta/statistical gate."""
    pr = project_root or os.getcwd()
    ld = os.path.join(pr, "ledger")
    path = os.path.join(ld, "counterfactual_eval.json")
    if not os.path.isfile(path):
        raise ContractViolation("Phase D gate: no counterfactual_eval.json found")
    with open(path) as f:
        data = json.load(f)

    if data.get("protocol_version") != "2.2":
        raise ContractViolation("Phase D: protocol_version must be '2.2'")
    if not data.get("pre_registered_criterion"):
        raise ContractViolation("Phase D: pre_registered_criterion is required")
    threshold = data.get("criterion_threshold")
    alpha = data.get("criterion_alpha")
    if threshold is None or alpha is None:
        raise ContractViolation("Phase D: criterion_threshold and criterion_alpha must be preregistered")

    baseline, treatment = data.get("baseline", {}), data.get("treatment", {})
    for label, block in (("baseline", baseline), ("treatment", treatment)):
        for key in ("n_passed", "n_total", "pass_rate"):
            if key not in block:
                raise ContractViolation(f"Phase D {label}: missing {key}")
        if block["n_total"] <= 0:
            raise ContractViolation(f"Phase D {label}: n_total must be > 0")
        expected = block["n_passed"] / block["n_total"]
        if abs(block["pass_rate"] - expected) > 1e-9:
            raise ContractViolation(f"Phase D {label}: pass_rate does not match raw counts")

    task_ids = list(data.get("task_ids", []))
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ContractViolation("Phase D requires raw paired baseline/treatment outcomes")
    pair_ids = [str(pair.get("task_id", "")) for pair in pairs]
    if pair_ids != task_ids:
        raise ContractViolation("Phase D paired task IDs must exactly match the preregistered task_ids order")
    if len(pairs) != baseline["n_total"] or len(pairs) != treatment["n_total"]:
        raise ContractViolation("Phase D paired outcome count must equal baseline/treatment n_total")

    prior_task_ids = set()
    for receipt in _receipts(ld):
        prior_task_ids.update(receipt.tasks.task_ids)
    reused = set(task_ids) & prior_task_ids
    if reused:
        raise ContractViolation(
            f"Phase D held-out tasks are not fresh; already used: {', '.join(sorted(reused)[:5])}"
        )

    reconstructed_b = sum(bool(pair.get("baseline_passed")) for pair in pairs)
    reconstructed_t = sum(bool(pair.get("treatment_passed")) for pair in pairs)
    if reconstructed_b != baseline["n_passed"] or reconstructed_t != treatment["n_passed"]:
        raise ContractViolation("Phase D aggregate counts do not match raw paired outcomes")

    delta = treatment["pass_rate"] - baseline["pass_rate"]
    if delta < float(threshold):
        raise ContractViolation(
            f"Phase D delta={delta:+.1%} is below preregistered threshold={float(threshold):+.1%}"
        )

    harmed = sum(
        bool(pair.get("baseline_passed")) and not bool(pair.get("treatment_passed"))
        for pair in pairs
    )
    improved = sum(
        not bool(pair.get("baseline_passed")) and bool(pair.get("treatment_passed"))
        for pair in pairs
    )
    discordant = harmed + improved
    p_value = _one_sided_binomial_tail(improved, discordant) if improved > harmed else 1.0
    if p_value > float(alpha):
        raise ContractViolation(
            f"Phase D paired exact p={p_value:.4f} exceeds preregistered alpha={float(alpha):.4f}"
        )

    print(
        f"  [Contract] Phase D: delta={delta:+.1%}, paired p={p_value:.4f}, "
        f"improved={improved}, harmed={harmed}"
    )


def check_budget_overrun(project_root: str = None) -> None:
    """Enforce the contract's 100/125/150 percent overrun policy."""
    pr = Path(project_root or os.getcwd())
    path = pr / "ledger" / "budgets.json"
    if not path.is_file():
        raise ContractViolation("ledger/budgets.json is required before Phase B")
    with path.open() as f:
        budgets = json.load(f)
    if not isinstance(budgets, list) or not budgets:
        raise ContractViolation("budgets.json must be a non-empty list")

    issues = []
    dimensions = (
        ("wall_clock_days", "max_wall_clock_days", "current_wall_clock_days"),
        ("researcher_days", "max_researcher_days", "current_researcher_days"),
        ("compute_hours", "max_compute_hours", "current_compute_hours"),
        ("material_experiments", "max_material_experiments", "current_experiments"),
    )
    for budget in budgets:
        phase = budget.get("phase", "?")
        for label, max_key, current_key in dimensions:
            maximum = float(budget.get(max_key, 0) or 0)
            current = float(budget.get(current_key, 0) or 0)
            if maximum <= 0:
                continue
            ratio = current / maximum
            if ratio >= 1.5:
                issues.append(f"Phase {phase} {label}: {ratio:.0%} >= 150%; phase must freeze")
            elif ratio >= 1.25:
                extension = budget.get("bounded_extension") or {}
                if not extension.get("reason") or not extension.get("approved_at"):
                    issues.append(
                        f"Phase {phase} {label}: {ratio:.0%} >= 125% without bounded written exception"
                    )
            elif ratio >= 1.0 and budget.get("mode") not in {"evaluate_best", "closed"}:
                issues.append(
                    f"Phase {phase} {label}: {ratio:.0%} >= 100%; mode must be evaluate_best or closed"
                )
    if issues:
        raise ContractViolation("Budget policy violations:\n  " + "\n  ".join(issues))
    print(f"  [Contract] Budget policy: {len(budgets)} phase ledgers valid")


__all__ = [
    "ContractViolation",
    "check_experiment_matrix",
    "check_lockbox_intact",
    "check_lockbox_pass",
    "check_chat_template_parity",
    "check_phase_d_gate",
    "check_phase_constants",
    "check_compensation_hypothesis",
    "check_amendment_record",
    "check_budget_overrun",
    "check_model_config_parity",
]
