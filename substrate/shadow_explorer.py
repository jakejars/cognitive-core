"""
Substrate — Shadow Exploration and Counterfactual Promotion

From Substrate Spec §12.2 (Shadow exploration):
  production retrieval + shadow candidate retrieval + uncertainty-directed exploration
  + temporal held-out shards + periodic counterfactual replay

From Substrate Spec §9.1 (Promotion by gates):
  Candidate procedure → shadow mode → replay → held-out counterfactual A/B
  → effect-sensitive safety checks → promotion threshold → live observation
"""

from __future__ import annotations
import time
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum

from .skill_miner import SkillPattern
from .skill_registry import SkillRegistry, SkillEntry, SkillStatus
from .skill_verifier import SkillVerifier, PromotionResult, Verdict, build_default_pipeline


class ExplorationMode(str, Enum):
    SHADOW = "shadow"  # Record but don't use
    COUNTERFACTUAL = "counterfactual"  # Evaluate offline
    ACTIVE = "active"  # Use in production


@dataclass
class ShadowCandidate:
    """
    A candidate that was evaluated in shadow mode.
    
    From Substrate Spec §12.2:
      For each production query, record shadow candidates that were
      not placed into active context. Offline evaluation asks whether
      those candidates would have improved the result.
    """
    candidate_id: str
    skill_name: str
    query: str
    would_improve: Optional[bool] = None
    production_score: float = 0.0
    shadow_score: float = 0.0
    evaluated_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShadowExplorer:
    """
    Manages shadow-mode exploration of skill candidates.
    
    Records shadow candidates during production queries, then evaluates
    them offline to determine if they would have improved results.
    """
    
    def __init__(self, exploration_rate: float = 0.1):
        self.exploration_rate = exploration_rate
        self._candidates: List[ShadowCandidate] = []
        self._rng = random.Random(42)
    
    def should_explore(self) -> bool:
        """Determine whether to explore a shadow candidate."""
        return self._rng.random() < self.exploration_rate
    
    def record_shadow(self, skill_name: str, query: str,
                      production_score: float, shadow_score: float) -> ShadowCandidate:
        """Record a shadow evaluation."""
        candidate = ShadowCandidate(
            candidate_id=f"shadow_{len(self._candidates):06d}",
            skill_name=skill_name,
            query=query[:100],
            production_score=production_score,
            shadow_score=shadow_score,
            evaluated_at=time.time(),
        )
        self._candidates.append(candidate)
        return candidate
    
    def evaluate_shadows(self, improvement_threshold: float = 0.05) -> List[ShadowCandidate]:
        """
        Evaluate all unevaluated shadow candidates.
        Returns candidates that would have improved results.
        """
        improved = []
        for c in self._candidates:
            if c.would_improve is not None:
                continue
            c.would_improve = (c.shadow_score - c.production_score) > improvement_threshold
            if c.would_improve:
                improved.append(c)
        return improved
    
    def get_improving_candidates(self) -> List[ShadowCandidate]:
        """Get candidates that would have improved results."""
        return [c for c in self._candidates if c.would_improve]
    
    def statistics(self) -> dict:
        total = len(self._candidates)
        evaluated = sum(1 for c in self._candidates if c.would_improve is not None)
        improving = sum(1 for c in self._candidates if c.would_improve)
        return {
            "total_candidates": total,
            "evaluated": evaluated,
            "improving": improving,
            "exploration_rate": self.exploration_rate,
        }


class CounterfactualEvaluator:
    """
    Runs counterfactual A/B evaluation of promoted skills.
    
    From Substrate Spec §9.1:
      shadow mode → replay → held-out counterfactual A/B
      → effect-sensitive safety checks → promotion threshold
    """
    
    def __init__(self, registry: SkillRegistry, verifier: Optional[SkillVerifier] = None):
        self.registry = registry
        self.verifier = verifier or build_default_pipeline(registry)
        self._results: List[Dict] = []
    
    def evaluate_skill(self, skill_name: str,
                       without_fn: Callable[[], float],
                       with_fn: Callable[[], float]) -> Dict:
        """
        Evaluate a skill by comparing performance with and without it.
        
        Args:
            skill_name: Name of the skill to evaluate
            without_fn: Function that runs without the skill, returns a score
            with_fn: Function that runs with the skill, returns a score
            
        Returns:
            Dict with comparison results
        """
        # Run without skill
        without_score = without_fn()
        
        # Run with skill
        with_score = with_fn()
        
        delta = with_score - without_score
        
        result = {
            "skill_name": skill_name,
            "without_score": without_score,
            "with_score": with_score,
            "delta": delta,
            "improves": delta > 0.05,
            "timestamp": time.time(),
        }
        self._results.append(result)
        
        # Update skill registry based on result
        skill = self.registry.get(skill_name)
        if skill:
            if delta > 0.05:
                self.registry.record_success(skill_name)
            elif delta < -0.05:
                self.registry.record_failure(skill_name)
                self.registry.quarantine(skill_name)
        
        return result
    
    def get_results(self) -> List[Dict]:
        return list(self._results)
    
    def statistics(self) -> dict:
        results = self._results
        if not results:
            return {"evaluations": 0}
        improving = sum(1 for r in results if r.get("improves"))
        return {
            "evaluations": len(results),
            "improving": improving,
            "avg_delta": sum(r.get("delta", 0) for r in results) / len(results),
        }


def quick_test():
    """Demonstrate shadow exploration and counterfactual evaluation."""
    from .skill_registry import SkillRegistry
    
    print("=== Shadow Exploration + Counterfactual Evaluation ===\n")
    
    # Shadow explorer
    explorer = ShadowExplorer(exploration_rate=0.5)
    
    for i in range(10):
        if explorer.should_explore():
            explorer.record_shadow(
                skill_name="test_skill",
                query=f"query_{i}",
                production_score=0.7,
                shadow_score=0.7 + (i / 100),
            )
    
    improved = explorer.evaluate_shadows()
    print(f"Shadow explorer:")
    print(f"  Candidates: {explorer.statistics()['total_candidates']}")
    print(f"  Improving:  {len(improved)}")
    
    # Counterfactual evaluator
    registry = SkillRegistry()
    registry.register(SkillEntry(name="test_skill", status=SkillStatus.SHADOW))
    evaluator = CounterfactualEvaluator(registry)
    
    result = evaluator.evaluate_skill(
        "test_skill",
        without_fn=lambda: 0.65,
        with_fn=lambda: 0.82,
    )
    print(f"\nCounterfactual evaluation:")
    print(f"  Without: {result['without_score']:.2f}")
    print(f"  With:    {result['with_score']:.2f}")
    print(f"  Delta:   {result['delta']:+.2f}")
    print(f"  Improves: {'✅' if result['improves'] else '❌'}")
    
    skill = registry.get("test_skill")
    print(f"  Skill status: {skill.status.value}")


if __name__ == "__main__":
    quick_test()