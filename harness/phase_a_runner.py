#!/usr/bin/env python3
"""
Phase A — Full Baseline Comparison: B1 (MiniCPM5-1B) vs B2 (Qwen3.5-4B)

Runs identical prompts on both models, collects latency/throughput/memory stats,
saves to ledger/baselines/.
"""

import sys, os, json, time
# Ensure project root is on path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from harness import Harness

# Representative prompts covering different capabilities
PROMPTS = {
    "factual": "What is the capital of France? Answer concisely.",
    "reasoning": "If I have 3 apples and buy 5 more, then give away 2, how many do I have? Show your working step by step.",
    "coding": "Write a short Python function that checks if a string is a palindrome.",
    "explanation": "Explain the difference between TCP and UDP in one sentence each.",
}

def format_chat(prompt: str, model_type: str) -> str:
    """Apply appropriate chat template."""
    if model_type == "qwen":
        return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    else:
        return f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"


def run_benchmark(model_path: str, label: str, model_type: str) -> dict:
    print(f"\n{'='*60}")
    print(f"Benchmark: {label}")
    print(f"{'='*60}")

    h = Harness(model_path)

    results = {}
    for key, prompt in PROMPTS.items():
        formatted = format_chat(prompt, model_type)
        result = h.generate(formatted, max_tokens=256, temperature=0.0)
        results[key] = {
            "prompt": prompt,
            "prompt_tokens": result["prompt_tokens"],
            "output_tokens": result["output_tokens"],
            "time_seconds": round(result["time_seconds"], 3),
            "tokens_per_sec": round(result["tokens_per_sec"], 1),
        }
        print(f"  {key:15s} → {result['output_tokens']:3d} tok  {result['time_seconds']:6.2f}s  {result['tokens_per_sec']:6.1f} tok/s")
        # Show non-empty snippet
        snippet = result['text'].strip()[:100].replace('\n', ' | ')
        print(f"    ↳ {snippet}...")

    # Aggregates
    times = [r["time_seconds"] for r in results.values()]
    tps = [r["tokens_per_sec"] for r in results.values()]
    toks = [r["output_tokens"] for r in results.values()]

    summary = {
        "model": label,
        "path": model_path,
        "n_prompts": len(results),
        "mean_time": round(sum(times) / len(times), 3),
        "median_time": round(sorted(times)[len(times) // 2], 3),
        "mean_tokens_per_sec": round(sum(tps) / len(tps), 1),
        "total_output_tokens": sum(toks),
        "results": results,
    }

    print(f"\n  --- Summary ---")
    print(f"  Mean time:     {summary['mean_time']:.2f}s")
    print(f"  Mean tok/s:    {summary['mean_tokens_per_sec']:.1f}")
    print(f"  Total output:  {summary['total_output_tokens']} tokens")

    return summary


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # B1: MiniCPM5-1B
    b1 = run_benchmark(
        os.path.join(base, "models", "MiniCPM5-1B"),
        "B1-MiniCPM5-1B", "minicpm"
    )

    # B2: Qwen3.5-4B
    b2 = run_benchmark(
        os.path.join(base, "models", "Qwen3.5-4B"),
        "B2-Qwen3.5-4B", "qwen"
    )

    # Save
    baseline_dir = os.path.join(base, "ledger", "baselines")
    os.makedirs(baseline_dir, exist_ok=True)

    with open(os.path.join(baseline_dir, "b1-minicpm5-1b.json"), "w") as f:
        json.dump(b1, f, indent=2)
    with open(os.path.join(baseline_dir, "b2-qwen3.5-4b.json"), "w") as f:
        json.dump(b2, f, indent=2)

    # Comparison report
    print(f"\n{'='*60}")
    print("COMPARISON: B1 (MiniCPM5-1B) vs B2 (Qwen3.5-4B)")
    print(f"{'='*60}")
    print(f"{'Metric':30s} {'B1 (1B)':>14s} {'B2 (4B)':>14s}")
    print(f"{'-'*30} {'-'*14} {'-'*14}")
    print(f"{'Mean time (s)':30s} {b1['mean_time']:>14.2f} {b2['mean_time']:>14.2f}")
    print(f"{'Mean tok/s':30s} {b1['mean_tokens_per_sec']:>14.1f} {b2['mean_tokens_per_sec']:>14.1f}")
    print(f"{'Total output tokens':30s} {b1['total_output_tokens']:>14d} {b2['total_output_tokens']:>14d}")

    print(f"\nResults saved to ledger/baselines/")