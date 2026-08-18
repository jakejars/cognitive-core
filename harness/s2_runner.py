#!/usr/bin/env python3
"""
S2 Baseline — Qwen3.5-4B + SubstrateRuntime

The substrate operates identically to S1 (same seeding, context compilation,
provenance). Only the underlying model changes.

This is the second cell of the 2×2 factorial design:
  S1 = MiniCPM5-1B + Substrate
  S2 = Qwen3.5-4B + Substrate
"""

import sys
import os
import json
import time

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from harness import Harness
from harness.gauntlet_evaluators import evaluate_task
from gauntlets.gauntlet_tasks import all_tasks, tasks_by_gauntlet
from substrate.runtime import SubstrateRuntime

from contract import (
    ExperimentCell, Partition, ReceiptWriter,
    ModelManifest, GenerationManifest, TaskManifest,
    RunMetrics, RunResult, ProtocolInfo, SubstrateManifest,
)


def run_s2(verbose: bool = True, gauntlet_filter: str = None, max_tasks: int = None,
           partition: Partition = Partition.DEV):
    """Run gauntlet tasks with Qwen3.5-4B + transparent substrate."""
    print(f"\n{'='*70}")
    print(f"  S2: Qwen3.5-4B + Transparent Substrate")
    print(f"{'='*70}")

    h = Harness(os.path.join(_project_root, "models", "Qwen3.5-4B"))
    rt = SubstrateRuntime()

    # Select tasks
    tasks = all_tasks()
    if gauntlet_filter:
        tasks = tasks_by_gauntlet(gauntlet_filter)
    if max_tasks:
        tasks = tasks[:max_tasks]

    print(f"  Tasks: {len(tasks)}")

    results = []
    for task in tasks:
        task_id = task["id"]
        prompt = task["prompt"]
        max_tokens = task.get("max_tokens", 50)

        # ── Substrate: seed memory with task context ──
        if task["gauntlet"] in ("LCTX01", "LCTX03", "SA01"):
            rt.record_observation(prompt, source="task_context",
                                  metadata={"task_id": task_id})

        # ── Build model prompt using Qwen format ──
        if task["gauntlet"] in ("M01", "SA01"):
            formatted = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        else:
            context_packet_str = rt.compile_context(prompt, k=3)
            has_context = ("Relevant claims" in context_packet_str or
                          "Evidence" in context_packet_str)
            if has_context:
                enriched = f"{context_packet_str}\n\n{prompt}"
            else:
                enriched = prompt
            formatted = f"<|im_start|>user\n{enriched}<|im_end|>\n<|im_start|>assistant\n"

        # ── Run inference ──
        t0 = time.time()
        try:
            result = h.generate(formatted, max_tokens=max_tokens, temperature=0.0)
            elapsed = time.time() - t0
            output_text = result["text"]

            eval_result = evaluate_task(output_text, task)

            if eval_result["passed"]:
                rt.record_claim(
                    f"Task {task_id} result: {output_text.strip()[:100]}",
                    confidence=eval_result["score"],
                )

            entry = {
                "task_id": task_id,
                "gauntlet": task["gauntlet"],
                "difficulty": task["difficulty"],
                "prompt_tokens": result["prompt_tokens"],
                "output_tokens": result["output_tokens"],
                "time_seconds": round(elapsed, 3),
                "tokens_per_sec": round(result["tokens_per_sec"], 1),
                "passed": eval_result["passed"],
                "score": eval_result["score"],
                "evaluation_details": eval_result["details"],
            }

            status = "✅" if eval_result["passed"] else "❌"
            if verbose:
                print(f"  {status} {task_id:15s} score={eval_result['score']:.2f}  "
                      f"{result['output_tokens']:3d} tok  {elapsed:.2f}s")

        except Exception as e:
            entry = {
                "task_id": task_id,
                "gauntlet": task["gauntlet"],
                "passed": False, "score": 0.0,
                "evaluation_details": f"Error: {e}",
                "time_seconds": 0, "output_tokens": 0,
            }
            print(f"  ⚠️  {task_id:15s} ERROR: {e}")

        results.append(entry)

    # Aggregate
    passed = [r for r in results if r["passed"]]
    by_gauntlet = {}
    for r in results:
        g = r["gauntlet"]
        if g not in by_gauntlet:
            by_gauntlet[g] = {"total": 0, "passed": 0, "scores": []}
        by_gauntlet[g]["total"] += 1
        by_gauntlet[g]["scores"].append(r["score"])
        if r["passed"]:
            by_gauntlet[g]["passed"] += 1

    summary = {
        "model": "S2-Qwen3.5-4B-Substrate",
        "total_tasks": len(results),
        "passed": len(passed),
        "pass_rate": round(len(passed) / len(results) * 100, 1) if results else 0,
        "mean_score": round(sum(r["score"] for r in results) / len(results), 3) if results else 0,
        "mean_time": round(sum(r["time_seconds"] for r in results) / len(results), 3) if results else 0,
        "by_gauntlet": {g: {"passed": d["passed"], "total": d["total"],
                             "pass_rate": round(d["passed"]/d["total"]*100, 1) if d["total"] else 0}
                        for g, d in by_gauntlet.items()},
        "substrate_stats": rt.get_statistics(),
    }

    print(f"\n  ─── S2 Results ───")
    print(f"  Tasks:    {summary['total_tasks']}")
    print(f"  Passed:   {summary['passed']}/{summary['total_tasks']} ({summary['pass_rate']}%)")
    print(f"  Score:    {summary['mean_score']:.2f}")
    print(f"  Time:     {summary['mean_time']:.2f}s per task")

    # Save via ReceiptWriter
    try:
        writer = ReceiptWriter(_project_root)
        writer.write_run(
            cell=ExperimentCell.S2,
            partition=partition,
            model=ModelManifest(
                model_id="Qwen3.5-4B",
                revision="main",
                weights_hash="",
                tokenizer_id="Qwen3.5-4B",
                tokenizer_hash="",
                template_adapter_version="verified_qwen_v1",
                applied_template="qwen",
            ),
            generation=GenerationManifest(
                thinking_mode=False,
                max_total_tokens=131072,
                max_answer_tokens=256,
                temperature=0.0,
                top_p=0.0,
                stop_policy="eos_plus_stops",
                stop_tokens=[151645, 151643],
            ),
            tasks=TaskManifest(
                source="gauntlets/gauntlet_tasks.py",
                partition=partition,
                task_ids=[r["task_id"] for r in results],
                content_hash="",
                n_tasks=len(results),
            ),
            result=RunResult(
                result_hash="",
                completed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                metrics=RunMetrics(
                    n_passed=summary["passed"],
                    n_total=summary["total_tasks"],
                    pass_rate=summary["pass_rate"] / 100.0,
                    mean_score=summary["mean_score"],
                    mean_latency_ms=summary["mean_time"] * 1000,
                    total_time_s=sum(r["time_seconds"] for r in results),
                ),
            ),
            protocol=ProtocolInfo(
                contract_version="2.2",
                preregistration_hash="",
                amendment_log_hash="",
                hypothesis="Substrate generality: Qwen3.5-4B + Substrate",
            ),
            hypothesis="Substrate generality: Qwen3.5-4B + Substrate",
            budget_consumed={"compute_hours": 0},
        )
        print(f"  [Contract] Receipt created for S2")
    except Exception as e:
        print(f"  ⚠️  Receipt creation failed: {e}")

    # Also save legacy baseline
    save_path = os.path.join(_project_root, "ledger", "baselines", "s2-qwen3.5-4b-substrate.json")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w") as f:
        save_data = {k: v for k, v in summary.items()}
        save_data["tasks"] = [{"id": r["task_id"], "passed": r["passed"],
                                "score": r["score"], "time": r["time_seconds"]}
                               for r in results]
        json.dump(save_data, f, indent=2)
    print(f"  Results saved to {save_path}")

    return summary


if __name__ == "__main__":
    run_s2(verbose=True)