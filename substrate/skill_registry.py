"""
Substrate — Minimal Skill Registry

From Substrate Spec §10. Manages validated reusable procedures with
typed interfaces, effects, permissions, and lifecycle state.

Skills are promoted through gates (not merely by frequency — Substrate Spec §9).
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .effects import EffectClass, EffectPolicy, get_policy


class SkillStatus(str, Enum):
    CANDIDATE = "candidate"
    SHADOW = "shadow"
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    RETIRED = "retired"


@dataclass
class SkillEntry:
    """
    A promoted skill with full metadata.

    From Substrate Spec §10: Every promoted skill should expose
    typed_inputs, typed_outputs, preconditions, postconditions,
    effects, permissions, failure_modes, validator, etc.
    """
    name: str
    version: str = "0.1.0"
    description: str = ""

    typed_inputs: Dict[str, str] = field(default_factory=dict)
    typed_outputs: Dict[str, str] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)

    effects: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

    failure_modes: List[str] = field(default_factory=list)
    retry_policy: str = "none"
    rollback_policy: str = "none"

    validator: Optional[Callable] = None
    handler: Optional[Callable] = None

    status: SkillStatus = SkillStatus.CANDIDATE
    confidence: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0.0
    created_at: float = 0.0

    provenance: Dict[str, Any] = field(default_factory=dict)
    source_trace_hashes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("handler", None)
        d.pop("validator", None)
        d["status"] = self.status.value
        return d


class SkillRegistry:
    """
    Registry of validated, versioned skills.

    Uses hysteresis for lifecycle transitions (Substrate Spec §15):
    - candidate creation: cheap
    - promotion to active: difficult
    - quarantine: easy + reversible
    - permanent retirement: difficult
    """

    def __init__(self):
        self._skills: Dict[str, SkillEntry] = {}
        self._by_status: Dict[SkillStatus, List[str]] = {
            s: [] for s in SkillStatus
        }

    def register(self, skill: SkillEntry) -> str:
        """Register or update a skill."""
        existing = self._skills.get(skill.name)
        if existing:
            # Move from old status list
            if existing.status in self._by_status:
                self._by_status[existing.status] = [n for n in self._by_status[existing.status] if n != skill.name]
        self._skills[skill.name] = skill
        self._by_status[skill.status].append(skill.name)
        return skill.name

    def get(self, name: str) -> Optional[SkillEntry]:
        return self._skills.get(name)

    def get_by_status(self, status: SkillStatus) -> List[SkillEntry]:
        return [self._skills[n] for n in self._by_status.get(status, [])]

    def promote(self, name: str) -> bool:
        """
        Promote a candidate to active status.

        From Substrate Spec §15: Promotion requires evidence.
        """
        skill = self._skills.get(name)
        if not skill:
            return False
        if skill.status != SkillStatus.CANDIDATE:
            return False
        self._by_status[skill.status].remove(name)
        skill.status = SkillStatus.ACTIVE
        self._by_status[SkillStatus.ACTIVE].append(name)
        return True

    def quarantine(self, name: str) -> bool:
        """
        Quarantine an active skill.

        From Substrate Spec §15: Quarantine is easy + reversible.
        """
        skill = self._skills.get(name)
        if not skill or skill.status != SkillStatus.ACTIVE:
            return False
        self._by_status[SkillStatus.ACTIVE].remove(name)
        skill.status = SkillStatus.QUARANTINED
        self._by_status[SkillStatus.QUARANTINED].append(name)
        return True

    def restore(self, name: str) -> bool:
        """Restore a quarantined skill to active."""
        skill = self._skills.get(name)
        if not skill or skill.status != SkillStatus.QUARANTINED:
            return False
        self._by_status[SkillStatus.QUARANTINED].remove(name)
        skill.status = SkillStatus.ACTIVE
        self._by_status[SkillStatus.ACTIVE].append(name)
        return True

    def retire(self, name: str) -> bool:
        """
        Permanently retire a skill.

        From Substrate Spec §15: Permanent retirement is difficult.
        """
        skill = self._skills.get(name)
        if not skill:
            return False
        for status_list in self._by_status.values():
            if name in status_list:
                status_list.remove(name)
        skill.status = SkillStatus.RETIRED
        self._by_status[SkillStatus.RETIRED].append(name)
        return True

    def record_success(self, name: str):
        skill = self._skills.get(name)
        if skill:
            skill.success_count += 1
            skill.last_used = time.time()

    def record_failure(self, name: str):
        skill = self._skills.get(name)
        if skill:
            skill.failure_count += 1
            skill.last_used = time.time()

    def list_skills(self) -> List[str]:
        return sorted(self._skills.keys())

    def count(self) -> int:
        return len(self._skills)


def quick_test():
    """Demonstrate the skill registry."""
    registry = SkillRegistry()

    # Register candidate skill
    skill = SkillEntry(
        name="verify_claim",
        description="Verify a claim against available evidence",
        typed_inputs={"claim": "string", "evidence_refs": "list"},
        typed_outputs={"verified": "bool", "confidence": "float"},
        effects=["READ_LOCAL"],
        failure_modes=["insufficient_evidence", "contradictory_evidence"],
    )
    registry.register(skill)
    print(f"Registered: {skill.name} (status={skill.status.value})")

    # Promote
    registry.promote("verify_claim")
    print(f"Promoted:   {skill.name} (status={skill.status.value})")

    # Record usage
    registry.record_success("verify_claim")
    registry.record_success("verify_claim")
    registry.record_failure("verify_claim")
    print(f"  Successes: {skill.success_count}, Failures: {skill.failure_count}")

    # Quarantine
    registry.quarantine("verify_claim")
    print(f"Quarantined: {skill.name} (status={skill.status.value})")

    # Restore
    registry.restore("verify_claim")
    print(f"Restored:   {skill.name} (status={skill.status.value})")

    # List all
    print(f"\nAll skills: {registry.list_skills()}")
    print(f"Active:     {[s.name for s in registry.get_by_status(SkillStatus.ACTIVE)]}")


if __name__ == "__main__":
    quick_test()