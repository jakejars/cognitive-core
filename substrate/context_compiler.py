"""
Substrate — Context Compiler

From Substrate Spec §20, §22. Assembles the active cognitive frontier
from available memory, evidence, and state.

The context compiler is the bridge between the substrate's structured memory
and the neural model's working context window.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
from enum import Enum


@dataclass
class ContextPacket:
    """
    The assembled context packet sent to the neural model.

    From Memory Spec §14: A typed packet, not a flat blob.
    """
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
        """Serialize to a text string for model consumption."""
        parts = ["[CONTEXT PACKET]"]

        if self.goal:
            parts.append(f"Goal: {self.goal}")
        if self.constraints:
            parts.append(f"Constraints: {'; '.join(self.constraints)}")
        if self.recent_dialogue:
            parts.append(f"\nRecent dialogue:\n{self.recent_dialogue}")
        if self.relevant_claims:
            parts.append(f"\nRelevant claims ({len(self.relevant_claims)}):")
            for c in self.relevant_claims[:5]:
                parts.append(f"  - {c.get('claim', str(c))}")
        if self.relevant_evidence:
            parts.append(f"\nEvidence ({len(self.relevant_evidence)} items):")
            for e in self.relevant_evidence[:5]:
                parts.append(f"  - {e.get('content', str(e))}")
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
    """An entry in available memory for context compilation."""
    id: str
    content: str
    entry_type: str  # 'claim', 'evidence', 'skill', 'event', 'observation'
    semantic_relevance: float = 0.0
    freshness: float = 1.0
    confidence: float = 1.0
    provenance: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextCompiler:
    """
    Assembles working context from available memory.

    From Substrate Spec §22:
      1. Hard gates (privacy, permissions, contradiction, taint)
      2. Score relevance
      3. Diversity selection (MMR)
      4. Entropy check
      5. Context packet assembly
    """

    def __init__(self, max_context_tokens: int = 8192):
        self.max_context_tokens = max_context_tokens
        self._memory_store: List[MemoryEntry] = []
        self._hard_gates: List[Callable] = []

    def register_hard_gate(self, gate_fn: Callable[[MemoryEntry], bool]):
        """
        Register a hard gate function.
        Returns True if the entry passes (should be included).
        """
        self._hard_gates.append(gate_fn)

    def store(self, entry: MemoryEntry):
        """Store a memory entry."""
        self._memory_store.append(entry)

    def store_many(self, entries: List[MemoryEntry]):
        """Store multiple entries."""
        self._memory_store.extend(entries)

    def apply_gates(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        """Apply all registered hard gates."""
        if not self._hard_gates:
            return entries
        result = []
        for entry in entries:
            if all(gate(entry) for gate in self._hard_gates):
                result.append(entry)
        return result

    def compute_entropy(self, scores: List[float]) -> float:
        """
        Compute Shannon entropy over retrieval scores.

        From Substrate Spec §19: High entropy → multiple plausible contexts →
        retrieve more / ask / search / verify.
        """
        import math
        if not scores:
            return 0.0
        total = sum(scores)
        if total == 0:
            return 0.0
        probs = [s / total for s in scores]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        # Normalize to 0-1 range
        max_entropy = math.log2(len(scores)) if len(scores) > 1 else 1.0
        return min(entropy / max_entropy, 1.0)

    def compile(self, query: str, k: int = 5) -> ContextPacket:
        """
        Compile a context packet relevant to the given query.

        This is a simple scoring baseline (Substrate Spec §22.2).
        Future versions will add learned reranking, MMR diversity, etc.
        """
        # Score all entries by simple keyword overlap
        scored = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for entry in self._memory_store:
            # Apply hard gates
            if self._hard_gates and not all(g(entry) for g in self._hard_gates):
                continue

            # Simple relevance: word overlap
            content_lower = entry.content.lower()
            overlap = sum(1 for w in query_words if w in content_lower)
            relevance = overlap / max(len(query_words), 1)

            # Combine with freshness and confidence
            score = (0.5 * relevance +
                     0.3 * entry.freshness +
                     0.2 * entry.confidence)
            scored.append((score, entry))

        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        top_k = scored[:k]

        # Compute entropy
        scores = [s for s, _ in scored] if scored else [0.0]
        entropy = self.compute_entropy(scores)

        # Build packet
        packet = ContextPacket(
            retrieval_entropy=round(entropy, 3),
            confidence_summary=round(sum(s[0] for s in top_k) / max(len(top_k), 1), 3) if top_k else 0.0,
        )

        for score, entry in top_k:
            if entry.entry_type == "claim":
                packet.relevant_claims.append({"claim": entry.content, "confidence": entry.confidence})
            elif entry.entry_type == "evidence":
                packet.relevant_evidence.append({"content": entry.content, "source": entry.metadata.get("source", "unknown")})
            elif entry.entry_type == "skill":
                packet.active_skills.append(entry.content)
            elif entry.entry_type == "observation":
                packet.relevant_evidence.append({"content": entry.content, "type": "observation"})

            if entry.provenance:
                packet.provenance_summary.extend(entry.provenance)

        return packet


def quick_test():
    """Demonstrate the context compiler."""
    compiler = ContextCompiler()

    # Register a hard gate: reject entries with low confidence
    compiler.register_hard_gate(lambda e: e.confidence >= 0.3)

    # Store some entries
    compiler.store(MemoryEntry(
        id="c1", content="Paris is the capital of France",
        entry_type="claim", confidence=0.95,
    ))
    compiler.store(MemoryEntry(
        id="c2", content="Jupyter is the largest planet",
        entry_type="claim", confidence=0.9,
    ))
    compiler.store(MemoryEntry(
        id="c3", content="The CPU temperature is 75°C",
        entry_type="observation", confidence=0.5,
    ))
    compiler.store(MemoryEntry(
        id="c4", content="The project language is Python",
        entry_type="claim", confidence=0.2,  # Will be gated out
    ))

    # Compile for a query
    packet = compiler.compile("What is the capital of France?", k=3)
    print("=== Context Packet ===")
    print(packet.serialize())

    print(f"\nRetrieval entropy: {packet.retrieval_entropy:.3f}")
    print(f"Confidence summary: {packet.confidence_summary:.3f}")


if __name__ == "__main__":
    quick_test()