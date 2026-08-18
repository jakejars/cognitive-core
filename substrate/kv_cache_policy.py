"""
Substrate — Bounded KV-Cache Policy

From Memory Spec §16:
  BF16 hot KV only
  INT8 bounded historic KV cache
  4-bit bounded historic KV cache
  compressed latent memory
  recompute-on-demand chunks
  hybrid cache with eviction

The target metric is:
  effective held-out context capability per resident GB and per unit latency
  not maximum advertised context or maximum cached tokens.

For MiniCPM5-1B (24 layers, 2 KV heads, 128 head_dim):
  Full 131K BF16 KV cache: ~24 GiB
  Full 131K 4-bit KV cache: ~6 GiB
  Bounded 8K 4-bit KV cache: ~0.4 GiB ← practical default
"""

from dataclasses import dataclass
from typing import Optional


# MiniCPM5-1B KV parameters
MINICPM_KV_PARAMS = {
    "layers": 24,
    "kv_heads": 2,
    "head_dim": 128,
}


def kv_cache_bytes(tokens: int, layers: int = 24, kv_heads: int = 2,
                   head_dim: int = 128, bits: int = 16) -> int:
    """
    Calculate KV cache size in bytes.
    
    Formula: tokens × layers × 2(K,V) × kv_heads × head_dim × (bits/8)
    """
    bytes_per_element = bits / 8
    return int(tokens * layers * 2 * kv_heads * head_dim * bytes_per_element)


def kv_cache_gib(tokens: int, **kwargs) -> float:
    """KV cache size in GiB."""
    return kv_cache_bytes(tokens, **kwargs) / (1024 ** 3)


@dataclass
class KVCachePolicy:
    """
    Policy for KV cache size management.
    
    From Memory Spec §16:
      - Hot KV: full precision, bounded size
      - Historic KV: compressed/quantized, bounded size
      - Cold: recompute on demand or evicted
    """
    hot_cache_tokens: int = 8192
    hot_cache_bits: int = 16  # BF16
    
    historic_cache_tokens: int = 32768
    historic_cache_bits: int = 4  # 4-bit quantized
    
    max_total_gib: float = 2.0  # Max total KV cache in GiB
    
    def hot_cache_gib(self) -> float:
        """Size of hot KV cache."""
        return kv_cache_gib(self.hot_cache_tokens, bits=self.hot_cache_bits)
    
    def historic_cache_gib(self) -> float:
        """Size of historic KV cache."""
        return kv_cache_gib(self.historic_cache_tokens, bits=self.historic_cache_bits)
    
    def total_gib(self) -> float:
        return self.hot_cache_gib() + self.historic_cache_gib()
    
    def is_valid(self) -> bool:
        return self.total_gib() <= self.max_total_gib
    
    def suggest(self) -> str:
        """Suggest a KV cache configuration."""
        configs = [
            ("8K hot BF16 + 32K historic 4-bit", 8192, 16, 32768, 4),
            ("4K hot BF16 + 16K historic 4-bit", 4096, 16, 16384, 4),
            ("16K hot 4-bit only", 16384, 4, 0, 4),
            ("8K hot 4-bit only", 8192, 4, 0, 4),
        ]
        
        results = []
        for name, hot_t, hot_b, hist_t, hist_b in configs:
            hot = kv_cache_gib(hot_t, bits=hot_b)
            hist = kv_cache_gib(hist_t, bits=hist_b)
            total = hot + hist
            ok = "✅" if total <= self.max_total_gib else "❌"
            results.append(f"  {ok} {name}: {hot:.2f}GiB + {hist:.2f}GiB = {total:.2f}GiB")
        
        return "\n".join(results)


def quick_test():
    """Demonstrate KV cache policy."""
    print("=== Bounded KV-Cache Policy ===\n")
    print(f"MiniCPM5-1B KV params: {MINICPM_KV_PARAMS}")
    print(f"  Full 131K BF16:  {kv_cache_gib(131072, bits=16):.1f} GiB")
    print(f"  Full 131K 4-bit: {kv_cache_gib(131072, bits=4):.1f} GiB")
    print(f"  Full 131K INT8:  {kv_cache_gib(131072, bits=8):.1f} GiB")
    print()
    
    policy = KVCachePolicy(max_total_gib=2.0)
    print(f"Default policy (max {policy.max_total_gib} GiB):")
    print(f"  Hot cache:      {policy.hot_cache_gib():.2f} GiB ({policy.hot_cache_tokens} tok @ {policy.hot_cache_bits}bit)")
    print(f"  Historic cache: {policy.historic_cache_gib():.2f} GiB ({policy.historic_cache_tokens} tok @ {policy.historic_cache_bits}bit)")
    print(f"  Total:          {policy.total_gib():.2f} GiB {'✅' if policy.is_valid() else '❌'}")
    print()
    print("Possible configurations:")
    print(policy.suggest())


if __name__ == "__main__":
    quick_test()