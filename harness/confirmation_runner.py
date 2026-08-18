#!/usr/bin/env python3
"""Unified B1/B2/S1/S2 confirmation runner.

This is the only runner intended for the clean v2.2 confirmation campaign.
All four factorial cells share the same partition loading, adapter rendering,
generation policy, scoring, evidence hashing, and receipt path.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from contract.evidence import (
    git_code_diff_hash,
    hash_json,
    hash_model_weights,
    hash_taskset,
    hash_tokenizer,
    hash_tree,
    sha256_file,
)
from contract.model_adapter import ModelAdapter
from contract.receipt_writer import ReceiptWriter
from contract.schema import (
    ExperimentCell,
    ModelManifest,
    Partition,
    ProtocolInfo,
    RunMetrics,
    RunResult,
    SubstrateManifest,
    TaskManifest,
)
from harness import Harness
from harness.experiment_support import (
    load_partition_tasks,
    mark_lockbox_evaluated,
    mark_lockbox_exposed,
    validate_lockbox_taskset,
)
from harness.gauntlet_evaluators import evaluate_task
from substrate.runtime import SubstrateRuntime


CELL_CONFIG = {
    ExperimentCell.B1: ("MiniCPM5-1B", False),
    ExperimentCell.B2: ("Qwen3.5-4B", False),
    ExperimentCell.S1: ("MiniCPM5-1B", True),
    ExperimentCell.S2: ("Qwen3.5-4B", True),
}


def _substrate_prompt(rt: SubstrateRuntime, task: dict) -> str:
    """One substrate policy shared by S1 and S2."""
    task_id = task["id"]
    prompt = task["prompt"]
    gauntlet = task.get("gauntlet", "")

    if gauntlet == "LCTX01":
        background = prompt.split("Question:")[0] if "Question:" in prompt else prompt
        rt.record_observation(background, source="task_context", metadata={"task_id": task_id})
    elif gauntlet in ("LCTX03", "SA01"):
        rt.record_observation(prompt, source="task_context", metadata={"task_id": task_id})

    if gauntlet in ("M01", "SA01"):
        return prompt

    packet = rt.compile_context(prompt, k=3)
    if "Relevant claims" in packet or "Evidence" in packet:
        return f"{packet}\n\n{prompt}"
    return prompt


def _required_hash(path: Path, label: str, confirmation: bool) -> str:
    if path.is_file():
        return sha256_file(path)
    if confirmation:
        raise RuntimeError(f"{label} is required for confirmatory evidence: {path}")
    return ""


def run_cell(
    *,
    cell: ExperimentCell,
    partition: Partition,
    task_file: str | None,
    gauntlet_filter: str | None,
    seed: int,
    verbose: bool,
) -> dict:
    model_id, use_substrate = CELL_CONFIG[cell]
    model_dir = _project_root / "models" / model_id
    if not model_dir.is_dir():
        raise RuntimeError(f"model directory not found: {model_dir}")

    tasks = load_partition_tasks(
        str(_project_root),
        partition,
        task_file=task_file,
        gauntlet_filter=gauntlet_filter,
    )

    if partition == Partition.LOCKBOX:
        validate_lockbox_taskset(str(_project_root), tasks, cell)
        mark_lockbox_exposed(str(_project_root), tasks)

    harness = Harness(str(model_dir))
    adapter = ModelAdapter.load(str(_project_root), model_id)
    adapter_issues = adapter.verify(harness.tokenizer)
    if adapter_issues:
        raise RuntimeError("adapter verification failed:\n  - " + "\n  - ".join(adapter_issues))
    generation = adapter.generation_manifest(seed=seed)

    substrate = SubstrateRuntime() if use_substrate else None
    results = []

    for task in tasks:
        task_id = str(task["id"])
        model_prompt = _substrate_prompt(substrate, task) if substrate else task["prompt"]
        rendered = adapter.render(harness.tokenizer, model_prompt)

        attempted = False
        try:
            attempted = True
            inference = harness.generate(
                rendered,
                max_tokens=generation.max_answer_tokens,
                temperature=generation.temperature,
                top_p=generation.top_p,
                stop_tokens=generation.stop_tokens,
                seed=generation.seed,
                verbose=False,
            )
            output_text = inference["text"]
            evaluated = evaluate_task(output_text, task)

            if substrate and evaluated["passed"]:
                substrate.record_claim(
                    f"Task {task_id} result: {output_text.strip()[:100]}",
                    confidence=evaluated["score"],
                )

            row = {
                "task_id": task_id,
                "gauntlet": task.get("gauntlet", ""),
                "passed": bool(evaluated["passed"]),
                "score": float(evaluated["score"]),
                "evaluation_details": evaluated["details"],
                "output_text": output_text,
                "prompt_tokens": inference["prompt_tokens"],
                "output_tokens": inference["output_tokens"],
                "time_seconds": inference["time_seconds"],
                "tokens_per_sec": inference["tokens_per_sec"],
                "finish_reason": inference["finish_reason"],
                "peak_memory_gb": inference.get("peak_memory_gb"),
                "executed_generation_config": inference["generation_config"],
            }
        except Exception as exc:
            row = {
                "task_id": task_id,
                "gauntlet": task.get("gauntlet", ""),
                "passed": False,
                "score": 0.0,
                "evaluation_details": f"runtime error: {exc}",
                "output_text": "",
                "time_seconds": 0.0,
                "output_tokens": 0,
                "peak_memory_gb": None,
            }
        finally:
            if partition == Partition.LOCKBOX and attempted:
                # An attempted model call consumes this cell's one authorised look,
                # even if inference/scoring/receipt finalisation subsequently fails.
                mark_lockbox_evaluated(str(_project_root), task_id, cell)

        results.append(row)
        if verbose:
            status = "PASS" if row["passed"] else "FAIL"
            print(f"[{cell.value}] {task_id}: {status} score={row['score']:.3f}")

    passed = sum(1 for row in results if row["passed"])
    total_time = sum(float(row.get("time_seconds", 0.0)) for row in results)
    mean_score = sum(float(row.get("score", 0.0)) for row in results) / len(results)
    peak_values = [float(row["peak_memory_gb"]) for row in results if row.get("peak_memory_gb")]
    peak_memory = max(peak_values) if peak_values else None

    summary = {
        "cell": cell.value,
        "partition": partition.value,
        "model_id": model_id,
        "n_passed": passed,
        "n_total": len(results),
        "pass_rate": passed / len(results),
        "mean_score": mean_score,
        "total_time_s": total_time,
        "mean_latency_ms": (total_time / len(results)) * 1000,
        "peak_memory_gb": peak_memory,
        "taskset_hash": hash_taskset(tasks),
        "adapter_hash": adapter.adapter_hash,
        "results": results,
    }

    confirmation = partition in (Partition.REPLICATION, Partition.LOCKBOX)
    weights_hash = hash_model_weights(model_dir) if confirmation else ""
    tokenizer_hash = hash_tokenizer(model_dir) if confirmation else ""
    prereg_hash = _required_hash(
        _project_root / "ledger" / "confirmation-campaign.md",
        "confirmation preregistration",
        confirmation,
    )
    amendment_hash = _required_hash(
        _project_root / "ledger" / "amendment-log.json",
        "amendment log",
        confirmation,
    )
    try:
        code_hash = git_code_diff_hash(_project_root)
    except Exception:
        if confirmation:
            raise
        code_hash = ""

    substrate_manifest = None
    if substrate:
        substrate_manifest = SubstrateManifest(
            revision=code_hash or "dev-unpinned",
            config_hash=hash_tree(_project_root / "substrate"),
            modules=["runtime", "context_compiler", "provenance"],
        )

    raw_output_hash = hash_json(results)
    result_hash = hash_json({key: value for key, value in summary.items() if key != "results"})
    metrics = RunMetrics(
        n_passed=passed,
        n_total=len(results),
        pass_rate=passed / len(results),
        mean_score=mean_score,
        mean_latency_ms=(total_time / len(results)) * 1000,
        total_time_s=total_time,
        model_resident_memory_gb=peak_memory,
        successful_tasks_per_gb=(passed / peak_memory) if peak_memory else None,
        successful_tasks_per_second=(passed / total_time) if total_time else None,
    )

    writer = ReceiptWriter(str(_project_root))
    receipt = writer.write_run(
        cell=cell,
        partition=partition,
        model=ModelManifest(
            model_id=model_id,
            revision=adapter.revision,
            weights_hash=weights_hash,
            tokenizer_id=model_id,
            tokenizer_hash=tokenizer_hash,
            template_adapter_version=f"verified_{adapter.adapter_hash[:16]}",
            applied_template=adapter.adapter_hash,
        ),
        generation=generation,
        tasks=TaskManifest(
            source=str(Path(task_file).resolve()) if task_file else "gauntlets/gauntlet_tasks.py",
            partition=partition,
            task_ids=[str(task["id"]) for task in tasks],
            content_hash=hash_taskset(tasks),
            n_tasks=len(tasks),
        ),
        substrate=substrate_manifest,
        result=RunResult(
            result_hash=result_hash,
            raw_output_hash=raw_output_hash,
            completed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            metrics=metrics,
        ),
        protocol=ProtocolInfo(
            contract_version="2.2",
            preregistration_hash=prereg_hash,
            amendment_log_hash=amendment_hash,
            hypothesis="2x2 factorial substrate/small-executive confirmation",
            code_diff_hash=code_hash,
        ),
        hypothesis="2x2 factorial substrate/small-executive confirmation",
        code_diff_hash=code_hash,
        budget_consumed={"compute_hours": total_time / 3600.0},
    )

    # Convenience mirror is written only after the authoritative receipt succeeds.
    run_dir = _project_root / "ledger" / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    mirror = run_dir / f"{receipt.run_id}.json"
    with mirror.open("w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(
        f"{cell.value}/{partition.value}: {passed}/{len(results)} "
        f"({passed / len(results):.1%}); receipt={receipt.receipt_hash[:16]}..."
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognitive Core v2.2 confirmation runner")
    parser.add_argument("--cell", required=True, choices=["B1", "B2", "S1", "S2"])
    parser.add_argument("--partition", default="dev", choices=["dev", "replication", "lockbox"])
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--gauntlet", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    run_cell(
        cell=ExperimentCell(args.cell),
        partition=Partition(args.partition),
        task_file=args.task_file,
        gauntlet_filter=args.gauntlet,
        seed=args.seed,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
