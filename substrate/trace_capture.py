"""
Substrate — Execution Trace Capture

From Substrate Spec §8 (Procedural Cortex):
  Execution traces → canonical trace/DAG representation → resonance/structural clustering
  → candidate procedure → derive typed interface → attach effects/permissions/failures
  → shadow replay → counterfactual held-out gauntlet → promote/quarantine/reject

This module captures the DAG of operations during model-substrate interaction.
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class NodeType(str, Enum):
    INTENT = "intent"
    ENRICHED_INTENT = "enriched_intent"
    TOOL_CALL = "tool_call"
    MODEL_CALL = "model_call"
    RETRIEVAL = "retrieval"
    VERIFICATION = "verification"
    SKILL_CALL = "skill_call"
    RESULT = "result"
    DECISION = "decision"


@dataclass
class TraceNode:
    """A single node in the execution trace DAG."""
    node_id: str
    node_type: NodeType
    operation: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    parent_ids: List[str] = field(default_factory=list)
    children_ids: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    effect_class: str = "PURE"
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def structural_hash(self) -> str:
        """Hash for structural identity (ignoring argument values)."""
        content = {
            "type": self.node_type.value,
            "operation": self.operation,
        }
        raw = json.dumps(content, sort_keys=True).encode()
        return f"struct_{hashlib.sha256(raw).hexdigest()[:16]}"


@dataclass
class ExecutionTrace:
    """A complete execution trace (DAG of operations)."""
    trace_id: str
    nodes: Dict[str, TraceNode] = field(default_factory=dict)
    root_ids: List[str] = field(default_factory=list)
    created_at: float = 0.0
    task_id: str = ""
    model: str = ""
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: TraceNode):
        self.nodes[node.node_id] = node

    def get_sequence(self) -> List[TraceNode]:
        """Get nodes in chronological order (topological sort)."""
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.timestamp)
        return sorted_nodes

    def get_subgraph(self, root_id: str) -> List[TraceNode]:
        """Get all nodes reachable from root_id."""
        result = []
        visited = set()

        def dfs(nid: str):
            if nid in visited or nid not in self.nodes:
                return
            visited.add(nid)
            node = self.nodes[nid]
            result.append(node)
            for cid in node.children_ids:
                dfs(cid)

        dfs(root_id)
        return result


class TraceCapture:
    """
    Captures execution traces from model-substrate interaction.

    Records every operation as a node in a DAG, preserving the full
    execution context for later skill mining.
    """

    def __init__(self):
        self._traces: List[ExecutionTrace] = []
        self._current_trace: Optional[ExecutionTrace] = None
        self._node_counter: int = 0

    def start_trace(self, task_id: str = "", model: str = "MiniCPM5-1B",
                    metadata: Optional[Dict] = None) -> str:
        """Start a new execution trace."""
        trace_id = f"trace_{hashlib.sha256(f'{time.time()}{task_id}'.encode()).hexdigest()[:16]}"
        self._current_trace = ExecutionTrace(
            trace_id=trace_id,
            created_at=time.time(),
            task_id=task_id,
            model=model,
            metadata=metadata or {},
        )
        return trace_id

    def end_trace(self, success: bool = True) -> ExecutionTrace:
        """End the current trace and return it."""
        if self._current_trace:
            self._current_trace.success = success
            self._traces.append(self._current_trace)
            trace = self._current_trace
            self._current_trace = None
            return trace
        raise ValueError("No active trace")

    def record_node(self, node_type: NodeType, operation: str,
                    arguments: Dict[str, Any],
                    parent_ids: Optional[List[str]] = None,
                    result: Optional[str] = None,
                    duration_ms: float = 0.0,
                    effect_class: str = "PURE",
                    success: bool = True,
                    error: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> TraceNode:
        """Record a node in the current trace."""
        if not self._current_trace:
            raise ValueError("No active trace. Call start_trace() first.")

        self._node_counter += 1
        node_id = f"node_{self._node_counter:06d}"

        node = TraceNode(
            node_id=node_id,
            node_type=node_type,
            operation=operation,
            arguments=arguments,
            result=result,
            parent_ids=parent_ids or [],
            timestamp=time.time(),
            duration_ms=duration_ms,
            effect_class=effect_class,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        # Update parent-child relationships
        for pid in node.parent_ids:
            parent = self._current_trace.nodes.get(pid)
            if parent:
                parent.children_ids.append(node_id)

        # If no parents, add as root
        if not parent_ids:
            self._current_trace.root_ids.append(node_id)

        self._current_trace.add_node(node)
        return node

    def get_traces(self, task_id: Optional[str] = None) -> List[ExecutionTrace]:
        """Get all traces, optionally filtered by task_id."""
        if task_id:
            return [t for t in self._traces if t.task_id == task_id]
        return list(self._traces)

    def get_all_sequences(self) -> List[List[TraceNode]]:
        """Get all node sequences for mining."""
        return [t.get_sequence() for t in self._traces]

    def statistics(self) -> dict:
        return {
            "total_traces": len(self._traces),
            "total_nodes": sum(len(t.nodes) for t in self._traces),
            "active_trace": self._current_trace is not None,
        }


def quick_test():
    """Demonstrate trace capture."""
    tc = TraceCapture()

    # Start a trace for a search task
    tc.start_trace(task_id="search_test", model="MiniCPM5-1B")

    # Record nodes
    intent = tc.record_node(
        NodeType.INTENT, "search",
        {"query": "MiniCPM long-context configuration"},
        effect_class="SEARCH",
    )
    print(f"1. Intent: {intent.node_id}")

    enriched = tc.record_node(
        NodeType.ENRICHED_INTENT, "search",
        {"query": "MiniCPM long-context configuration", "effect_class": "SEARCH"},
        parent_ids=[intent.node_id],
        effect_class="SEARCH",
    )
    print(f"2. Enriched: {enriched.node_id}")

    result = tc.record_node(
        NodeType.RESULT, "search_result",
        {"found": True, "count": 5},
        parent_ids=[enriched.node_id],
        result="Found 5 results about MiniCPM long-context",
        duration_ms=150.0,
    )
    print(f"3. Result: {result.node_id}")

    # End trace
    trace = tc.end_trace(success=True)
    print(f"\nTrace: {trace.trace_id}")
    print(f"  Nodes: {len(trace.nodes)}")
    print(f"  Roots: {trace.root_ids}")

    # Get sequence
    seq = trace.get_sequence()
    print(f"\n  Sequence:")
    for node in seq:
        print(f"    {node.node_type.value:20s} {node.operation:20s} → {str(node.result)[:50] if node.result else '...'}")

    print(f"\nStats: {tc.statistics()}")


if __name__ == "__main__":
    quick_test()