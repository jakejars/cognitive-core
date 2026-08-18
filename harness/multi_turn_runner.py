#!/usr/bin/env python3
"""
Multi-Turn Gauntlet Runner — B1 vs S1

Tests how well each system handles multi-turn conversations where
state must persist across turns.

B1 (model alone): All turns fed in a single prompt, then final question.
S1 (model + substrate): Turns fed incrementally, substrate accumulates state,
  then final question with external memory retrieval.

This is where the substrate's state tracking should provide measurable benefit.
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
from harness.gauntlet_evaluators import evaluate_task, strip_chat_markup
from gauntlets.multi_turn_tasks import all_mt_tasks, MultiTurnTask, Turn
from substrate.runtime import SubstrateRuntime
from substrate.external_memory import ExternalMemory


def run_b1_mt(h: Harness, task: MultiTurnTask, verbose: bool = False) -> dict:
    """
    B1: Feed all turns as a single prompt, then answer the question.
    This gives the model all context at once (upper bound on performance).
    """
    # Build the conversation history
    conv_parts = []
    final_question = ""
    expected = ""
    evaluator_name = "contains"
    
    for turn in task.turns:
        if turn.is_question:
            final_question = turn.content
            expected = turn.expected_answer
            evaluator_name = turn.evaluator
        else:
            conv_parts.append(f"{turn.role}: {turn.content}")
    
    # Full context: conversation history + question
    prompt = "\n\n".join(conv_parts)
    prompt += f"\n\nQuestion: {final_question}"
    
    formatted = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
    
    t0 = time.time()
    result = h.generate(formatted, max_tokens=task.max_tokens, temperature=0.0)
    elapsed = time.time() - t0
    
    output_text = strip_chat_markup(result["text"])
    
    # Evaluate using the correct evaluator
    from harness.gauntlet_evaluators import EVALUATORS
    eval_fn = EVALUATORS.get(evaluator_name, EVALUATORS["contains"])
    if isinstance(expected, list):
        eval_result = eval_fn(output_text, expected)
    else:
        eval_result = eval_fn(output_text, expected)
    
    entry = {
        "task_id": task.id,
        "gauntlet": task.gauntlet,
        "difficulty": task.difficulty,
        "output_tokens": result["output_tokens"],
        "time_seconds": round(elapsed, 3),
        "passed": eval_result["passed"],
        "score": eval_result["score"],
        "details": eval_result["details"],
    }
    
    if verbose:
        status = "✅" if eval_result["passed"] else "❌"
        print(f"  {status} {task.id:15s} score={eval_result['score']:.2f}  "
              f"{result['output_tokens']:3d} tok  {elapsed:.2f}s")
    
    return entry


def run_s1_mt(h: Harness, task: MultiTurnTask, verbose: bool = False) -> dict:
    """
    S1: Feed turns incrementally, substrate accumulates state in external memory.
    This simulates real multi-turn usage where the model doesn't have all history.
    """
    rt = SubstrateRuntime()
    ext_mem = ExternalMemory(chunk_size_tokens=50)
    
    final_question = ""
    expected = ""
    evaluator_name = "contains"
    
    # Process turns one at a time
    for turn in task.turns:
        if turn.is_question:
            final_question = turn.content
            expected = turn.expected_answer
            evaluator_name = turn.evaluator
            break  # Don't process the question as a turn
        
        # Record this turn in external memory
        turn_text = f"{turn.role}: {turn.content}"
        ext_mem.append(turn_text, source=turn.role)
        
        # Also record as observation in substrate
        rt.record_observation(turn_text, source=turn.role,
                              metadata={"task_id": task.id})
        
        # Record any claims from the assistant's responses
        if turn.role == "assistant":
            rt.record_claim(turn.content, confidence=0.9)
    
    # Now retrieve relevant context from external memory
    retrieved = ext_mem.retrieve(final_question, k=5)
    context_text = ""
    if retrieved:
        chunk_ids = [c.chunk_id for _, c in retrieved]
        context_text = ext_mem.materialise(chunk_ids)
    
    # Build the prompt with retrieved context + question
    if context_text:
        prompt = f"Previous conversation context:\n{context_text}\n\nQuestion: {final_question}"
    else:
        prompt = f"Question: {final_question}"
    
    formatted = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
    
    t0 = time.time()
    result = h.generate(formatted, max_tokens=task.max_tokens, temperature=0.0)
    elapsed = time.time() - t0
    
    output_text = strip_chat_markup(result["text"])
    
    # Evaluate
    from harness.gauntlet_evaluators import EVALUATORS
    eval_fn = EVALUATORS.get(evaluator_name, EVALUATORS["contains"])
    if isinstance(expected, list):
        eval_result = eval_fn(output_text, expected)
    else:
        eval_result = eval_fn(output_text, expected)
    
    entry = {
        "task_id": task.id,
        "gauntlet": task.gauntlet,
        "difficulty": task.difficulty,
        "output_tokens": result["output_tokens"],
        "time_seconds": round(elapsed, 3),
        "passed": eval_result["passed"],
        "score": eval_result["score"],
        "details": eval_result["details"],
        "memory_stats": ext_mem.statistics(),
    }
    
    if verbose:
        status = "✅" if eval_result["passed"] else "❌"
        print(f"  {status} {task.id:15s} score={eval_result['score']:.2f}  "
              f"{result['output_tokens']:3d} tok  {elapsed:.2f}s  "
              f"mem:{ext_mem.statistics()['chunks']}chunks")
    
    return entry


def run_comparison(verbose: bool = True, gauntlet_filter: str = None):
    """Run B1 vs S1 on multi-turn tasks."""
    print(f"\n{'='*70}")
    print(f"  Multi-Turn Gauntlet: B1 vs S1")
    print(f"{'='*70}")
    
    tasks = all_mt_tasks()
    if gauntlet_filter:
        tasks = [t for t in tasks if t.gauntlet == gauntlet_filter]
    
    print(f"  Tasks: {len(tasks)}")
    print(f"  Total turns: {sum(len(t.turns) for t in tasks)}")
    
    # Load model
    model_path = os.path.join(_project_root, "models", "MiniCPM5-1B")
    h = Harness(model_path)
    
    # Run B1
    print(f"\n  ── B1 (all context in one prompt) ──")
    b1_results = [run_b1_mt(h, t, verbose) for t in tasks]
    b1_passed = sum(1 for r in b1_results if r["passed"])
    b1_pass_rate = round(b1_passed / len(b1_results) * 100, 1)
    b1_mean_score = round(sum(r["score"] for r in b1_results) / len(b1_results), 3)
    print(f"  B1: {b1_passed}/{len(b1_results)} ({b1_pass_rate}%) score={b1_mean_score:.3f}")
    
    # Run S1
    print(f"\n  ── S1 (incremental turns + external memory) ──")
    s1_results = [run_s1_mt(h, t, verbose) for t in tasks]
    s1_passed = sum(1 for r in s1_results if r["passed"])
    s1_pass_rate = round(s1_passed / len(s1_results) * 100, 1)
    s1_mean_score = round(sum(r["score"] for r in s1_results) / len(s1_results), 3)
    print(f"  S1: {s1_passed}/{len(s1_results)} ({s1_pass_rate}%) score={s1_mean_score:.3f}")
    
    # Comparison
    print(f"\n{'='*70}")
    print(f"  COMPARISON: Multi-Turn Tasks")
    print(f"{'='*70}")
    print(f"  {'Metric':35s} {'B1 (full ctx)':>18s} {'S1 (incremental)':>18s}")
    print(f"  {'-'*35} {'-'*18} {'-'*18}")
    print(f"  {'Pass rate (%)':35s} {b1_pass_rate:>18.1f} {s1_pass_rate:>18.1f}")
    print(f"  {'Mean score':35s} {b1_mean_score:>18.3f} {s1_mean_score:>18.3f}")
    
    # Per-gauntlet
    gauntlets = sorted(set(r["gauntlet"] for r in b1_results))
    print(f"\n  Per-Gauntlet Pass Rate:")
    print(f"  {'Gauntlet':10s} {'B1':>10s} {'S1':>10s}  {'Delta':>8s}")
    print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*8}")
    for g in gauntlets:
        b1_g = [r for r in b1_results if r["gauntlet"] == g]
        s1_g = [r for r in s1_results if r["gauntlet"] == g]
        b1_r = round(sum(1 for r in b1_g if r["passed"]) / len(b1_g) * 100, 1) if b1_g else 0
        s1_r = round(sum(1 for r in s1_g if r["passed"]) / len(s1_g) * 100, 1) if s1_g else 0
        d = round(s1_r - b1_r, 1)
        print(f"  {g:10s} {b1_r:>9.1f}% {s1_r:>9.1f}%  {d:>+7.1f}%")
    
    # Save results
    save = {
        "b1": {"pass_rate": b1_pass_rate, "mean_score": b1_mean_score,
               "results": [{"id": r["task_id"], "passed": r["passed"], "score": r["score"]} for r in b1_results]},
        "s1": {"pass_rate": s1_pass_rate, "mean_score": s1_mean_score,
               "results": [{"id": r["task_id"], "passed": r["passed"], "score": r["score"]} for r in s1_results]},
    }
    save_path = os.path.join(_project_root, "ledger", "baselines", "multi_turn_comparison.json")
    with open(save_path, "w") as f:
        json.dump(save, f, indent=2)
    print(f"\n  Results saved to {save_path}")
    
    return b1_results, s1_results


if __name__ == "__main__":
    run_comparison(verbose=True)