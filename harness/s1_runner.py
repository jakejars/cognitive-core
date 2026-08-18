#!/usr/bin/env python3
"""
S1 Baseline — MiniCPM5-1B + Validated Substrate

The substrate operates transparently:
  - Pre-seeds memory with task context
  - Tracks provenance and effects
  - For retrieval/state tasks, appends relevant context as "information"
  - For structural/yes-no tasks, passes the prompt clean
  - Records all operations in the event ledger

This is the first test of the hypothesis:
  S1 (model + substrate) > B1 (model alone) on stateful/retrieval tasks
  while maintaining B1 performance on structural tasks.
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


def run_s1(verbose: bool = True, gauntlet_filter: str = None, max_tasks: int = None):
    """Run gauntlet tasks with model + transparent substrate."""
    print(f"\n{'='*70}")
    print(f"  S1: MiniCPM5-1B + Transparent Substrate")
    print(f"{'='*70}")

    h = Harness(os.path.join(_project_root, "models", "MiniCPM5-1B"))
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
        # For retrieval tasks (LCTX), seed the exact facts
        if task["gauntlet"] == "LCTX01":
            # Extract the "Here is some text/data" portion as background
            if "Here is" in prompt or "Below is" in prompt or "Here are" in prompt:
                background = prompt.split("Question:")[0] if "Question:" in prompt else prompt
                rt.record_observation(background, source="task_context",
                                      metadata={"task_id": task_id})

        # For state tasks (SA01), seed the state history
        if task["gauntlet"] == "SA01":
            rt.record_observation(prompt, source="task_context",
                                  metadata={"task_id": task_id})

        # For multi-hop tasks (LCTX03), seed the facts
        if task["gauntlet"] == "LCTX03":
            rt.record_observation(prompt, source="task_context",
                                  metadata={"task_id": task_id})

        # ── Build model prompt ──
        # Structural tasks (M01) and state tasks (SA01): clean prompt, no extras
        if task["gauntlet"] in ("M01", "SA01"):
            formatted = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        else:
            # For retrieval/state tasks, get substrate context
            context_packet_str = rt.compile_context(prompt, k=3)
            # Simple extraction: check if there's any relevant content
            has_context = ("Relevant claims" in context_packet_str or 
                          "Evidence" in context_packet_str)
            
            if has_context:
                # Include the context packet as a "remembered" block before the question
                enriched = f"{context_packet_str}\n\n{prompt}"
            else:
                enriched = prompt

            formatted = f"<|user|>\n{enriched}<|end|>\n<|assistant|>\n"

        # ── Run inference ──
        t0 = time.time()
        try:
            result = h.generate(formatted, max_tokens=max_tokens, temperature=0.0)
            elapsed = time.time() - t0
            output_text = result["text"]

            # ── Substrate: record outcome ──
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
        "model": "S1-MiniCPM5-1B-Substrate",
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

    print(f"\n  ─── S1 Results ───")
    print(f"  Tasks:    {summary['total_tasks']}")
    print(f"  Passed:   {summary['passed']}/{summary['total_tasks']} ({summary['pass_rate']}%)")
    print(f"  Score:    {summary['mean_score']:.2f}")
    print(f"  Time:     {summary['mean_time']:.2f}s per task")
    print(f"  Substrate: {rt.ledger.count()} events, {len(rt.compiler._memory_store)} memory entries")

    # Save
    save_path = os.path.join(_project_root, "ledger", "baselines", "s1-minicpm5-1b-substrate.json")
    with open(save_path, "w") as f:
        save_data = {k: v for k, v in summary.items()}
        save_data["tasks"] = [{"id": r["task_id"], "passed": r["passed"],
                                "score": r["score"], "time": r["time_seconds"]}
                               for r in results]
        json.dump(save_data, f, indent=2)
    print(f"  Results saved to {save_path}")

    return summary


def compare_with_b1(s1_summary: dict):
    """Compare S1 with B1 from the saved baseline."""
    b1_path = os.path.join(_project_root, "ledger", "baselines", "gauntlet_b1_minicpm5_1b.json")
    if not os.path.exists(b1_path):
        print("\n⚠️  B1 baseline not found — run gauntlet_runner.py first")
        return

    with open(b1_path) as f:
        b1 = json.load(f)

    print(f"\n{'='*70}")
    print(f"  COMPARISON: B1 (model) vs S1 (model + substrate)")
    print(f"{'='*70}")
    print(f"\n  {'Metric':30s} {'B1':>18s} {'S1':>18s}  {'Delta':>10s}")
    print(f"  {'-'*30} {'-'*18} {'-'*18} {'-'*10}")
    delta_pass = s1_summary['pass_rate'] - b1.get('pass_rate', 0)
    delta_score = s1_summary['mean_score'] - b1.get('mean_score', 0)
    print(f"  {'Pass rate (%)':30s} {b1.get('pass_rate', 0):>18.1f} {s1_summary['pass_rate']:>18.1f}  {delta_pass:>+9.1f}")
    print(f"  {'Mean score':30s} {b1.get('mean_score', 0):>18.3f} {s1_summary['mean_score']:>18.3f}  {delta_score:>+9.3f}")

    # Per-gauntlet
    all_g = sorted(set(list(b1.get("by_gauntlet", {}).keys()) +
                      list(s1_summary.get("by_gauntlet", {}).keys())))
    print(f"\n  Per-Gauntlet Pass Rate:")
    print(f"  {'Gauntlet':10s} {'B1':>10s} {'S1':>10s}  {'Delta':>8s}")
    print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*8}")
    for g in all_g:
        b1_g = b1.get("by_gauntlet", {}).get(g, {})
        b1_total = b1_g.get("total", 0)
        b1_passed = b1_g.get("passed", 0)
        b1_rate = round(b1_passed / b1_total * 100, 1) if b1_total else 0
        
        s1_g = s1_summary.get("by_gauntlet", {}).get(g, {})
        s1_rate = s1_g.get("pass_rate", 0)
        
        d = round(s1_rate - b1_rate, 1)
        print(f"  {g:10s} {b1_rate:>9.1f}% {s1_rate:>9.1f}%  {d:>+7.1f}%")


if __name__ == "__main__":
    s1 = run_s1(verbose=True)
    compare_with_b1(s1)