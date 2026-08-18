"""
Cognitive Core Gen-2 — Phase A Baseline Harness

Minimal harness to:
  - Load stock MiniCPM5-1B (and later ~4B models) via MLX
  - Run inference with grammar-constrained decoding
  - Measure latency, memory, token throughput
  - Evaluate against gauntlet tasks

Usage:
    from harness import Harness
    h = Harness("models/MiniCPM5-1B")
    result = h.generate("Hello", max_tokens=100)
"""

import json
import time
import os
from pathlib import Path
from typing import Optional

import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler


class Harness:
    """Baseline evaluation harness for Cognitive Core Gen-2."""

    def __init__(self, model_path: str, max_kv_size: int = 131072):
        """
        Args:
            model_path: Path or HF repo ID for the model.
            max_kv_size: Max KV-cache size (default matches MiniCPM5 native 131K).
        """
        self.model_path = str(Path(model_path).resolve()) if Path(model_path).exists() else model_path
        self.max_kv_size = max_kv_size

        print(f"[Harness] Loading model from {self.model_path} ...")
        t0 = time.time()
        self.model, self.tokenizer = load(self.model_path)
        load_time = time.time() - t0
        print(f"[Harness] Loaded in {load_time:.2f}s")

        # Basic model info
        self.params = self.model.nparams if hasattr(self.model, "nparams") else None
        self.layers = getattr(self.model, "layers", None)
        if self.layers is None and hasattr(self.model, "model"):
            self.layers = getattr(self.model.model, "layers", None)
        n_layers = len(self.layers) if self.layers else "?"
        print(f"[Harness] Parameters: {self.params} | Layers: {n_layers}")

        # Tokenizer info
        self.vocab_size = len(self.tokenizer) if hasattr(self.tokenizer, "__len__") else "?"

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 0.0,
        verbose: bool = False,
    ) -> dict:
        """
        Run generation and return results with timing.

        Returns:
            dict with keys: text, prompt_tokens, output_tokens,
                            total_tokens, tokens_per_sec, time_seconds
        """
        # Tokenize to count prompt tokens
        prompt_tokens = self.tokenizer.encode(prompt)
        n_prompt = len(prompt_tokens)

        # Create sampler (default: greedy)
        sampler = make_sampler(temp=temperature, top_p=top_p)

        # Generate (MLX-LM 0.31+ returns str directly)
        t0 = time.time()
        output_text = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
            verbose=verbose,
        )
        elapsed = time.time() - t0

        # Count output tokens
        if isinstance(output_text, str):
            n_output = len(self.tokenizer.encode(output_text))
        else:
            n_output = len(output_text)
            output_text = self.tokenizer.decode(output_text)

        return {
            "text": output_text,
            "prompt_tokens": n_prompt,
            "output_tokens": n_output,
            "total_tokens": n_prompt + n_output,
            "tokens_per_sec": n_output / elapsed if elapsed > 0 else 0,
            "time_seconds": elapsed,
        }

    def benchmark(self, prompt: str, max_tokens: int = 256, n_runs: int = 3) -> dict:
        """Run generation multiple times and return aggregate stats."""
        results = []
        for i in range(n_runs):
            # Warmup on first run
            result = self.generate(prompt, max_tokens=max_tokens, temperature=0.0)
            results.append(result)

        times = [r["time_seconds"] for r in results]
        tokens = [r["output_tokens"] for r in results]
        tps = [r["tokens_per_sec"] for r in results]

        return {
            "n_runs": n_runs,
            "prompt": prompt[:80] + ("..." if len(prompt) > 80 else ""),
            "mean_time": sum(times) / len(times),
            "p50_time": sorted(times)[len(times) // 2],
            "p95_time": sorted(times)[int(len(times) * 0.95)],
            "mean_tokens_per_sec": sum(tps) / len(tps),
            "total_output_tokens": sum(tokens),
            "sample_output": results[-1]["text"][:200] if results else "",
        }

    def get_model_info(self) -> dict:
        """Return model metadata."""
        return {
            "path": self.model_path,
            "params": self.params,
            "max_kv_size": self.max_kv_size,
            "vocab_size": self.vocab_size,
        }


def quick_test():
    """Quick smoke test — loads model and runs one generation."""
    h = Harness("models/MiniCPM5-1B")
    info = h.get_model_info()
    print(f"\nModel info: {json.dumps(info, indent=2)}")

    result = h.generate("Hello! What can you help me with today?", max_tokens=100)
    print(f"\nGeneration: {result['output_tokens']} tokens in {result['time_seconds']:.2f}s ({result['tokens_per_sec']:.1f} tok/s)")
    print(f"Output preview: {result['text'][:200]}")

    benchmark = h.benchmark("What is 2+2?", max_tokens=50, n_runs=3)
    print(f"\nBenchmark: {benchmark['mean_time']:.2f}s avg, {benchmark['mean_tokens_per_sec']:.1f} tok/s avg")


if __name__ == "__main__":
    quick_test()