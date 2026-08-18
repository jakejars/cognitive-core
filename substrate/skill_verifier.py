"""
Substrate — Skill Verifier and Promotion Pipeline

From Substrate Spec §9 (Promotion by gates):
  Candidate procedure → hard validity gates → effect-sensitive safety gates
  → held-out capability gate → reliability gate → Pareto comparison
  → parsimony within near-tie band → promote/quarantine/reject
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum

from .skill_miner import SkillPattern
from .skill_registry import SkillRegistry, SkillEntry, SkillStatus
from .effects import EffectClass, EffectPolicy


class Verdict(str, Enum):
    PROMOTE = "promote"
    QUARANTINE = "quarantine"
    REJECT = "reject"
    SHADOW = "shadow"


@dataclass
class GateResult:
    """Result of a single promotion gate."""
    gate_name: str
    passed: bool
    details: str = ""
    score: float = 0.0


@dataclass
class PromotionResult:
    """Complete result of the promotion pipeline."""
    pattern_id: str
    skill_name: str
    verdict: Verdict
    gate_results: List[GateResult]
    overall_score: float
    details: str = ""


class PromotionGate:
    """A single gate in the promotion pipeline."""
    
    def __init__(self, name: str, gate_fn: Callable[[SkillPattern], GateResult]):
        self.name = name
        self.gate_fn = gate_fn
    
    def evaluate(self, pattern: SkillPattern) -> GateResult:
        return self.gate_fn(pattern)


class SkillVerifier:
    """
    Verifies and promotes mined skills through a gate pipeline.

    From Substrate Spec §9.1:
      1. Hard validity gates
      2. Effect-sensitive safety gates
      3. Held-out capability gate
      4. Reliability gate
      5. Pareto comparison
      6. Parsimony within near-tie band
    """

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self._gates: List[PromotionGate] = []

    def add_gate(self, gate: PromotionGate):
        """Register a promotion gate."""
        self._gates.append(gate)

    def verify(self, pattern: SkillPattern) -> PromotionResult:
        """Run all gates on a pattern and return the promotion decision."""
        gate_results = []
        all_passed = True

        for gate in self._gates:
            result = gate.evaluate(pattern)
            gate_results.append(result)
            if not result.passed:
                all_passed = False

        # Calculate overall score (average of gate scores)
        overall_score = sum(r.score for r in gate_results) / len(gate_results) if gate_results else 0.0

        # Determine verdict
        if all_passed and overall_score >= 0.7:
            verdict = Verdict.PROMOTE
        elif all_passed and overall_score >= 0.4:
            verdict = Verdict.SHADOW
        elif not all_passed:
            verdict = Verdict.REJECT
        else:
            verdict = Verdict.QUARANTINE

        return PromotionResult(
            pattern_id=pattern.pattern_id,
            skill_name=f"skill_{pattern.pattern_id[:8]}",
            verdict=verdict,
            gate_results=gate_results,
            overall_score=overall_score,
            details="; ".join(f"{r.gate_name}: {'✅' if r.passed else '❌'}" for r in gate_results),
        )

    def promote_to_registry(self, pattern: SkillPattern, verdict: Verdict) -> Optional[str]:
        """
        Promote a verified pattern to the skill registry.
        Returns the skill name if promoted, None otherwise.
        """
        if verdict not in (Verdict.PROMOTE, Verdict.SHADOW):
            return None

        skill_name = f"auto_{pattern.pattern_id[:8]}"

        entry = SkillEntry(
            name=skill_name,
            description=f"Auto-mined skill: {' → '.join(pattern.operation_sequence)}",
            typed_inputs={k: "string" for k in pattern.input_keys},
            typed_outputs={k: "string" for k in pattern.output_keys},
            effects=pattern.effects,
            status=SkillStatus.SHADOW if verdict == Verdict.SHADOW else SkillStatus.CANDIDATE,
            confidence=pattern.success_rate,
            success_count=pattern.frequency,
            provenance={"source": "skill_miner", "pattern_id": pattern.pattern_id},
        )

        self.registry.register(entry)
        return skill_name


# ── Built-in Gates ────────────────────────────────────────────────

def min_length_gate(min_length: int = 2) -> PromotionGate:
    """Gate: pattern must have minimum length."""
    def _gate(p: SkillPattern) -> GateResult:
        passed = len(p.operation_sequence) >= min_length
        return GateResult("min_length", passed, 
                         f"Length {len(p.operation_sequence)} >= {min_length}",
                         score=1.0 if passed else 0.0)
    return PromotionGate("min_length", _gate)


def min_frequency_gate(min_freq: int = 2) -> PromotionGate:
    """Gate: pattern must appear in minimum number of traces."""
    def _gate(p: SkillPattern) -> GateResult:
        passed = p.frequency >= min_freq
        return GateResult("min_frequency", passed,
                         f"Frequency {p.frequency} >= {min_freq}",
                         score=min(1.0, p.frequency / min_freq))
    return PromotionGate("min_frequency", _gate)


def success_rate_gate(min_rate: float = 0.7) -> PromotionGate:
    """Gate: pattern must have minimum success rate."""
    def _gate(p: SkillPattern) -> GateResult:
        passed = p.success_rate >= min_rate
        return GateResult("success_rate", passed,
                         f"Success rate {p.success_rate:.0%} >= {min_rate:.0%}",
                         score=p.success_rate)
    return PromotionGate("success_rate", _gate)


def duration_gate(max_duration_ms: float = 5000) -> PromotionGate:
    """Gate: pattern must not be excessively slow."""
    def _gate(p: SkillPattern) -> GateResult:
        passed = p.avg_duration_ms <= max_duration_ms
        score = max(0.0, 1.0 - (p.avg_duration_ms / max_duration_ms))
        return GateResult("duration", passed,
                         f"Duration {p.avg_duration_ms:.1f}ms <= {max_duration_ms}ms",
                         score=score)
    return PromotionGate("duration", _gate)


def build_default_pipeline(registry: SkillRegistry) -> SkillVerifier:
    """Build the recommended default verification pipeline."""
    verifier = SkillVerifier(registry)
    verifier.add_gate(min_length_gate(2))
    verifier.add_gate(min_frequency_gate(2))
    verifier.add_gate(success_rate_gate(0.7))
    verifier.add_gate(duration_gate(5000))
    return verifier


def quick_test():
    """Demonstrate skill verification."""
    from .skill_registry import SkillRegistry
    from .skill_miner import SkillMiner
    from .trace_capture import TraceCapture, NodeType

    # Capture traces
    tc = TraceCapture()
    for i in range(5):
        tc.start_trace(task_id=f"task_{i}")
        n1 = tc.record_node(NodeType.INTENT, "search", {"query": f"query_{i}"}, effect_class="SEARCH")
        n2 = tc.record_node(NodeType.ENRICHED_INTENT, "search", {"query": f"query_{i}"}, parent_ids=[n1.node_id])
        n3 = tc.record_node(NodeType.RESULT, "search_result", {"found": True}, parent_ids=[n2.node_id], duration_ms=100.0)
        tc.end_trace(success=True)

    # Mine patterns
    miner = SkillMiner(min_frequency=2, min_pattern_length=2)
    patterns = miner.mine(tc.get_traces())

    # Verify and promote
    registry = SkillRegistry()
    verifier = build_default_pipeline(registry)

    print("=== Skill Verification Demo ===")
    for p in patterns[:5]:
        result = verifier.verify(p)
        name = verifier.promote_to_registry(p, result.verdict)
        status = "✅" if result.verdict == Verdict.PROMOTE else "⬜" if result.verdict == Verdict.SHADOW else "❌"
        print(f"{status} {result.verdict.value:10s} | score={result.overall_score:.2f} | {' → '.join(p.operation_sequence[:4])}")
        if name:
            registered = registry.get(name)
            if registered:
                print(f"     → Registered as '{name}' (status={registered.status.value})")

    print(f"\nRegistry: {registry.count()} skills, {len(registry.get_by_status(SkillStatus.ACTIVE))} active")


if __name__ == "__main__":
    quick_test()