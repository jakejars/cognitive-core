"""
Substrate — Provenance Tracker

From Substrate Spec §5, §7. Tracks the dependency graph between events,
claims, decisions, and evidence.

The provenance DAG is hash-consed — identical content produces identical nodes.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set


@dataclass
class ProvenanceNode:
    """
    A node in the provenance DAG.

    Each node represents some piece of evidence, a claim, a decision,
    or an operation result.
    """
    node_id: str
    """Content-addressed ID."""

    node_type: str
    """'evidence', 'claim', 'decision', 'observation', 'skill_result'"""

    content: Dict[str, Any]
    """The node content."""

    parent_ids: List[str] = field(default_factory=list)
    """Parent nodes that this node depends on."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Extensible metadata: confidence, source, timestamp, etc."""

    def to_dict(self) -> dict:
        return asdict(self)


class ProvenanceTracker:
    """
    Content-addressed provenance DAG.

    Tracks dependencies:
        claim → evidence → file version → tool result
        decision → claims → evidence
        skill_result → operation → arguments → dependencies

    From Substrate Spec §7: "One-million-token history can contain enormous
    textual repetition. The DAG should not."
    """

    def __init__(self):
        self._nodes: Dict[str, ProvenanceNode] = {}
        self._by_type: Dict[str, List[str]] = {}

    def _compute_id(self, node_type: str, content: dict, parent_ids: List[str]) -> str:
        raw = json.dumps({
            "type": node_type,
            "content": content,
            "parents": sorted(parent_ids),
        }, sort_keys=True, default=str).encode()
        return f"prov_{hashlib.sha256(raw).hexdigest()[:32]}"

    def record(self, node_type: str, content: Dict[str, Any],
               parent_ids: Optional[List[str]] = None,
               metadata: Optional[Dict] = None) -> ProvenanceNode:
        """Record a provenance node. Returns existing node if content-identical."""
        parent_ids = parent_ids or []
        node_id = self._compute_id(node_type, content, parent_ids)

        if node_id in self._nodes:
            return self._nodes[node_id]

        # Validate parent references
        for pid in parent_ids:
            if pid not in self._nodes:
                raise ValueError(f"Parent node {pid} not found in tracker")

        node = ProvenanceNode(
            node_id=node_id,
            node_type=node_type,
            content=content,
            parent_ids=parent_ids,
            metadata=metadata or {},
        )
        self._nodes[node_id] = node
        self._by_type.setdefault(node_type, []).append(node_id)
        return node

    def get(self, node_id: str) -> Optional[ProvenanceNode]:
        """Retrieve a node by ID."""
        return self._nodes.get(node_id)

    def get_by_type(self, node_type: str) -> List[ProvenanceNode]:
        """Get all nodes of a type."""
        return [self._nodes[nid] for nid in self._by_type.get(node_type, [])]

    def get_closure(self, node_id: str) -> List[ProvenanceNode]:
        """
        Get the full dependency closure for a node (all ancestors).
        From Substrate Spec §13 (Lazy context evaluation).
        """
        visited: Set[str] = set()
        result: List[ProvenanceNode] = []

        def dfs(nid: str):
            if nid in visited:
                return
            visited.add(nid)
            node = self._nodes.get(nid)
            if not node:
                return
            for pid in node.parent_ids:
                dfs(pid)
            result.append(node)

        dfs(node_id)
        return result

    def count(self) -> int:
        return len(self._nodes)

    def all_nodes(self) -> List[ProvenanceNode]:
        return list(self._nodes.values())


def quick_test():
    """Demonstrate the provenance tracker."""
    prov = ProvenanceTracker()

    # Evidence from a tool call
    ev1 = prov.record("evidence", {
        "tool": "file_read",
        "path": "/data/config.json",
        "content_hash": "abc123",
    })
    print(f"Evidence 1: {ev1.node_id}")

    # Evidence from search
    ev2 = prov.record("evidence", {
        "tool": "search",
        "query": "MiniCPM configuration",
        "result_count": 5,
    })
    print(f"Evidence 2: {ev2.node_id}")

    # Claim based on evidence
    claim = prov.record("claim", {
        "claim": "MiniCPM5 supports 131K native context",
        "confidence": 0.85,
    }, parent_ids=[ev1.node_id, ev2.node_id])
    print(f"Claim:     {claim.node_id}")

    # Decision based on claim
    decision = prov.record("decision", {
        "action": "use_native_context",
        "reason": "Native 131K is sufficient for current tasks",
    }, parent_ids=[claim.node_id])
    print(f"Decision:  {decision.node_id}")

    # Closure
    closure = prov.get_closure(decision.node_id)
    print(f"\nDecision closure ({len(closure)} nodes):")
    for node in closure:
        print(f"  [{node.node_type:10s}] {str(node.content)[:60]}")

    # Content-addressing (same evidence → same node)
    ev3 = prov.record("evidence", {
        "tool": "file_read",
        "path": "/data/config.json",
        "content_hash": "abc123",
    })
    print(f"\nContent-addressing: same evidence → same ID: {ev1.node_id == ev3.node_id}")

    print(f"\nTotal nodes: {prov.count()}")


if __name__ == "__main__":
    quick_test()