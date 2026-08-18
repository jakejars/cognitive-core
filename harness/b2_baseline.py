"""
Cognitive Core Gen-2 — Phase A B2 Baseline Script

Load and benchmark the strong ~4B model (Qwen3.5-4B) using the same harness.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import Harness


def run_b2_baseline():
    print("=" * 60)
    print("Phase A — B2 Baseline (Qwen3.5-4B)")
    print("=" * 60)

    h = Harness("models/Qwen3.5-4B")
    info = h.get_model_info()
    print(f"\nModel info: {info}")

    # Basic tests
    prompts = [
        "What is the capital of France?",
        "Explain how a transformer attention mechanism works in one paragraph.",
        "If I have 3 apples and buy 5 more, then give away 2, how many do I have?",
        "Write a short function in Python that checks if a string is a palindrome.",
        "Summarise the concept of 'demand-paged virtual memory'.",
    ]

    print("\n--- Benchmarking ---")
    for prompt in prompts:
        result = h.generate(prompt, max_tokens=150, temperature=0.0)
        print(f"\nPrompt: {prompt[:60]}...")
        print(f"  Output: {result['output_tokens']} tokens in {result['time_seconds']:.2f}s ({result['tokens_per_sec']:.1f} tok/s)")
        print(f"  Preview: {result['text'][:150]}...")


if __name__ == "__main__":
    run_b2_baseline()