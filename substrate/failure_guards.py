"""
Substrate — Failure-Derived Guards

From Substrate Spec §11:
  Failures are first-class training and procedure-refinement data.
  They reveal missing guards, unsafe reorderings, insufficient preconditions.

Analyzes failed traces to extract guard conditions, preconditions,
and fallback procedures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from collections import Counter

from .trace_capture import ExecutionTrace, TraceNode, NodeType


@dataclass
class GuardCondition:
    """
    A guard condition derived from a failure trace.
    
    From Substrate Spec §11.1:
      failure observation → attributed cause → typed precondition/guard/validator/fallback
    """
    guard_id: str
    operation: str
    condition: str
    failure_pattern: str
    severity: str  # 'error', 'warning', 'info'
    source_trace_ids: List[str] = field(default_factory=list)
    frequency: int = 1
    suggested_fix: str = ""


class FailureAnalyzer:
    """
    Analyzes failed execution traces to extract guard conditions.
    
    From Substrate Spec §11:
      Where possible, convert validated lessons into inspectable substrate state.
    """

    def __init__(self):
        self._guards: Dict[str, GuardCondition] = {}

    def analyze_trace(self, trace: ExecutionTrace) -> List[GuardCondition]:
        """Analyze a failed trace and extract guard conditions."""
        guards = []
        for node in trace.get_sequence():
            if node.success:
                continue

            # Determine failure pattern
            pattern = self._classify_failure(node, trace)
            if not pattern:
                continue

            # Generate guard condition
            guard = GuardCondition(
                guard_id=f"guard_{node.node_id}",
                operation=node.operation,
                condition=self._derive_condition(node, pattern),
                failure_pattern=pattern,
                severity=self._classify_severity(node, pattern),
                source_trace_ids=[trace.trace_id],
                suggested_fix=self._suggest_fix(node, pattern),
            )
            guards.append(guard)

            # Deduplicate by condition
            key = f"{node.operation}:{guard.condition}"
            if key in self._guards:
                self._guards[key].frequency += 1
                if trace.trace_id not in self._guards[key].source_trace_ids:
                    self._guards[key].source_trace_ids.append(trace.trace_id)
            else:
                self._guards[key] = guard

        return guards

    def _classify_failure(self, node: TraceNode, trace: ExecutionTrace) -> Optional[str]:
        """Classify the type of failure."""
        error = (node.error or "").lower()
        result = (node.result or "").lower()

        if "timeout" in error or "timed out" in error:
            return "timeout"
        if "permission" in error or "denied" in error:
            return "permission_denied"
        if "not found" in error or "missing" in error:
            return "missing_resource"
        if "invalid" in error:
            return "invalid_input"
        if not node.success and not node.error:
            return "operation_failed"
        return None

    def _derive_condition(self, node: TraceNode, pattern: str) -> str:
        """Derive a human-readable guard condition."""
        conditions = {
            "timeout": f"Operation '{node.operation}' must complete within timeout",
            "permission_denied": f"Operation '{node.operation}' requires permission check before execution",
            "missing_resource": f"Required resource for '{node.operation}' must exist before invocation",
            "invalid_input": f"Input to '{node.operation}' must be validated before execution",
            "operation_failed": f"Operation '{node.operation}' should have a fallback on failure",
        }
        return conditions.get(pattern, f"Unknown failure in '{node.operation}'")

    def _classify_severity(self, node: TraceNode, pattern: str) -> str:
        """Classify the severity of a failure."""
        severe = {"timeout", "permission_denied"}
        if pattern in severe:
            return "error"
        if node.operation in ("verify", "validate"):
            return "warning"
        return "info"

    def _suggest_fix(self, node: TraceNode, pattern: str) -> str:
        """Suggest a fix for the failure pattern."""
        fixes = {
            "timeout": "Add timeout parameter with retry logic",
            "permission_denied": "Add permission check gate before operation",
            "missing_resource": "Add precondition check and resource initialization",
            "invalid_input": "Add input schema validation before operation",
            "operation_failed": "Add try-catch with fallback to model reasoning",
        }
        return fixes.get(pattern, "Review operation for error handling")

    def get_guards(self) -> List[GuardCondition]:
        return list(self._guards.values())

    def statistics(self) -> dict:
        return {
            "total_guards": len(self._guards),
            "by_severity": dict(Counter(g.severity for g in self._guards.values())),
            "by_pattern": dict(Counter(g.failure_pattern for g in self._guards.values())),
        }


def quick_test():
    """Demonstrate failure analysis."""
    from .trace_capture import TraceCapture, NodeType

    tc = TraceCapture()

    # Simulate a failed trace
    tc.start_trace(task_id="failed_task")
    n1 = tc.record_node(NodeType.INTENT, "tool_call", {"tool": "read_file", "path": "/secret/data"},
                       effect_class="READ_LOCAL")
    n2 = tc.record_node(NodeType.RESULT, "tool_result", {"error": "Permission denied"},
                       parent_ids=[n1.node_id], success=False, error="Permission denied",
                       duration_ms=500.0)
    tc.end_trace(success=False)

    # Simulate a successful trace
    tc.start_trace(task_id="successful_task")
    n1 = tc.record_node(NodeType.INTENT, "search", {"query": "hello"}, effect_class="SEARCH")
    n2 = tc.record_node(NodeType.RESULT, "search_result", {"found": True},
                       parent_ids=[n1.node_id], duration_ms=100.0)
    tc.end_trace(success=True)

    # Analyze
    analyzer = FailureAnalyzer()
    for trace in tc.get_traces():
        if not trace.success:
            guards = analyzer.analyze_trace(trace)
            for g in guards:
                print(f"Guard: [{g.severity}] {g.condition}")
                print(f"  Pattern: {g.failure_pattern}")
                print(f"  Fix: {g.suggested_fix}")

    print(f"\nStats: {analyzer.statistics()}")


if __name__ == "__main__":
    quick_test()