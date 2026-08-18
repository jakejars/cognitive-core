"""
Substrate — Resonance, Quality Separation, and Hysteresis

From Substrate Spec §12 (Resonance), §13 (Separate frequency from quality),
and §15 (Hysteresis for continual learning).

Resonance:  A trace/skill has weight w. Reuse reinforces, decay reduces.
Quality:    Kalman filter estimates latent quality from noisy observations.
Hysteresis: Asymmetric lifecycle thresholds — promotion hard, quarantine easy.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ResonanceState:
    """
    Resonance weight for a skill or memory.
    
    From Substrate Spec §12:
      w ← w + Δ (reuse reinforces)
      w ← w(1-λ) (decay per tick)
      w* = Δr/λ (equilibrium)
    """
    item_id: str
    weight: float = 0.5
    reuse_count: int = 0
    last_used: float = 0.0
    decay_rate: float = 0.01  # λ
    reuse_delta: float = 0.1  # Δ
    
    def reinforce(self):
        """Apply reuse reinforcement."""
        self.weight = min(1.0, self.weight + self.reuse_delta)
        self.reuse_count += 1
        self.last_used = time.time()
    
    def decay(self):
        """Apply time-based decay."""
        if self.last_used == 0:
            return
        elapsed = time.time() - self.last_used
        ticks = elapsed / 3600  # 1 tick per hour
        for _ in range(min(int(ticks), 100)):  # Cap at 100 ticks
            self.weight *= (1 - self.decay_rate)
        self.weight = max(0.01, self.weight)
        self.last_used = time.time()
    
    @property
    def equilibrium_weight(self) -> float:
        """Theoretical equilibrium: w* = Δr/λ"""
        if self.decay_rate == 0:
            return 1.0
        r = self.reuse_count / max(time.time() - self.last_used + 1, 1) * 3600
        return min(1.0, self.reuse_delta * r / self.decay_rate)


@dataclass
class KalmanQuality:
    """
    Kalman filter estimate of latent quality.
    
    From Substrate Spec §13.2:
      K = P⁻/(P⁻ + R)  ← Kalman gain
      x = x⁻ + K(z - x⁻)  ← State update
      P = (1 - K)P⁻  ← Covariance update
    """
    estimated_quality: float = 0.5
    covariance: float = 1.0
    process_noise: float = 0.01  # Q
    measurement_noise: float = 0.1  # R
    
    def update(self, observation: float):
        """Update with a new observation (0.0-1.0)."""
        # Predict
        predicted_quality = self.estimated_quality
        predicted_cov = self.covariance + self.process_noise
        
        # Update
        kalman_gain = predicted_cov / (predicted_cov + self.measurement_noise)
        self.estimated_quality = predicted_quality + kalman_gain * (observation - predicted_quality)
        self.covariance = (1 - kalman_gain) * predicted_cov
    
    @property
    def uncertainty(self) -> float:
        """Current uncertainty (standard deviation)."""
        return math.sqrt(self.covariance)


class ResonanceTracker:
    """
    Tracks resonance and quality separately for skills and memories.
    
    From Substrate Spec §13: "Gen-2 should maintain separate signals."
    - Resonance: how often something is used
    - Quality: how good it is (Kalman estimate)
    """
    
    def __init__(self):
        self._resonance: Dict[str, ResonanceState] = {}
        self._quality: Dict[str, KalmanQuality] = {}
    
    def record_use(self, item_id: str, observation: Optional[float] = None):
        """Record a use of an item, optionally with a quality observation."""
        if item_id not in self._resonance:
            self._resonance[item_id] = ResonanceState(item_id=item_id)
            self._quality[item_id] = KalmanQuality()
        
        self._resonance[item_id].reinforce()
        if observation is not None:
            self._quality[item_id].update(observation)
    
    def get_resonance(self, item_id: str) -> Optional[ResonanceState]:
        if item_id in self._resonance:
            self._resonance[item_id].decay()
            return self._resonance[item_id]
        return None
    
    def get_quality(self, item_id: str) -> Optional[KalmanQuality]:
        return self._quality.get(item_id)
    
    def get_combined_score(self, item_id: str) -> float:
        """Combined score: resonance × quality."""
        res = self.get_resonance(item_id)
        qual = self.get_quality(item_id)
        if not res:
            return 0.0
        r = res.weight
        q = qual.estimated_quality if qual else 0.5
        return r * q
    
    def statistics(self) -> dict:
        return {
            "tracked_items": len(self._resonance),
            "avg_resonance": sum(r.weight for r in self._resonance.values()) / max(len(self._resonance), 1),
            "avg_quality": sum(q.estimated_quality for q in self._quality.values()) / max(len(self._quality), 1),
        }


class HysteresisController:
    """
    Asymmetric lifecycle thresholds.
    
    From Substrate Spec §15:
      candidate creation:       cheap
      promotion:                difficult
      quarantine:               easy + reversible
      permanent retirement:     difficult
    
    For high-effect skills: promotion threshold higher, quarantine threshold lower.
    For read-only skills:   promotion may be statistical.
    For irreversible:       promotion requires perfect replay + explicit human policy.
    """
    
    def __init__(self, effect_sensitivity: str = "normal"):
        self.effect_sensitivity = effect_sensitivity
        self._set_thresholds()
    
    def _set_thresholds(self):
        if self.effect_sensitivity == "high":
            self.promotion_threshold = 0.85
            self.quarantine_threshold = 0.3
        elif self.effect_sensitivity == "low":
            self.promotion_threshold = 0.5
            self.quarantine_threshold = 0.1
        else:  # normal
            self.promotion_threshold = 0.7
            self.quarantine_threshold = 0.2
    
    def should_promote(self, quality_score: float, frequency: int) -> Tuple[bool, str]:
        """Determine if a skill should be promoted."""
        if quality_score >= self.promotion_threshold and frequency >= 2:
            return True, f"Quality {quality_score:.2f} >= {self.promotion_threshold}"
        return False, f"Quality {quality_score:.2f} < {self.promotion_threshold}"
    
    def should_quarantine(self, quality_score: float, failure_rate: float) -> Tuple[bool, str]:
        """Determine if a skill should be quarantined."""
        if failure_rate > 0.5 or quality_score < self.quarantine_threshold:
            return True, f"Quality {quality_score:.2f} < {self.quarantine_threshold} or failures {failure_rate:.2f}"
        return False, "Within acceptable range"
    
    def should_retire(self, quality_score: float, age_days: float) -> Tuple[bool, str]:
        """Determine if a skill should be permanently retired."""
        if quality_score < 0.1 and age_days > 30:
            return True, f"Quality {quality_score:.2f} < 0.1 for {age_days:.0f} days"
        return False, "Not eligible for retirement"


def quick_test():
    """Demonstrate resonance, quality, and hysteresis."""
    print("=== Resonance + Quality + Hysteresis ===\n")
    
    # Resonance tracker
    rt = ResonanceTracker()
    for i in range(10):
        rt.record_use("skill_search", observation=0.8 if i < 8 else 0.3)
    rt.record_use("skill_verify", observation=0.9)
    
    print("Resonance:")
    for sid in ["skill_search", "skill_verify"]:
        res = rt.get_resonance(sid)
        qual = rt.get_quality(sid)
        print(f"  {sid}: resonance={res.weight:.2f}, quality={qual.estimated_quality:.2f}, combined={rt.get_combined_score(sid):.2f}")
    
    # Hysteresis controller
    hc = HysteresisController("normal")
    promote, reason = hc.should_promote(0.85, 5)
    print(f"\nHysteresis (normal):")
    print(f"  Promote (q=0.85, freq=5): {'✅' if promote else '❌'} — {reason}")
    
    hc_high = HysteresisController("high")
    promote, reason = hc_high.should_promote(0.8, 5)
    print(f"  High-effect promote (q=0.8, freq=5): {'✅' if promote else '❌'} — {reason}")
    
    quarantine, reason = hc.should_quarantine(0.15, 0.6)
    print(f"  Quarantine (q=0.15, fail=0.6): {'✅' if quarantine else '❌'} — {reason}")
    
    print(f"\nResonance stats: {rt.statistics()}")


if __name__ == "__main__":
    quick_test()