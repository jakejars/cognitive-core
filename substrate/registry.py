"""
Substrate — Operation Registry

Trusted registry of operations and their metadata. From Substrate Spec §3.3.
The model cannot override registry-defined safety semantics.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from .effects import EffectClass, get_policy, EffectPolicy


@dataclass
class OperationInfo:
    """
    Registered operation metadata.

    This is the runtime's authoritative definition — not model-suggested.
    From Substrate Spec §3.2.
    """
    name: str
    """Operation name, e.g. 'search', 'invoke_skill', 'verify'."""

    version: str = "1.0.0"
    """Semantic version of this operation definition."""

    description: str = ""
    """Human-readable description."""

    input_schema: Dict[str, Any] = field(default_factory=dict)
    """Expected argument schema (JSON Schema style)."""

    output_schema: Dict[str, Any] = field(default_factory=dict)
    """Expected output schema."""

    effect_class: EffectClass = EffectClass.PURE
    """Default effect class."""

    effect_policy: Optional[EffectPolicy] = None
    """Effect policy (derived from effect_class if not set)."""

    handler: Optional[Callable] = None
    """Optional runtime handler function."""

    def __post_init__(self):
        if self.effect_policy is None:
            self.effect_policy = get_policy(self.effect_class)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("handler", None)
        return d


# ── Built-in Operations (from Substrate Spec §3.3) ──────────────────

BUILTIN_OPS = [
    OperationInfo(
        name="pure_call",
        description="Pure deterministic function call",
        input_schema={"type": "object", "properties": {"function": {"type": "string"}, "args": {"type": "array"}}},
        effect_class=EffectClass.PURE,
    ),
    OperationInfo(
        name="model_call",
        description="Neural model inference",
        input_schema={"type": "object", "properties": {"prompt": {"type": "string"}, "max_tokens": {"type": "integer"}}},
        effect_class=EffectClass.MODEL_STOCHASTIC,
    ),
    OperationInfo(
        name="tool_call",
        description="External tool invocation",
        input_schema={"type": "object", "properties": {"tool": {"type": "string"}, "arguments": {"type": "object"}}},
        effect_class=EffectClass.COMPUTE_SANDBOXED,
    ),
    OperationInfo(
        name="retrieve",
        description="Local memory retrieval",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}}},
        effect_class=EffectClass.READ_LOCAL,
    ),
    OperationInfo(
        name="search",
        description="External semantic search",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}, "corpus": {"type": "string"}}},
        effect_class=EffectClass.SEARCH,
    ),
    OperationInfo(
        name="compute",
        description="Sandboxed computation",
        input_schema={"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string"}}},
        effect_class=EffectClass.COMPUTE_SANDBOXED,
    ),
    OperationInfo(
        name="verify",
        description="Deterministic verification",
        input_schema={"type": "object", "properties": {"draft_ref": {"type": "string"}, "evidence_refs": {"type": "array"}}},
        effect_class=EffectClass.PURE,
    ),
    OperationInfo(
        name="materialize",
        description="Materialise historical state into working context",
        input_schema={"type": "object", "properties": {"ref": {"type": "string"}}},
        effect_class=EffectClass.READ_LOCAL,
    ),
    OperationInfo(
        name="ask_user",
        description="Request human input",
        input_schema={"type": "object", "properties": {"question": {"type": "string"}}},
        effect_class=EffectClass.HUMAN_APPROVAL,
    ),
    OperationInfo(
        name="escalate",
        description="Escalate to human operator",
        input_schema={"type": "object", "properties": {"reason": {"type": "string"}, "context_refs": {"type": "array"}}},
        effect_class=EffectClass.HUMAN_APPROVAL,
    ),
    OperationInfo(
        name="commit_effect",
        description="Commit an irreversible effect",
        input_schema={"type": "object", "properties": {"effect": {"type": "string"}, "target": {"type": "string"}}},
        effect_class=EffectClass.IRREVERSIBLE,
    ),
]


class OperationRegistry:
    """
    Trusted registry of operations.

    The model proposes semantic intent (operation name + arguments).
    The registry resolves it to the authoritative metadata.

    From Substrate Spec §3.2: "The model cannot override registry-defined
    safety semantics by emitting different metadata."
    """

    def __init__(self):
        self._ops: Dict[str, OperationInfo] = {}
        for op in BUILTIN_OPS:
            self.register(op)

    def register(self, op: OperationInfo):
        """Register an operation (built-in or custom)."""
        self._ops[op.name] = op

    def get(self, name: str) -> Optional[OperationInfo]:
        """Look up an operation by name."""
        return self._ops.get(name)

    def resolve(self, name: str) -> OperationInfo:
        """Resolve operation, raising KeyError if not found."""
        if name not in self._ops:
            raise KeyError(f"Unknown operation: '{name}'. Registered: {list(self._ops.keys())}")
        return self._ops[name]

    def list_operations(self) -> List[str]:
        """Return all registered operation names."""
        return sorted(self._ops.keys())

    def execution_hash(self, name: str, arguments: dict) -> str:
        """
        Compute execution identity hash.

        From Substrate Spec §6.2: Must include operation_version, canonical_arguments.
        Never use structural identity as execution cache key.
        """
        op = self.resolve(name)
        content = {
            "operation": name,
            "version": op.version,
            "arguments": arguments,
        }
        raw = json.dumps(content, sort_keys=True).encode()
        return f"exec_{hashlib.sha256(raw).hexdigest()[:32]}"

    def structural_hash(self, name: str, arguments: dict) -> str:
        """
        Compute structural identity hash.

        From Substrate Spec §6.1: Used for near-duplicate detection, skill mining,
        clustering. May ignore selected literal values.

        For now, this is identical to execution hash but conceptually distinct.
        In future, this should canonicalize variable names and formatting.
        """
        return self.execution_hash(name, arguments)


def quick_test():
    """Demonstrate the operation registry."""
    reg = OperationRegistry()

    print("=== Registered Operations ===")
    for name in reg.list_operations():
        info = reg.get(name)
        print(f"  {name:20s} → {info.effect_class.value:20s} deterministic={info.effect_policy.deterministic}")

    # Resolve
    info = reg.resolve("search")
    print(f"\nResolve 'search':")
    print(f"  Effect: {info.effect_class.value}")
    print(f"  Policy: deterministic={info.effect_policy.deterministic}, idempotent={info.effect_policy.idempotent}")

    # Execution hash
    h1 = reg.execution_hash("search", {"query": "hello"})
    h2 = reg.execution_hash("search", {"query": "world"})
    print(f"\nExecution hashes:")
    print(f"  search('hello'): {h1}")
    print(f"  search('world'): {h2}")
    print(f"  Different arguments → different hashes: {h1 != h2}")

    # Unknown operation
    try:
        reg.resolve("nonexistent")
    except KeyError as e:
        print(f"\nUnknown operation error correctly raised: {e}")


if __name__ == "__main__":
    quick_test()