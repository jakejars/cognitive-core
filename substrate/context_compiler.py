"""Substrate — Context Compiler.

Assembles the active cognitive frontier from available memory, evidence, and
state. The oracle path intentionally bypasses ranking while preserving the same
ContextPacket serialization used by ordinary retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Callable


@dataclass
class ContextPacket:
    goal: str = ""
    constraints: List[str] = field(default_factory=list)
    recent_dialogue: str = ""
    relevant_claims: List[Dict] = field(default_factory=list)
    relevant_evidence: List[Dict] = field(default_factory=list)
    active_skills: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    tool_state: Dict[str, Any] = field(default_factory=dict)
    side_effect_state: Dict[str, Any] = field(default_factory=dict)
    retrieval_entropy: float = 0.0
    confidence_summary: float = 0.0
    historical_chunks: List[Dict] = field(default_factory=list)
    provenance_summary: List[str] = field(default_factory=list)

    def serialize(self) -> str:
        parts = ["[CONTEXT PACKET]"]
        if self.goal:
            parts.append(f"Goal: {self.goal}")
        if self.constraints:
            parts.append(f"Constraints: {'; '.join(self.constraints)}")
        if self.recent_dialogue:
            parts.append(f"\nRecent dialogue:\n{self.recent_dialogue}")
        if self.relevant_claims:
            parts.append(f"\nRelevant claims ({len(self.relevant_claims)}):")
            for claim in self.relevant_claims:
                parts.append(f"  - {claim.get('claim', str(claim))}")
        if self.relevant_evidence:
            parts.append(f"\nEvidence ({len(self.relevant_evidence)} items):")
            for evidence in self.relevant_evidence:
                parts.append(f"  - {evidence.get('content', str(evidence))}")
        if self.active_skills:
            parts.append(f"\nActive skills: {', '.join(self.active_skills)}")
        if self.open_questions:
            parts.append(f"\nOpen questions: {'; '.join(self.open_questions)}")
        if self.contradictions:
            parts.append(f"\n⚠️  Contradictions: {'; '.join(self.contradictions)}")
        if self.provenance_summary:
            parts.append(f"\nProvenance: {'; '.join(self.provenance_summary)}")
        parts.append("\n[/CONTEXT PACKET]")
        return "\n".join(parts)


class RetrievalMode(str, Enum):
    SEMANTIC_ONLY = "semantic_only"
    DETERMINISTIC_HYBRID = "deterministic_hybrid"
    LEARNED_RERANKER = "learned_reranker"
    HYBRID = "hybrid"


@dataclass
class MemoryEntry:
    id: str
    content: str
    entry_type: str
    semantic_relevance: float = 0.0
    freshness: float = 1.0
    confidence: float = 1.0
    provenance: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextCompiler:
    def __init__(self, max_context_tokens: int = 8192):
        self.max_context_tokens = max_context_tokens
        self._memory_store: List[MemoryEntry] = []
        self._hard_gates: List[Callable] = []

    def register_hard_gate(self, gate_fn: Callable[[MemoryEntry], bool]):
        self._hard_gates.append(gate_fn)

    def store(self, entry: MemoryEntry):
        self._memory_store.append(entry)

    def store_many(self, entries: List[MemoryEntry]):
        self._memory_store.extend(entries)

    def apply_gates(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        if not self._hard_gates:
            return entries
        return [entry for entry in entries if all(gate(entry) for gate in self._hard_gates)]

    def compute_entropy(self, scores: List[float]) -> float:
        import math

        if not scores:
            return 0.0
        total = sum(scores)
        if total == 0:
            return 0.0
        probs = [score / total for score in scores]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(len(scores)) if len(scores) > 1 else 1.0
        return min(entropy / max_entropy, 1.0)

    def _append_entry(self, packet: ContextPacket, entry: MemoryEntry) -> None:
        if entry.entry_type == "claim":
            packet.relevant_claims.append({"claim": entry.content, "confidence": entry.confidence})
        elif entry.entry_type == "skill":
            packet.active_skills.append(entry.content)
        else:
            packet.relevant_evidence.append({
                "content": entry.content,
                "type": entry.entry_type,
                "source": entry.metadata.get("source", "unknown"),
                "record_id": entry.id,
            })
        if entry.provenance:
            packet.provenance_summary.extend(entry.provenance)

    def compile(self, query: str, k: int = 5) -> ContextPacket:
        scored = []
        query_words = set(query.lower().split())
        for entry in self._memory_store:
            if self._hard_gates and not all(gate(entry) for gate in self._hard_gates):
                continue
            content_lower = entry.content.lower()
            overlap = sum(1 for word in query_words if word in content_lower)
            relevance = overlap / max(len(query_words), 1)
            score = 0.5 * relevance + 0.3 * entry.freshness + 0.2 * entry.confidence
            scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_k = scored[:k]
        scores = [score for score, _ in scored] if scored else [0.0]
        packet = ContextPacket(
            retrieval_entropy=round(self.compute_entropy(scores), 3),
            confidence_summary=(
                round(sum(score for score, _ in top_k) / len(top_k), 3) if top_k else 0.0
            ),
        )
        for _, entry in top_k:
            self._append_entry(packet, entry)
        return packet

    def compile_by_ids(self, record_ids: List[str]) -> ContextPacket:
        """Oracle perfect-recall path: expose the whole relevant set by frozen IDs.

        This is intentionally *not* perfect selection. The caller supplies all
        records deemed relevant to the task, including superseded and near-miss
        records, and the model must still reason over them.
        """
        index = {entry.id: entry for entry in self._memory_store}
        missing = [record_id for record_id in record_ids if record_id not in index]
        if missing:
            raise ValueError(f"oracle record IDs not present in memory: {missing}")

        packet = ContextPacket(retrieval_entropy=0.0, confidence_summary=1.0)
        for record_id in record_ids:
            self._append_entry(packet, index[record_id])
        return packet
