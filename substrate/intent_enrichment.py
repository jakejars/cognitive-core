"""
Substrate — Intent Enrichment

From Substrate Spec §3: "The model proposes semantic intent. The runtime
attaches authority, effects, versions, validation, and execution identity."

This module bridges the model-emitted Intent (from tools/intents.py) to the
substrate's enriched execution node.
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .registry import OperationRegistry
from .effects import EffectClass, EffectPolicy
from .event_ledger import EventLedger


@dataclass
class EnrichedIntent:
    """
    Fully enriched execution node.

    The model emits minimal semantic intent. The substrate resolves it
    into this enriched form with all runtime metadata attached.
    """
    operation: str
    """Operation name, resolved against registry."""

    arguments: Dict[str, Any]
    """Canonicalized arguments."""

    effect_class: EffectClass
    """Resolved from registry."""

    effect_policy: EffectPolicy
    """Resolved effect policy."""

    operation_version: str
    """From registry."""

    execution_hash: str
    """Execution identity hash (includes arguments)."""

    structural_hash: str
    """Structural identity hash (for mining/dedup)."""

    timestamp: float
    """When enrichment occurred."""

    required_permissions: List[str] = field(default_factory=list)
    """From registry effect policy."""

    provenance_refs: List[str] = field(default_factory=list)
    """Event IDs this execution depends on."""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["effect_class"] = self.effect_class.value
        return d


class IntentEnricher:
    """
    Enriches model-emitted intents with runtime metadata.

    From Substrate Spec §3.2: The substrate resolves the requested operation
    against a trusted registry and constructs the full executable node.
    """

    def __init__(self, registry: Optional[OperationRegistry] = None,
                 ledger: Optional[EventLedger] = None):
        self.registry = registry or OperationRegistry()
        self.ledger = ledger or EventLedger()

    def enrich(self, operation: str, arguments: Dict[str, Any],
               provenance_refs: Optional[List[str]] = None,
               metadata: Optional[Dict] = None) -> EnrichedIntent:
        """
        Convert model-emitted intent into enriched execution node.

        Args:
            operation: Operation name (from Intent.operation.value)
            arguments: Operation arguments (from Intent.arguments)
            provenance_refs: Optional event IDs this depends on
            metadata: Optional metadata for ledger recording
        """
        # Resolve against registry
        op_info = self.registry.resolve(operation)

        # Compute hashes
        exec_hash = self.registry.execution_hash(operation, arguments)
        struct_hash = self.registry.structural_hash(operation, arguments)

        # Build enriched intent
        enriched = EnrichedIntent(
            operation=operation,
            arguments=arguments,
            effect_class=op_info.effect_class,
            effect_policy=op_info.effect_policy,
            operation_version=op_info.version,
            execution_hash=exec_hash,
            structural_hash=struct_hash,
            timestamp=time.time(),
            required_permissions=op_info.effect_policy.required_permissions,
            provenance_refs=provenance_refs or [],
        )

        # Record in ledger as an event
        self.ledger.record(
            event_type="enriched_intent",
            source="substrate",
            payload=enriched.to_dict(),
            provenance_refs=enriched.provenance_refs,
            effect_class=enriched.effect_class.value,
            metadata=metadata or {},
        )

        return enriched


def quick_test():
    """Demonstrate intent enrichment."""
    from tools.intents import search_intent, answer_intent

    enricher = IntentEnricher()

    print("=== Intent Enrichment ===")

    # Enrich a search intent
    intent = search_intent("MiniCPM long-context configuration")
    enriched = enricher.enrich(intent.operation.value, intent.arguments)

    print(f"\nModel intent: {intent.operation.value}")
    print(f"  arguments: {intent.arguments}")
    print(f"\nEnriched:")
    print(f"  operation:        {enriched.operation}")
    print(f"  effect_class:     {enriched.effect_class.value}")
    print(f"  deterministic:    {enriched.effect_policy.deterministic}")
    print(f"  idempotent:       {enriched.effect_policy.idempotent}")
    print(f"  version:          {enriched.operation_version}")
    print(f"  execution_hash:   {enriched.execution_hash[:20]}...")
    print(f"  structural_hash:  {enriched.structural_hash[:20]}...")

    # Enrich an answer intent
    intent2 = answer_intent("The capital is Paris.", evidence_refs=["evt_..."])
    enriched2 = enricher.enrich(intent2.operation.value, intent2.arguments,
                                 provenance_refs=intent2.evidence_refs)

    print(f"\nAnswer intent:")
    print(f"  operation:   {enriched2.operation}")
    print(f"  effect:      {enriched2.effect_class.value}")
    print(f"  provenance:  {enriched2.provenance_refs}")

    print(f"\nLedger events: {enricher.ledger.count()}")


if __name__ == "__main__":
    quick_test()