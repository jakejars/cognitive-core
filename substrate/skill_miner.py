"""
Substrate — Skill Miner

From Substrate Spec §8 (Procedural Cortex):
  Execution traces → canonical trace/DAG representation
  → resonance/structural clustering → candidate procedure
  → derive typed interface → attach effects/permissions/failures
  → shadow replay → counterfactual held-out gauntlet → promote/quarantine/reject

This module mines repeated patterns from execution traces to form candidate skills.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict

from .trace_capture import TraceNode, ExecutionTrace, TraceCapture, NodeType


@dataclass
class SkillPattern:
    """
    A mined skill pattern — a repeated sequence of operations.

    From Substrate Spec §10 (Skill contract):
      name, typed_inputs, typed_outputs, preconditions, postconditions,
      effects, permissions, failure_modes
    """
    pattern_id: str
    """Content-addressed ID."""

    operation_sequence: List[str]
    """Sequence of operation names, e.g. ['search', 'verify', 'answer']."""

    node_types: List[str]
    """Corresponding node types."""

    frequency: int = 0
    """Number of times this pattern appears across traces."""

    avg_duration_ms: float = 0.0
    """Average duration of the pattern."""

    success_rate: float = 1.0
    """Fraction of times the pattern succeeded."""

    input_keys: List[str] = field(default_factory=list)
    """Inferred input parameter names."""

    output_keys: List[str] = field(default_factory=list)
    """Inferred output parameter names."""

    effects: List[str] = field(default_factory=list)
    """Inferred effect classes."""

    source_trace_ids: List[str] = field(default_factory=list)
    """Traces where this pattern was found."""

    def to_dict(self) -> dict:
        return asdict(self)


class SkillMiner:
    """
    Mines repeated patterns from execution traces.

    Implements the contiguous-sequence mining approach from Substrate Spec §8.
    """

    def __init__(self, min_frequency: int = 2, min_pattern_length: int = 2):
        self.min_frequency = min_frequency
        self.min_pattern_length = min_pattern_length
        self._patterns: Dict[str, SkillPattern] = {}

    def _node_signature(self, node: TraceNode) -> str:
        """Create a signature for sequence matching (ignores argument values)."""
        return f"{node.node_type.value}:{node.operation}"

    def _extract_patterns_from_sequence(self, seq: List[TraceNode],
                                         trace_id: str) -> Dict[str, int]:
        """Extract all contiguous subsequences from a single trace."""
        signatures = [self._node_signature(n) for n in seq]
        pattern_counts: Dict[str, int] = {}

        # Extract all contiguous subsequences of min_pattern_length or more
        for length in range(self.min_pattern_length, len(signatures) + 1):
            for start in range(0, len(signatures) - length + 1):
                subseq = signatures[start:start + length]
                pattern_key = "→".join(subseq)

                # Build a content-addressed ID
                pattern_id = f"pat_{hashlib.sha256(pattern_key.encode()).hexdigest()[:16]}"

                if pattern_id not in pattern_counts:
                    # Gather metadata
                    ops = [n.operation for n in seq[start:start + length]]
                    types = [n.node_type.value for n in seq[start:start + length]]
                    durations = [n.duration_ms for n in seq[start:start + length]]
                    successes = [n.success for n in seq[start:start + length]]

                    # Infer inputs/outputs from arguments
                    input_keys = set()
                    output_keys = set()
                    effects = set()
                    for n in seq[start:start + length]:
                        input_keys.update(n.arguments.keys())
                        if n.result:
                            output_keys.add("result")
                        effects.add(n.effect_class)

                    pattern = SkillPattern(
                        pattern_id=pattern_id,
                        operation_sequence=ops,
                        node_types=types,
                        frequency=1,
                        avg_duration_ms=sum(durations) / len(durations) if durations else 0,
                        success_rate=sum(1 for s in successes if s) / len(successes) if successes else 1.0,
                        input_keys=sorted(input_keys),
                        output_keys=sorted(output_keys),
                        effects=sorted(effects),
                        source_trace_ids=[trace_id],
                    )
                    self._patterns[pattern_id] = pattern
                    pattern_counts[pattern_id] = 1
                else:
                    pattern_counts[pattern_id] += 1

        return pattern_counts

    def mine(self, traces: List[ExecutionTrace]) -> List[SkillPattern]:
        """
        Mine patterns from a list of execution traces.

        Returns all patterns that meet min_frequency.
        """
        # Reset
        self._patterns = {}
        trace_pattern_counts: List[Dict[str, int]] = []

        # Extract patterns from each trace
        for trace in traces:
            seq = trace.get_sequence()
            if len(seq) < self.min_pattern_length:
                continue
            counts = self._extract_patterns_from_sequence(seq, trace.trace_id)
            trace_pattern_counts.append(counts)

        # Count pattern frequencies across traces
        pattern_trace_count: Dict[str, int] = defaultdict(int)
        for counts in trace_pattern_counts:
            for pid in counts:
                pattern_trace_count[pid] += 1

        # Filter by min_frequency
        frequent_patterns = []
        for pid, count in pattern_trace_count.items():
            if count >= self.min_frequency:
                pattern = self._patterns[pid]
                pattern.frequency = count
                frequent_patterns.append(pattern)

        # Sort by frequency (descending) and then length (descending)
        frequent_patterns.sort(key=lambda p: (-p.frequency, -len(p.operation_sequence)))

        return frequent_patterns

    def get_patterns(self, min_frequency: int = 1) -> List[SkillPattern]:
        """Get all mined patterns, optionally filtered by frequency."""
        return [p for p in self._patterns.values() if p.frequency >= min_frequency]

    def statistics(self) -> dict:
        return {
            "total_patterns": len(self._patterns),
            "frequent_patterns": len([p for p in self._patterns.values() if p.frequency >= self.min_frequency]),
            "min_frequency": self.min_frequency,
            "min_length": self.min_pattern_length,
        }


def quick_test():
    """Demonstrate skill mining."""
    from .trace_capture import TraceCapture, NodeType

    tc = TraceCapture()

    # Create two similar traces (simulating a "search then verify" pattern)
    for task_id in ["search_1", "search_2", "search_3"]:
        tc.start_trace(task_id=task_id)

        n1 = tc.record_node(NodeType.INTENT, "search", {"query": f"query_{task_id}"},
                           effect_class="SEARCH")
        n2 = tc.record_node(NodeType.ENRICHED_INTENT, "search", {"query": f"query_{task_id}"},
                           parent_ids=[n1.node_id], effect_class="SEARCH")
        n3 = tc.record_node(NodeType.RESULT, "search_result", {"found": True},
                           parent_ids=[n2.node_id], duration_ms=100.0)
        n4 = tc.record_node(NodeType.INTENT, "verify", {"ref": "result_1"},
                           parent_ids=[n3.node_id], effect_class="PURE")
        n5 = tc.record_node(NodeType.RESULT, "verify_result", {"verified": True},
                           parent_ids=[n4.node_id], duration_ms=50.0,
                           result="Verification passed")

        tc.end_trace(success=True)

    # Add a different trace (no verify step)
    tc.start_trace(task_id="simple_search")
    n1 = tc.record_node(NodeType.INTENT, "search", {"query": "simple query"},
                       effect_class="SEARCH")
    n2 = tc.record_node(NodeType.ENRICHED_INTENT, "search", {"query": "simple query"},
                       parent_ids=[n1.node_id], effect_class="SEARCH")
    n3 = tc.record_node(NodeType.RESULT, "search_result", {"found": True},
                       parent_ids=[n2.node_id], duration_ms=80.0)
    tc.end_trace(success=True)

    # Mine patterns
    miner = SkillMiner(min_frequency=2, min_pattern_length=2)
    patterns = miner.mine(tc.get_traces())

    print("=== Skill Miner Demo ===")
    print(f"Total traces: {tc.statistics()['total_traces']}")
    print(f"Patterns found: {len(patterns)}")
    print()

    for p in patterns:
        print(f"Pattern: {p.pattern_id}")
        print(f"  Sequence: {' → '.join(p.operation_sequence)}")
        print(f"  Types:    {' → '.join(p.node_types)}")
        print(f"  Frequency: {p.frequency}x across traces")
        print(f"  Avg duration: {p.avg_duration_ms:.1f}ms")
        print(f"  Success rate: {p.success_rate:.0%}")
        print(f"  Inputs: {p.input_keys}")
        print(f"  Effects: {p.effects}")
        print()

    print(f"Stats: {miner.statistics()}")


if __name__ == "__main__":
    quick_test()