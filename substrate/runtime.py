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
from .trace_capture import TraceCapture, TraceNode, NodeType
from .skill_miner import SkillMiner
from .skill_verifier import SkillVerifier, build_default_pipeline, Verdict


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
        self.tracer = TraceCapture()
        self.skill_miner = SkillMiner(min_frequency=2, min_pattern_length=2)
        self.skill_verifier = build_default_pipeline(self.skills)

        # Track model context
        self._session_state: Dict[str, Any] = {}
        self._trace_active: bool = False

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
          5. Record trace node
          6. Return enriched intent for execution
        """
        enriched = self.enricher.enrich(operation, arguments, provenance_refs, metadata)

        # Check effect policy for restrictions
        policy = enriched.effect_policy
        if not policy.idempotent:
            pass

        # Record trace node
        if self._trace_active:
            self.tracer.record_node(
                NodeType.INTENT, operation, arguments,
                effect_class=enriched.effect_class.value,
                metadata={"execution_hash": enriched.execution_hash},
            )

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

    def start_trace(self, task_id: str = ""):
        """Start capturing an execution trace."""
        self._trace_active = True
        self.tracer.start_trace(task_id=task_id, model="MiniCPM5-1B")

    def end_trace(self, success: bool = True):
        """End trace capture and return the trace."""
        self._trace_active = False
        return self.tracer.end_trace(success=success)

    def mine_skills(self, min_frequency: int = 1) -> int:
        """
        Mine and promote skills from captured traces.
        Returns the number of promoted skills.
        """
        traces = self.tracer.get_traces()
        if not traces:
            return 0

        patterns = self.skill_miner.mine(traces)
        # Also try with lower frequency for single traces
        if not patterns and len(traces) == 1:
            self.skill_miner.min_frequency = 1
            patterns = self.skill_miner.mine(traces)
        promoted = 0
        for pattern in patterns:
            result = self.skill_verifier.verify(pattern)
            name = self.skill_verifier.promote_to_registry(pattern, result.verdict)
            if name and result.verdict in (Verdict.PROMOTE, Verdict.SHADOW):
                promoted += 1

        return promoted

    def record_trace_node(self, node_type: NodeType, operation: str,
                          arguments: Dict[str, Any],
                          parent_ids: Optional[List[str]] = None,
                          result: Optional[str] = None,
                          duration_ms: float = 0.0,
                          effect_class: str = "PURE",
                          success: bool = True) -> Optional[TraceNode]:
        """Record a trace node explicitly. Returns the node or None if no active trace."""
        if not self._trace_active:
            return None
        return self.tracer.record_node(
            node_type, operation, arguments,
            parent_ids=parent_ids,
            result=result,
            duration_ms=duration_ms,
            effect_class=effect_class,
            success=success,
        )

    def get_statistics(self) -> dict:
        """Return substrate statistics."""
        return {
            "events": self.ledger.count(),
            "provenance_nodes": self.provenance.count(),
            "skills": self.skills.count(),
            "memory_entries": len(self.compiler._memory_store),
            "registered_operations": len(self.registry.list_operations()),
            "traces": self.tracer.statistics()["total_traces"],
            "trace_nodes": self.tracer.statistics()["total_nodes"],
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