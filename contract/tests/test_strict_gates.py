import json
from dataclasses import asdict
from pathlib import Path

import pytest

from contract.hardening import (
    ContractViolation,
    check_compensation_hypothesis,
    check_phase_d_gate,
)
from contract.schema import (
    ExperimentCell,
    ExperimentReceipt,
    GenerationManifest,
    ModelManifest,
    Partition,
    ProtocolInfo,
    RunMetrics,
    RunResult,
    SubstrateManifest,
    TaskManifest,
)


def _receipt(cell, pass_rate, tasks_per_gb, tasks_per_second, created_at="2026-08-18T01:00:00+00:00"):
    r = ExperimentReceipt(
        run_id=f"{cell.value}-dev",
        cell=cell,
        partition=Partition.DEV,
        created_at=created_at,
        model=ModelManifest(
            model_id="M",
            revision="r",
            weights_hash="",
            tokenizer_id="T",
            tokenizer_hash="",
            template_adapter_version="verified_x",
            applied_template="a",
        ),
        generation=GenerationManifest(
            thinking_mode=False,
            max_total_tokens=100,
            max_answer_tokens=10,
            temperature=0.0,
            top_p=0.0,
            stop_policy="explicit_plus_eos",
            stop_tokens=[],
            seed=0,
        ),
        tasks=TaskManifest(
            source="fresh.json",
            partition=Partition.DEV,
            task_ids=["t1", "t2"],
            content_hash="same-taskset",
            n_tasks=2,
        ),
        substrate=SubstrateManifest("r", "s", ["x"]) if cell in (ExperimentCell.S1, ExperimentCell.S2) else None,
        result=RunResult(
            result_hash="result",
            raw_output_hash="raw",
            completed_at=created_at,
            metrics=RunMetrics(
                n_passed=round(pass_rate * 2),
                n_total=2,
                pass_rate=pass_rate,
                mean_score=pass_rate,
                mean_latency_ms=10,
                total_time_s=1,
                successful_tasks_per_gb=tasks_per_gb,
                successful_tasks_per_second=tasks_per_second,
            ),
        ),
        protocol=ProtocolInfo("2.2", "p", "a", "h", "d"),
        budget_consumed={"compute_hours": 0.01},
    )
    r.finalize()
    return r


def _save_receipt(root, receipt):
    path = Path(root, "ledger", "receipts")
    path.mkdir(parents=True, exist_ok=True)
    Path(path, f"{receipt.run_id}.json").write_text(json.dumps(asdict(receipt), default=str))


def test_compensation_gate_requires_efficiency_metrics(tmp_path):
    _save_receipt(tmp_path, _receipt(ExperimentCell.B1, 0.5, None, None))
    _save_receipt(tmp_path, _receipt(ExperimentCell.B2, 1.0, None, None))
    with pytest.raises(ContractViolation, match="efficiency"):
        check_compensation_hypothesis(str(tmp_path))


def test_compensation_required_only_when_b2_dominates_matched_efficiency(tmp_path):
    _save_receipt(tmp_path, _receipt(ExperimentCell.B1, 0.5, 1.0, 1.0))
    _save_receipt(tmp_path, _receipt(ExperimentCell.B2, 1.0, 2.0, 2.0))
    with pytest.raises(ContractViolation, match="Compensation Hypothesis"):
        check_compensation_hypothesis(str(tmp_path))


def test_phase_d_requires_paired_outcomes(tmp_path):
    Path(tmp_path, "ledger").mkdir()
    Path(tmp_path, "ledger", "counterfactual_eval.json").write_text(json.dumps({
        "protocol_version": "2.2",
        "pre_registered_criterion": "improve >= 20%",
        "criterion_threshold": 0.2,
        "criterion_alpha": 0.05,
        "task_ids": ["a", "b", "c", "d", "e"],
        "baseline": {"n_passed": 0, "n_total": 5, "pass_rate": 0.0},
        "treatment": {"n_passed": 5, "n_total": 5, "pass_rate": 1.0}
    }))
    with pytest.raises(ContractViolation, match="paired"):
        check_phase_d_gate(str(tmp_path))


def test_phase_d_accepts_strong_paired_improvement(tmp_path):
    Path(tmp_path, "ledger").mkdir()
    pairs = [
        {"task_id": f"t{i}", "baseline_passed": False, "treatment_passed": True}
        for i in range(5)
    ]
    Path(tmp_path, "ledger", "counterfactual_eval.json").write_text(json.dumps({
        "protocol_version": "2.2",
        "pre_registered_criterion": "improve >= 20%, one-sided exact paired p <= .05",
        "criterion_threshold": 0.2,
        "criterion_alpha": 0.05,
        "task_ids": [p["task_id"] for p in pairs],
        "baseline": {"n_passed": 0, "n_total": 5, "pass_rate": 0.0},
        "treatment": {"n_passed": 5, "n_total": 5, "pass_rate": 1.0},
        "pairs": pairs
    }))
    check_phase_d_gate(str(tmp_path))
