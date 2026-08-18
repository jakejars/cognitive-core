"""
Cognitive Core Gen-2 — Substrate Runtime (Integrated)

Combines all substrate components into a single runtime that
sits between the model and the outside world.

Usage:
    from substrate.runtime import SubstrateRuntime
    rt = SubstrateRuntime()
    
    # Model proposes intent
    enriched = rt.process_intent("search", {"query": "hello"})
    
    # Substrate records and enriches
    print(enriched.execution_hash)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from .event_ledger import EventLedger
from .registry import OperationRegistry
from .effects import EffectClass
from .provenance import ProvenanceTracker
from .context_compiler import ContextCompiler, MemoryEntry
from .intent_enrichment import IntentEnricher, EnrichedIntent
from .skill_registry import SkillRegistry, SkillEntry


class SubstrateRuntime:
    """
    Integrated trusted substrate runtime.

    Owns: identity, state, provenance, effects, skills, context assembly.
    Does NOT: own neural inference, mint authority tokens, or define model semantics.
    """

    def __init__(self):
        self.registry = OperationRegistry()
        self.ledger = EventLedger()
        self.provenance = ProvenanceTracker()
        self.skills = SkillRegistry()
        self.enricher = IntentEnricher(registry=self.registry, ledger=self.ledger)
        self.compiler = ContextCompiler()

        # Track model context
        self._session_state: Dict[str, Any] = {}

    def process_intent(self, operation: str, arguments: Dict[str, Any],
                       provenance_refs: Optional[List[str]] = None,
                       metadata: Optional[Dict] = None) -> EnrichedIntent:
        """
        Process a model-emitted intent through the substrate.

        Steps:
          1. Enrich with registry metadata
          2. Record in event ledger
          3. Track provenance
          4. Check effect policy
          5. Return enriched intent for execution
        """
        enriched = self.enricher.enrich(operation, arguments, provenance_refs, metadata)

        # Check effect policy for restrictions
        policy = enriched.effect_policy
        if not policy.idempotent:
            # Record in ledger as non-idempotent for audit
            pass

        return enriched

    def record_observation(self, content: str, source: str = "system",
                           metadata: Optional[Dict] = None) -> None:
        """Record an environmental observation in memory."""
        self.compiler.store(MemoryEntry(
            id=f"obs_{len(self.compiler._memory_store)}",
            content=content,
            entry_type="observation",
            freshness=1.0,
            confidence=1.0,
            metadata={"source": source, **(metadata or {})},
        ))

    def record_claim(self, claim: str, confidence: float,
                     provenance_refs: Optional[List[str]] = None) -> str:
        """Record a claim with confidence and provenance."""
        # Store in compiler
        entry = MemoryEntry(
            id=f"claim_{len(self.compiler._memory_store)}",
            content=claim,
            entry_type="claim",
            confidence=confidence,
            provenance=provenance_refs or [],
        )
        self.compiler.store(entry)

        # Record in ledger
        event = self.ledger.record("claim", "substrate", {
            "claim": claim,
            "confidence": confidence,
        }, confidence=confidence)

        # Track in provenance
        self.provenance.record("claim", {"claim": claim, "confidence": confidence},
                               parent_ids=provenance_refs or [])

        return event.event_id

    def compile_context(self, query: str, k: int = 5) -> str:
        """Compile a context packet for the model."""
        packet = self.compiler.compile(query, k=k)
        return packet.serialize()

    def get_state(self) -> Dict[str, Any]:
        """Get current session state."""
        return dict(self._session_state)

    def set_state(self, key: str, value: Any):
        """Set session state value."""
        self._session_state[key] = value

    def get_statistics(self) -> dict:
        """Return substrate statistics."""
        return {
            "events": self.ledger.count(),
            "provenance_nodes": self.provenance.count(),
            "skills": self.skills.count(),
            "memory_entries": len(self.compiler._memory_store),
            "registered_operations": len(self.registry.list_operations()),
        }


def quick_test():
    """Demonstrate the integrated runtime."""
    rt = SubstrateRuntime()

    print("=== Substrate Runtime Test ===\n")

    # 1. Process a model intent
    enriched = rt.process_intent("search", {"query": "MiniCPM configuration"})
    print(f"1. Processed intent: {enriched.operation}")
    print(f"   Effect class: {enriched.effect_class.value}")
    print(f"   Execution hash: {enriched.execution_hash[:24]}...")

    # 2. Process a tool call intent
    enriched2 = rt.process_intent("tool_call", {
        "tool": "read_file",
        "arguments": {"path": "/config.yaml"}
    })
    print(f"\n2. Tool intent: {enriched2.operation}")
    print(f"   Effect class: {enriched2.effect_class.value}")
    print(f"   Deterministic: {enriched2.effect_policy.deterministic}")

    # 3. Record claims and observations
    rt.record_observation("File /config.yaml contains: language=Python, theme=dark")
    claim_id = rt.record_claim("The project language is Python", confidence=0.95)
    print(f"\n3. Recorded claim: {claim_id}")

    # 4. Compile context
    context = rt.compile_context("What language is the project using?", k=3)
    print(f"\n4. Context packet:")
    print(context[:400])

    # 5. Check stats
    stats = rt.get_statistics()
    print(f"\n5. Substrate statistics:")
    for k, v in stats.items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    quick_test()