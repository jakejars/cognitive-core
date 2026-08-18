"""
Cognitive Core Gen-2 — baseline inference harness.

The module is import-safe on non-Apple CI so protocol/support tests can run there;
actual inference still fails closed unless MLX + mlx-lm are installed.
"""

import json
import time
from pathlib import Path
from typing import Optional, Sequence

try:
    import mlx.core as mx
    from mlx_lm import load, stream_generate
    from mlx_lm.sample_utils import make_sampler
except ImportError:  # Protocol tests run on Linux CI where MLX is unavailable.
    mx = None
    load = None
    stream_generate = None
    make_sampler = None


class Harness:
    """Baseline evaluation harness for Cognitive Core Gen-2."""

    def __init__(self, model_path: str, max_kv_size: int = 131072):
        if mx is None or load is None or stream_generate is None or make_sampler is None:
            raise RuntimeError("MLX/MLX-LM is required for inference; protocol-only CI may import without it")

        self.model_path = str(Path(model_path).resolve()) if Path(model_path).exists() else model_path
        self.max_kv_size = max_kv_size

        print(f"[Harness] Loading model from {self.model_path} ...")
        t0 = time.time()
        self.model, self.tokenizer = load(self.model_path)
        load_time = time.time() - t0
        print(f"[Harness] Loaded in {load_time:.2f}s")

        self.params = self.model.nparams if hasattr(self.model, "nparams") else None
        self.layers = getattr(self.model, "layers", None)
        if self.layers is None and hasattr(self.model, "model"):
            self.layers = getattr(self.model.model, "layers", None)
        n_layers = len(self.layers) if self.layers else "?"
        print(f"[Harness] Parameters: {self.params} | Layers: {n_layers}")
        self.vocab_size = len(self.tokenizer) if hasattr(self.tokenizer, "__len__") else "?"

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 0.0,
        stop_tokens: Optional[Sequence[int]] = None,
        seed: Optional[int] = 0,
        verbose: bool = False,
    ) -> dict:
        """Run generation with explicit, receipt-bindable settings."""
        prompt_tokens = self.tokenizer.encode(prompt)
        n_prompt = len(prompt_tokens)

        if seed is not None:
            mx.random.seed(seed)

        sampler = make_sampler(temp=temperature, top_p=top_p)
        explicit_stops = set(int(token) for token in (stop_tokens or []))

        chunks = []
        n_output = 0
        finish_reason = "length"
        peak_memory_gb = 0.0
        t0 = time.time()

        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
            max_kv_size=self.max_kv_size,
        ):
            peak_memory_gb = max(peak_memory_gb, float(getattr(response, "peak_memory", 0.0) or 0.0))
            if response.token in explicit_stops:
                finish_reason = "stop"
                break
            chunks.append(response.text)
            n_output = response.generation_tokens
            if response.finish_reason is not None:
                finish_reason = response.finish_reason

        elapsed = time.time() - t0
        output_text = "".join(chunks)

        if verbose:
            print(output_text)

        return {
            "text": output_text,
            "prompt_tokens": n_prompt,
            "output_tokens": n_output,
            "total_tokens": n_prompt + n_output,
            "tokens_per_sec": n_output / elapsed if elapsed > 0 else 0,
            "time_seconds": elapsed,
            "finish_reason": finish_reason,
            "peak_memory_gb": peak_memory_gb or None,
            "generation_config": {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stop_tokens": sorted(explicit_stops),
                "seed": seed,
                "max_kv_size": self.max_kv_size,
            },
        }

    def benchmark(self, prompt: str, max_tokens: int = 256, n_runs: int = 3) -> dict:
        results = [
            self.generate(prompt, max_tokens=max_tokens, temperature=0.0, seed=0)
            for _ in range(n_runs)
        ]
        times = [r["time_seconds"] for r in results]
        tokens = [r["output_tokens"] for r in results]
        tps = [r["tokens_per_sec"] for r in results]
        return {
            "n_runs": n_runs,
            "prompt": prompt[:80] + ("..." if len(prompt) > 80 else ""),
            "mean_time": sum(times) / len(times),
            "p50_time": sorted(times)[len(times) // 2],
            "p95_time": sorted(times)[min(len(times) - 1, int(len(times) * 0.95))],
            "mean_tokens_per_sec": sum(tps) / len(tps),
            "total_output_tokens": sum(tokens),
            "peak_memory_gb": max((r.get("peak_memory_gb") or 0.0) for r in results),
            "sample_output": results[-1]["text"][:200] if results else "",
        }

    def get_model_info(self) -> dict:
        return {
            "path": self.model_path,
            "params": self.params,
            "max_kv_size": self.max_kv_size,
            "vocab_size": self.vocab_size,
        }


def quick_test():
    h = Harness("models/MiniCPM5-1B")
    print(f"\nModel info: {json.dumps(h.get_model_info(), indent=2)}")
    result = h.generate("Hello! What can you help me with today?", max_tokens=100)
    print(
        f"\nGeneration: {result['output_tokens']} tokens in {result['time_seconds']:.2f}s "
        f"({result['tokens_per_sec']:.1f} tok/s)"
    )
    print(f"Output preview: {result['text'][:200]}")


if __name__ == "__main__":
    quick_test()
