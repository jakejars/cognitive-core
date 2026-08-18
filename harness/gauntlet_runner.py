#!/usr/bin/env python3
"""
Gauntlet Runner — Cognitive Core Gen-2 Phase A

Loads gauntlet tasks, runs them through a model harness, scores results,
and produces a comparison report.

Usage:
    python3 harness/gauntlet_runner.py                  # Run all gauntlets on B1
    python3 harness/gauntlet_runner.py --both           # Run B1 and B2
    python3 harness/gauntlet_runner.py --gauntlet M01   # Run specific gauntlet
    python3 harness/gauntlet_runner.py --both --gauntlet LCTX01
"""

import sys
import os
import json
import time
import argparse

# Ensure project root is on path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from harness import Harness
from harness.gauntlet_evaluators import evaluate_task
from gauntlets.gauntlet_tasks import all_tasks, tasks_by_gauntlet


def format_chat(prompt: str, template: str) -> str:
    """Apply the appropriate chat template."""
    if template == "qwen":
        return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    else:
        return f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"


def run_task(h: Harness, task: dict, verbose: bool = False) -> dict:
    """Run a single task and return results."""
    prompt = format_chat(task["prompt"], task.get("chat_template", "minicpm"))
    max_tokens = task.get("max_tokens", 100)

    try:
        result = h.generate(prompt, max_tokens=max_tokens, temperature=0.0)
        output_text = result["text"]

        # Evaluate
        eval_result = evaluate_task(output_text, task)

        entry = {
            "task_id": task["id"],
            "gauntlet": task["gauntlet"],
            "difficulty": task["difficulty"],
            "prompt_tokens": result["prompt_tokens"],
            "output_tokens": result["output_tokens"],
            "time_seconds": round(result["time_seconds"], 3),
            "tokens_per_sec": round(result["tokens_per_sec"], 1),
            "passed": eval_result["passed"],
            "score": eval_result["score"],
            "evaluation_details": eval_result["details"],
            "output_preview": output_text.strip()[:150],
        }

        if verbose:
            status = "✅" if eval_result["passed"] else "❌"
            print(f"  {status} {task['id']:15s} score={eval_result['score']:.2f}  "
                  f"{result['output_tokens']:3d} tok  {result['time_seconds']:5.2f}s  "
                  f"→ {output_text.strip()[:60]}")

        return entry

    except Exception as e:
        print(f"  ⚠️  {task['id']:15s} ERROR: {e}")
        return {
            "task_id": task["id"],
            "gauntlet": task["gauntlet"],
            "difficulty": task["difficulty"],
            "prompt_tokens": 0,
            "output_tokens": 0,
            "time_seconds": 0,
            "tokens_per_sec": 0,
            "passed": False,
            "score": 0.0,
            "evaluation_details": f"Runtime error: {e}",
            "output_preview": "",
        }


def run_gauntlets(model_path: str, label: str, task_filter: str = None,
                  verbose: bool = True, max_tasks: int = None) -> dict:
    """Run all (or filtered) gauntlet tasks on a model."""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")

    h = Harness(model_path)

    # Select tasks
    if task_filter:
        tasks = tasks_by_gauntlet(task_filter)
        print(f"  Gauntlet: {task_filter} ({len(tasks)} tasks)")
    else:
        tasks = all_tasks()
        print(f"  All gauntlets ({len(tasks)} tasks)")

    if max_tasks:
        tasks = tasks[:max_tasks]

    # Run each task
    results = []
    for task in tasks:
        result = run_task(h, task, verbose=verbose)
        results.append(result)

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
        "model": label,
        "total_tasks": len(results),
        "passed": len(passed),
        "failed": len(results) - len(passed),
        "pass_rate": round(len(passed) / len(results) * 100, 1) if results else 0,
        "mean_score": round(sum(r["score"] for r in results) / len(results), 3) if results else 0,
        "mean_time": round(sum(r["time_seconds"] for r in results) / len(results), 3) if results else 0,
        "total_time": round(sum(r["time_seconds"] for r in results), 2),
        "by_gauntlet": by_gauntlet,
        "results": results,
    }

    # Print summary
    print(f"\n  ─── {label} Results ───")
    print(f"  Tasks:    {summary['total_tasks']}")
    print(f"  Passed:   {summary['passed']}/{summary['total_tasks']} ({summary['pass_rate']}%)")
    print(f"  Score:    {summary['mean_score']:.2f}")
    print(f"  Time:     {summary['total_time']:.1f}s total, {summary['mean_time']:.2f}s per task")
    print(f"\n  By Gauntlet:")
    for gid, gdata in sorted(by_gauntlet.items()):
        g_pass_rate = round(gdata["passed"] / gdata["total"] * 100, 1)
        g_mean = round(sum(gdata["scores"]) / len(gdata["scores"]), 2)
        print(f"    {gid:8s} {gdata['passed']:2d}/{gdata['total']:2d} passed ({g_pass_rate}%)  "
              f"mean score: {g_mean:.2f}")

    return summary


def compare(summaries: list):
    """Print comparison of multiple model runs."""
    if len(summaries) < 2:
        return

    print(f"\n{'='*70}")
    print(f"  COMPARISON")
    print(f"{'='*70}")

    # Overall comparison
    print(f"\n  {'Metric':30s}", end="")
    for s in summaries:
        print(f"  {s['model']:>18s}", end="")
    print()

    print(f"  {'-'*30}", end="")
    for _ in summaries:
        print(f"  {'-'*18}", end="")
    print()

    print(f"  {'Pass rate (%)':30s}", end="")
    for s in summaries:
        print(f"  {s['pass_rate']:>18.1f}", end="")
    print()

    print(f"  {'Mean score':30s}", end="")
    for s in summaries:
        print(f"  {s['mean_score']:>18.3f}", end="")
    print()

    print(f"  {'Mean time (s)':30s}", end="")
    for s in summaries:
        print(f"  {s['mean_time']:>18.3f}", end="")
    print()

    print(f"  {'Total time (s)':30s}", end="")
    for s in summaries:
        print(f"  {s['total_time']:>18.1f}", end="")
    print()

    # Per-gauntlet comparison
    all_gauntlets = sorted(set(g for s in summaries for g in s.get("by_gauntlet", {})))
    if all_gauntlets:
        print(f"\n  Per-Gauntlet Pass Rate:")
        print(f"  {'Gauntlet':10s}", end="")
        for s in summaries:
            print(f"  {s['model']:>18s}", end="")
        print()
        print(f"  {'-'*10}", end="")
        for _ in summaries:
            print(f"  {'-'*18}", end="")
        print()

        for gid in all_gauntlets:
            print(f"  {gid:10s}", end="")
            for s in summaries:
                gdata = s.get("by_gauntlet", {}).get(gid, {"passed": 0, "total": 0})
                rate = round(gdata["passed"] / gdata["total"] * 100, 1) if gdata["total"] else 0
                print(f"  {rate:>17.1f}%", end="")
            print()


def main():
    parser = argparse.ArgumentParser(description="Cognitive Core Gen-2 Gauntlet Runner")
    parser.add_argument("--both", action="store_true", help="Run both B1 and B2")
    parser.add_argument("--model", type=str, default="B1", help="Model to run (B1 or B2)")
    parser.add_argument("--gauntlet", type=str, default=None, help="Specific gauntlet (e.g. M01)")
    parser.add_argument("--max-tasks", type=int, default=None, help="Limit tasks")
    parser.add_argument("--verbose", action="store_true", default=True, help="Show per-task results")
    parser.add_argument("--save", action="store_true", default=True, help="Save results")
    args = parser.parse_args()

    base = _project_root
    models_to_run = []

    if args.both:
        models_to_run = [
            (os.path.join(base, "models", "MiniCPM5-1B"), "B1-MiniCPM5-1B"),
            (os.path.join(base, "models", "Qwen3.5-4B"), "B2-Qwen3.5-4B"),
        ]
    else:
        model_path = os.path.join(base, "models", "MiniCPM5-1B")
        label = "B1-MiniCPM5-1B"
        if args.model.upper() == "B2":
            model_path = os.path.join(base, "models", "Qwen3.5-4B")
            label = "B2-Qwen3.5-4B"
        models_to_run = [(model_path, label)]

    # Update tasks to use correct chat template per model
    summaries = []
    for model_path, label in models_to_run:
        summary = run_gauntlets(model_path, label, task_filter=args.gauntlet,
                                verbose=args.verbose, max_tasks=args.max_tasks)
        summaries.append(summary)

        # Save results
        if args.save:
            save_label = label.lower().replace("-", "_")
            gauntlet_suffix = f"_{args.gauntlet.lower()}" if args.gauntlet else ""
            save_path = os.path.join(base, "ledger", "baselines",
                                     f"gauntlet_{save_label}{gauntlet_suffix}.json")
            with open(save_path, "w") as f:
                # Remove full results from saved file (too verbose)
                save_summary = {k: v for k, v in summary.items() if k != "results"}
                save_summary["result_count"] = len(summary["results"])
                # Save summary + pass/fail per task
                save_summary["tasks"] = [
                    {"id": r["task_id"], "passed": r["passed"], "score": r["score"],
                     "time": r["time_seconds"]}
                    for r in summary["results"]
                ]
                json.dump(save_summary, f, indent=2)
            print(f"\n  Results saved to {save_path}")

    # Compare if both ran
    if len(summaries) >= 2:
        compare(summaries)


if __name__ == "__main__":
    main()