"""
Substrate — Effect Classes

From Substrate Spec §4. Defines the effect taxonomy used for scheduling,
idempotency, permissions, and audit.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class EffectClass(str, Enum):
    """Taxonomy of operation effects. Determines scheduling, idempotency, and audit policy."""

    PURE = "PURE"
    """Deterministic, no side effects. May be reordered, memoised, deduplicated, parallelised."""

    READ_LOCAL = "READ_LOCAL"
    """Reads local state but does not mutate. Deterministic within state version."""

    READ_REMOTE = "READ_REMOTE"
    """Reads remote state. Non-deterministic in general but safe to retry."""

    SEARCH = "SEARCH"
    """Semantic search over indexed corpora. Idempotent, moderate cost."""

    MODEL_STOCHASTIC = "MODEL_STOCHASTIC"
    """Neural model generation. Non-deterministic, potentially expensive."""

    COMPUTE_SANDBOXED = "COMPUTE_SANDBOXED"
    """Sandboxed computation (e.g. code execution). Deterministic within sandbox."""

    MUTATE_REVERSIBLE = "MUTATE_REVERSIBLE"
    """Mutation with defined rollback procedure."""

    MUTATE_EXTERNAL = "MUTATE_EXTERNAL"
    """Mutation of external state without guaranteed rollback."""

    IRREVERSIBLE = "IRREVERSIBLE"
    """Irreversible action. Must never be deduplicated or replayed from structural match alone."""

    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    """Requires human consent before execution."""


@dataclass
class EffectPolicy:
    """
    Policy constraints for an effect class.

    These are the runtime-enforced rules, not model-suggested preferences.
    """
    effect_class: EffectClass

    # Determinism
    deterministic: bool = True

    # Idempotency
    idempotent: bool = True
    """If True, the operation may safely be retried with identical arguments."""

    # Parallelism
    parallel_safe: bool = True
    """If True, may execute concurrently with other operations of compatible classes."""

    # Reorder safety
    reorder_safe: bool = True
    """If True, may be reordered past other operations (only for PURE)."""

    # Retry policy
    max_retries: int = 0
    retry_delay_ms: int = 0

    # Rollback
    rollback_available: bool = False
    """If True, a compensating action exists to undo this effect."""

    # Permission requirements
    required_permissions: List[str] = field(default_factory=list)

    # Audit
    audit_level: str = "basic"
    """'none', 'basic' (logged), 'detailed' (full input/output capture)."""


# Effect class → default policy mapping
DEFAULT_POLICIES = {
    EffectClass.PURE: EffectPolicy(
        effect_class=EffectClass.PURE,
        deterministic=True, idempotent=True,
        parallel_safe=True, reorder_safe=True,
        audit_level="none",
    ),
    EffectClass.READ_LOCAL: EffectPolicy(
        effect_class=EffectClass.READ_LOCAL,
        deterministic=True, idempotent=True,
        parallel_safe=True, reorder_safe=False,
    ),
    EffectClass.READ_REMOTE: EffectPolicy(
        effect_class=EffectClass.READ_REMOTE,
        deterministic=False, idempotent=True,
        parallel_safe=True, reorder_safe=False,
    ),
    EffectClass.SEARCH: EffectPolicy(
        effect_class=EffectClass.SEARCH,
        deterministic=False, idempotent=True,
        parallel_safe=True, reorder_safe=False,
    ),
    EffectClass.MODEL_STOCHASTIC: EffectPolicy(
        effect_class=EffectClass.MODEL_STOCHASTIC,
        deterministic=False, idempotent=False,
        parallel_safe=True, reorder_safe=False,
    ),
    EffectClass.COMPUTE_SANDBOXED: EffectPolicy(
        effect_class=EffectClass.COMPUTE_SANDBOXED,
        deterministic=True, idempotent=True,
        parallel_safe=True, reorder_safe=False,
    ),
    EffectClass.MUTATE_REVERSIBLE: EffectPolicy(
        effect_class=EffectClass.MUTATE_REVERSIBLE,
        deterministic=False, idempotent=False,
        parallel_safe=False, reorder_safe=False,
        rollback_available=True,
        audit_level="detailed",
    ),
    EffectClass.MUTATE_EXTERNAL: EffectPolicy(
        effect_class=EffectClass.MUTATE_EXTERNAL,
        deterministic=False, idempotent=False,
        parallel_safe=False, reorder_safe=False,
        audit_level="detailed",
    ),
    EffectClass.IRREVERSIBLE: EffectPolicy(
        effect_class=EffectClass.IRREVERSIBLE,
        deterministic=False, idempotent=False,
        parallel_safe=False, reorder_safe=False,
        audit_level="detailed",
        required_permissions=["explicit_human_policy"],
    ),
    EffectClass.HUMAN_APPROVAL: EffectPolicy(
        effect_class=EffectClass.HUMAN_APPROVAL,
        deterministic=False, idempotent=True,
        parallel_safe=False, reorder_safe=False,
        audit_level="detailed",
    ),
}


def get_policy(effect_class: EffectClass) -> EffectPolicy:
    """Get the default policy for an effect class."""
    return DEFAULT_POLICIES.get(effect_class, DEFAULT_POLICIES[EffectClass.PURE])