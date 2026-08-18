"""
Substrate — Event Ledger

Append-only record of all operations. From Substrate Spec §23:
  - RAW TRACE: append-only observation/log
  - EVENT: structured, append-only
  - CLAIM: requires evidence/confidence state
  - DECISION: requires provenance

This module implements the EVENT and CLAIM levels with content-addressing.
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Event:
    """
    A single recorded event in the ledger.

    Events are immutable once committed.
    """
    event_id: str
    """Unique content-addressed identifier: sha256(type + timestamp + payload)."""

    event_type: str
    """'trace', 'event', 'claim', 'decision', 'observation'"""

    timestamp: float
    """Unix timestamp of event creation."""

    source: str
    """'model', 'substrate', 'tool', 'user', 'system'"""

    payload: Dict[str, Any]
    """Event-specific data."""

    provenance_refs: List[str] = field(default_factory=list)
    """Event IDs that this event depends on or references."""

    effect_class: str = "PURE"
    """Effect class at the time of recording."""

    confidence: Optional[float] = None
    """Optional confidence score (0.0-1.0) for claims/decisions."""

    supersedes: Optional[str] = None
    """If set, this event supersedes the referenced event ID."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Extensible metadata."""

    def compute_id(self) -> str:
        """Compute content-addressed ID."""
        content = {
            "type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload,
            "provenance_refs": sorted(self.provenance_refs),
            "supersedes": self.supersedes,
        }
        raw = json.dumps(content, sort_keys=True, default=str).encode()
        return f"evt_{hashlib.sha256(raw).hexdigest()[:32]}"

    def to_dict(self) -> dict:
        return asdict(self)


class EventLedger:
    """
    Append-only event ledger with content-addressed lookup.

    From Substrate Spec §23:
    - Supports raw traces, structured events, claims, and decisions
    - Events are immutable once committed
    - Supports supersession chains
    """

    def __init__(self):
        self._events: Dict[str, Event] = {}
        self._by_type: Dict[str, List[str]] = {}
        self._by_source: Dict[str, List[str]] = {}
        self._superseded_by: Dict[str, str] = {}
        """Maps event_id → event_id that supersedes it (for forward traversal)."""

    def record(self, event_type: str, source: str, payload: Dict[str, Any],
               provenance_refs: Optional[List[str]] = None,
               effect_class: str = "PURE",
               confidence: Optional[float] = None,
               supersedes: Optional[str] = None,
               metadata: Optional[Dict] = None) -> Event:
        """Record a new event and return it with computed event_id."""
        event = Event(
            event_id="",  # computed below
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            payload=payload,
            provenance_refs=provenance_refs or [],
            effect_class=effect_class,
            confidence=confidence,
            supersedes=supersedes,
            metadata=metadata or {},
        )
        event.event_id = event.compute_id()

        # Store
        self._events[event.event_id] = event
        self._by_type.setdefault(event_type, []).append(event.event_id)
        self._by_source.setdefault(source, []).append(event.event_id)

        # Track supersession
        if supersedes:
            self._superseded_by[supersedes] = event.event_id

        return event

    def get(self, event_id: str) -> Optional[Event]:
        """Retrieve an event by ID."""
        return self._events.get(event_id)

    def get_by_type(self, event_type: str) -> List[Event]:
        """Get all events of a given type."""
        return [self._events[eid] for eid in self._by_type.get(event_type, [])]

    def get_by_source(self, source: str) -> List[Event]:
        """Get all events from a given source."""
        return [self._events[eid] for eid in self._by_source.get(source, [])]

    def resolve_supersession(self, event_id: str) -> Optional[Event]:
        """
        Follow supersession chain forward to find the current active event.

        If B.supersedes = A, then B replaces A. Given A's ID, returns B.
        Follows the chain to the terminal node.
        """
        current_id = event_id
        while current_id in self._superseded_by:
            current_id = self._superseded_by[current_id]
        return self.get(current_id)

    def latest_by_tag(self, tag: str, value: str) -> Optional[Event]:
        """Find the latest event where metadata[tag] == value."""
        candidates = []
        for event in self._events.values():
            if event.metadata.get(tag) == value:
                candidates.append(event)
        if not candidates:
            return None
        return max(candidates, key=lambda e: e.timestamp)

    def all_events(self) -> List[Event]:
        """Return all events sorted by timestamp."""
        return sorted(self._events.values(), key=lambda e: e.timestamp)

    def count(self) -> int:
        return len(self._events)


def quick_test():
    """Demonstrate the event ledger."""
    ledger = EventLedger()

    # Record a trace
    evt1 = ledger.record("trace", "model", {
        "operation": "search",
        "query": "MiniCPM long-context configuration"
    }, effect_class="SEARCH")
    print(f"Trace event: {evt1.event_id}")
    print(f"  Type: {evt1.event_type}, Source: {evt1.source}")

    # Record a claim
    evt2 = ledger.record("claim", "substrate", {
        "claim": "Paris is the capital of France",
        "confidence": 0.95,
    }, provenance_refs=[evt1.event_id], confidence=0.95)
    print(f"Claim event: {evt2.event_id}")

    # Record a decision
    evt3 = ledger.record("decision", "model", {
        "action": "answer",
        "content": "The capital of France is Paris.",
    }, provenance_refs=[evt1.event_id, evt2.event_id], effect_class="PURE")
    print(f"Decision event: {evt3.event_id}")

    # Verify content addressing (same payload → same ID)
    evt4 = ledger.record("trace", "model", {
        "operation": "search",
        "query": "MiniCPM long-context configuration"
    }, effect_class="SEARCH")
    print(f"\nContent-addressing check:")
    print(f"  Same payload → {evt1.event_id == evt4.event_id}")

    # Supersession
    evt_old = ledger.record("claim", "substrate", {
        "claim": "Pluto is a planet",
        "confidence": 0.3,
    }, confidence=0.3)
    evt_new = ledger.record("claim", "substrate", {
        "claim": "Pluto is a dwarf planet",
        "confidence": 0.95,
    }, supersedes=evt_old.event_id, confidence=0.95)
    resolved = ledger.resolve_supersession(evt_new.event_id)
    print(f"\nSupersession: superseded claim → '{evt_old.payload['claim']}'")
    print(f"  Active claim → '{resolved.payload['claim']}'")

    print(f"\nTotal events: {ledger.count()}")


if __name__ == "__main__":
    quick_test()