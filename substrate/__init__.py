"""
Cognitive Core Gen-2 — Substrate Runtime

The trusted deterministic substrate beneath the neural executive.
See `docs/specs/COGNITIVE-SUBSTRATE-SPEC-v2.2.md`.

Design principles:
  1. The model proposes semantic intent; the substrate owns execution semantics.
  2. Deterministic, inspectable, auditable.
  3. Dual identity: structural (for mining/clustering) vs execution (for caching/provenance).
  4. Effect-aware: every operation has a known effect class.
  5. Content-addressed: hash-consed Merkle DAG for memory.
"""

from .event_ledger import EventLedger, Event
from .registry import OperationRegistry, OperationInfo
from .effects import EffectClass, EffectPolicy
from .provenance import ProvenanceTracker, ProvenanceNode
from .context_compiler import ContextCompiler, ContextPacket
from .intent_enrichment import IntentEnricher
from .skill_registry import SkillRegistry, SkillEntry

__all__ = [
    "EventLedger", "Event",
    "OperationRegistry", "OperationInfo",
    "EffectClass", "EffectPolicy",
    "ProvenanceTracker", "ProvenanceNode",
    "ContextCompiler", "ContextPacket",
    "IntentEnricher",
    "SkillRegistry", "SkillEntry",
]