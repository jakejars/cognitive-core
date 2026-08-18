#!/usr/bin/env python3
"""
Long-Context Evaluation Runner — Phase C

Tests retrieval accuracy at varying context lengths.
  B1: Native context window (up to 131K tokens)
  S1: External memory chunk retrieval (any length)

From Memory Spec §17 (RULER-style), §22 (LCTX gauntlets):
  - One needle (LCTX01)
  - Many needles (LCTX02)
  - Multi-hop distributed (LCTX03)
  - Latest state (LCTX04)
  - Supersession (LCTX05)
"""

import sys
import os
import json
import time
import math

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from harness import Harness
from harness.gauntlet_evaluators import strip_chat_markup, contains
from harness.long_context_gen import LongContextGenerator
from substrate.external_memory import ExternalMemory


# ── Context lengths to test ─────────────────────────────────────────

CONTEXT_LENGTHS = [
    1_000,      # 1K — baseline
    10_000,     # 10K
    50_000,     # 50K
    100_000,    # 100K
    # 500_000,   # 500K — uncomment when ready for large-scale test
    # 1_000_000, # 1M — target
]

DEPTH_POSITIONS = [0.1, 0.25, 0.5, 0.75, 0.9]
"""Depth positions as fractions of total context length."""


def run_b1_retrieval(h: Harness, context: str, question: str,
                     expected: str, max_tokens: int = 50) -> dict:
    """
    B1: Feed entire context + question in one prompt.
    Limited by native context window (~131K tokens).
    """
    # Estimate token count
    approx_tokens = len(context.split()) + len(question.split())
    
    prompt = f"{context}\n\nQuestion: {question}"
    formatted = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
    
    t0 = time.time()
    result = h.generate(formatted, max_tokens=max_tokens, temperature=0.0)
    elapsed = time.time() - t0
    
    output = strip_chat_markup(result["text"])
    eval_result = contains(output, expected.split(" is ")[-1].split(" of ")[-1].rstrip(".") if " is " in expected else expected[:30])
    
    # More precise: check if key value from the needle is in output
    import re
    values = re.findall(r'(\d+)\s*(units|ms|MB|GHz|W|%|req/s)', expected)
    if values:
        expected_val = values[0][0] + " " + values[0][1]
        eval_result = contains(output, values[0][0])
    
    return {
        "output": output[:100],
        "output_tokens": result["output_tokens"],
        "time_seconds": round(elapsed, 3),
        "passed": eval_result["passed"],
        "score": eval_result["score"],
        "context_tokens_approx": approx_tokens,
    }


def run_s1_retrieval(h: Harness, context: str, question: str,
                     expected: str, max_tokens: int = 50) -> dict:
    """
    S1: Store context in external memory, then retrieve relevant chunks.
    Not limited by context window.
    """
    ext_mem = ExternalMemory(chunk_size_tokens=100)
    
    # Store context in external memory
    t0_store = time.time()
    ext_mem.append(context, source="long_context")
    store_time = time.time() - t0_store
    
    # Retrieve relevant chunks
    retrieved = ext_mem.retrieve(question, k=5)
    chunk_text = ""
    if retrieved:
        chunk_ids = [c.chunk_id for _, c in retrieved]
        chunk_text = ext_mem.materialise(chunk_ids)
    
    # Build prompt with retrieved context
    if chunk_text:
        prompt = f"Relevant information from history:\n{chunk_text}\n\nQuestion: {question}"
    else:
        prompt = f"Question: {question}"
    
    formatted = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
    
    t0_gen = time.time()
    result = h.generate(formatted, max_tokens=max_tokens, temperature=0.0)
    gen_time = time.time() - t0_gen
    
    output = strip_chat_markup(result["text"])
    
    # Evaluate
    import re
    values = re.findall(r'(\d+)\s*(units|ms|MB|GHz|W|%|req/s)', expected)
    eval_result = {"passed": False, "score": 0.0}
    if values:
        val = values[0][0]
        eval_result = contains(output, val)
    
    return {
        "output": output[:100],
        "output_tokens": result["output_tokens"],
        "time_seconds": round(store_time + gen_time, 3),
        "store_time": round(store_time, 3),
        "gen_time": round(gen_time, 3),
        "passed": eval_result["passed"],
        "score": eval_result["score"],
        "chunks_retrieved": len(retrieved),
        "memory_stats": ext_mem.statistics(),
    }


def run_length_comparison(target_tokens: int, needles_count: int = 3,
                          verbose: bool = True) -> dict:
    """Run B1 vs S1 at a specific context length."""
    gen = LongContextGenerator(seed=42 + target_tokens)
    
    context, needles, qa_pairs = gen.generate_needle_qa(
        target_tokens=target_tokens,
        num_needles=needles_count,
        needle_type="fact",
    )
    
    actual_tokens = len(context.split())
    
    if verbose:
        print(f"\n  Context: {actual_tokens:,} tokens, {needles_count} needles")
    
    # Load model
    model_path = os.path.join(_project_root, "models", "MiniCPM5-1B")
    h = Harness(model_path)
    
    # Can B1 use native context?
    b1_possible = actual_tokens <= 120000  # Leave margin for prompt
    
    b1_results = []
    s1_results = []
    
    for qa in qa_pairs:
        question = qa["question"]
        expected = qa["expected"]
        depth = qa["depth"]
        
        if verbose:
            print(f"    Needle at depth {depth:.0%}: Q: {question}")
        
        # B1
        if b1_possible:
            b1_r = run_b1_retrieval(h, context, question, expected)
            b1_r["depth"] = depth
            b1_results.append(b1_r)
            if verbose:
                s = "✅" if b1_r["passed"] else "❌"
                print(f"      B1: {s} {b1_r['output'][:60]} ({b1_r['time_seconds']:.2f}s)")
        
        # S1
        s1_r = run_s1_retrieval(h, context, question, expected)
        s1_r["depth"] = depth
        s1_results.append(s1_r)
        if verbose:
            s = "✅" if s1_r["passed"] else "❌"
            print(f"      S1: {s} {s1_r['output'][:60]} ({s1_r['time_seconds']:.2f}s)")
    
    summary = {
        "target_tokens": target_tokens,
        "actual_tokens": actual_tokens,
        "needles": needles_count,
        "b1_possible": b1_possible,
        "b1": {
            "passed": sum(1 for r in b1_results if r["passed"]) if b1_results else 0,
            "total": len(b1_results),
            "pass_rate": round(sum(1 for r in b1_results if r["passed"]) / len(b1_results) * 100, 1) if b1_results else 0,
            "mean_time": round(sum(r["time_seconds"] for r in b1_results) / len(b1_results), 3) if b1_results else 0,
        },
        "s1": {
            "passed": sum(1 for r in s1_results if r["passed"]),
            "total": len(s1_results),
            "pass_rate": round(sum(1 for r in s1_results if r["passed"]) / len(s1_results) * 100, 1),
            "mean_time": round(sum(r["time_seconds"] for r in s1_results) / len(s1_results), 3),
        },
    }
    
    if b1_possible:
        delta = round(summary["s1"]["pass_rate"] - summary["b1"]["pass_rate"], 1)
        summary["delta_vs_b1"] = delta
        if verbose:
            print(f"      → B1: {summary['b1']['pass_rate']}% vs S1: {summary['s1']['pass_rate']}% (Δ={delta:+.1f}%)")
    else:
        delta = summary["s1"]["pass_rate"]
        summary["delta_vs_b1"] = None
        if verbose:
            print(f"      → B1 not possible (>131K). S1: {summary['s1']['pass_rate']}%")
    
    return summary


def run_full_comparison(verbose: bool = True):
    """Run comparison across all context lengths."""
    print(f"\n{'='*70}")
    print(f"  Long-Context Comparison: B1 vs S1")
    print(f"  Memory Spec §9 — LC0 Baseline (External Memory)")
    print(f"{'='*70}")
    print(f"\n  MiniCPM5-1B native context: 131,072 tokens")
    print(f"  External memory chunk size: 100 tokens")
    print(f"  Needles per context: 3 (at depths 10%, 25%, 50%, 75%, 90%)")
    print()
    
    all_results = []
    
    for length in CONTEXT_LENGTHS:
        if verbose:
            print(f"\n  {'─'*60}")
        
        result = run_length_comparison(
            target_tokens=length,
            needles_count=min(5, max(3, length // 5000)),
            verbose=verbose,
        )
        all_results.append(result)
    
    # Summary table
    print(f"\n{'='*70}")
    print(f"  SUMMARY: Long-Context Retrieval Accuracy")
    print(f"{'='*70}")
    print(f"  {'Context Size':>15s} {'B1 (native)':>15s} {'S1 (ext mem)':>15s} {'Delta':>10s}")
    print(f"  {'─'*15} {'─'*15} {'─'*15} {'─'*10}")
    
    for r in all_results:
        size = f"{r['actual_tokens']:,}"
        b1_rate = f"{r['b1']['pass_rate']}%" if r['b1_possible'] else "N/A (>131K)"
        s1_rate = f"{r['s1']['pass_rate']}%"
        delta_str = f"{r['delta_vs_b1']:+.1f}%" if r['delta_vs_b1'] is not None else "N/A"
        print(f"  {size:>15s} {b1_rate:>15s} {s1_rate:>15s} {delta_str:>10s}")
    
    # Save
    save_path = os.path.join(_project_root, "ledger", "baselines", "long_context_comparison.json")
    with open(save_path, "w") as f:
        # Strip large data for serialization
        save_data = []
        for r in all_results:
            save_data.append({k: v for k, v in r.items()})
        json.dump(save_data, f, indent=2)
    print(f"\n  Results saved to {save_path}")
    
    return all_results


if __name__ == "__main__":
    results = run_full_comparison(verbose=True)