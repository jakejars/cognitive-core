"""
Grammar-Constrained Tool Intent Framework for Cognitive Core Gen-2

The neural model emits concise semantic intent. The trusted substrate
enriches it at runtime. This module provides:
  - Pydantic-style intent schemas
  - Grammar constraints for structured decoding
  - Output validation

Based on Substrate Spec §3 — Minimal model-emitted intent + Runtime enrichment.
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# ── Effect Classes (from Substrate Spec §4) ──────────────────────────

class EffectClass(str, Enum):
    PURE = "PURE"
    READ_LOCAL = "READ_LOCAL"
    READ_REMOTE = "READ_REMOTE"
    SEARCH = "SEARCH"
    MODEL_STOCHASTIC = "MODEL_STOCHASTIC"
    COMPUTE_SANDBOXED = "COMPUTE_SANDBOXED"
    MUTATE_REVERSIBLE = "MUTATE_REVERSIBLE"
    MUTATE_EXTERNAL = "MUTATE_EXTERNAL"
    IRREVERSIBLE = "IRREVERSIBLE"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


# ── Operation Registry (from Substrate Spec §3.3) ────────────────────

class Operation(str, Enum):
    PURE_CALL = "pure_call"
    MODEL_CALL = "model_call"
    TOOL_CALL = "tool_call"
    RETRIEVE = "retrieve"
    SEARCH = "search"
    COMPUTE = "compute"
    MAP = "map"
    JOIN = "join"
    BRANCH = "branch"
    RETRY = "retry"
    VERIFY = "verify"
    MATERIALIZE = "materialize"
    ASK_USER = "ask_user"
    ESCALATE = "escalate"
    HUMAN_APPROVAL = "human_approval"
    COMMIT_EFFECT = "commit_effect"


# ── Model-Emitted Intent (from Substrate Spec §3.1) ──────────────────

@dataclass
class Intent:
    """Minimal semantic intent emitted by the neural model."""
    operation: Operation
    arguments: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    candidate_dependencies: List[str] = field(default_factory=list)

    def to_yaml_like(self) -> str:
        """Serialize to a YAML-like string for grammar-constrained decoding."""
        lines = [
            f"operation: {self.operation.value}",
        ]
        if self.arguments:
            lines.append("arguments:")
            for k, v in self.arguments.items():
                lines.append(f"  {k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}")
        if self.evidence_refs:
            lines.append(f"evidence_refs: {json.dumps(self.evidence_refs)}")
        if self.candidate_dependencies:
            lines.append(f"candidate_dependencies: {json.dumps(self.candidate_dependencies)}")
        return "\n".join(lines)

    @classmethod
    def from_yaml_like(cls, text: str) -> "Intent":
        """Parse YAML-like intent string back into an Intent."""
        op = Operation.PURE_CALL
        args = {}
        evidence = []
        deps = []

        for line in text.strip().split("\n"):
            line = line.rstrip()
            if line.startswith("operation:"):
                op_name = line.split(":", 1)[1].strip()
                try:
                    op = Operation(op_name)
                except ValueError:
                    pass
            elif line.startswith("evidence_refs:"):
                try:
                    evidence = json.loads(line.split(":", 1)[1].strip())
                except (json.JSONDecodeError, IndexError):
                    pass
            elif line.startswith("candidate_dependencies:"):
                try:
                    deps = json.loads(line.split(":", 1)[1].strip())
                except (json.JSONDecodeError, IndexError):
                    pass
            elif line.startswith("  ") and ":" in line:
                # argument line
                k, v = line.strip().split(":", 1)
                k = k.strip()
                v = v.strip()
                # Try to parse as JSON
                try:
                    args[k] = json.loads(v)
                except (json.JSONDecodeError, ValueError):
                    args[k] = v

        return cls(operation=op, arguments=args, evidence_refs=evidence, candidate_dependencies=deps)


# ── Runtime-Enriched Node (from Substrate Spec §3.2) ──────────────────

@dataclass
class EnrichedNode:
    """Full execution node with runtime-attached metadata."""
    operation_id: str = ""
    operation_version: str = "1.0.0"
    input_schema: Dict = field(default_factory=dict)
    output_schema: Dict = field(default_factory=dict)
    canonical_arguments: Dict = field(default_factory=dict)
    content_hash: str = ""
    execution_hash: str = ""
    effect_class: EffectClass = EffectClass.PURE
    deterministic: bool = True
    idempotency: str = "yes"
    permissions: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    confidentiality: str = "public"
    estimated_cost: str = "low"
    estimated_latency: str = "low"
    provenance: Dict = field(default_factory=dict)
    validator: Optional[str] = None
    retry_policy: str = "none"
    rollback_policy: str = "none"


# ── Intent Router ────────────────────────────────────────────────────

class IntentRouter:
    """Maps model-emitted intents to runtime-enriched nodes."""

    def __init__(self):
        # Operation → default effect class mapping
        self._effect_map = {
            Operation.PURE_CALL: EffectClass.PURE,
            Operation.MODEL_CALL: EffectClass.MODEL_STOCHASTIC,
            Operation.TOOL_CALL: EffectClass.COMPUTE_SANDBOXED,
            Operation.RETRIEVE: EffectClass.READ_LOCAL,
            Operation.SEARCH: EffectClass.SEARCH,
            Operation.COMPUTE: EffectClass.COMPUTE_SANDBOXED,
            Operation.MAP: EffectClass.PURE,
            Operation.JOIN: EffectClass.PURE,
            Operation.BRANCH: EffectClass.PURE,
            Operation.RETRY: EffectClass.PURE,
            Operation.VERIFY: EffectClass.PURE,
            Operation.MATERIALIZE: EffectClass.READ_LOCAL,
            Operation.ASK_USER: EffectClass.HUMAN_APPROVAL,
            Operation.ESCALATE: EffectClass.HUMAN_APPROVAL,
            Operation.HUMAN_APPROVAL: EffectClass.HUMAN_APPROVAL,
            Operation.COMMIT_EFFECT: EffectClass.IRREVERSIBLE,
        }

    def enrich(self, intent: Intent) -> EnrichedNode:
        """Convert a model intent into a fully enriched execution node."""
        effect = self._effect_map.get(intent.operation, EffectClass.PURE)
        is_deterministic = effect in (EffectClass.PURE, EffectClass.READ_LOCAL, EffectClass.COMPUTE_SANDBOXED)
        is_idempotent = effect not in (EffectClass.IRREVERSIBLE, EffectClass.MUTATE_EXTERNAL)

        return EnrichedNode(
            operation_id=f"{intent.operation.value}_{hash(json.dumps(intent.arguments, sort_keys=True)) & 0xFFFFFFFF}",
            canonical_arguments=intent.arguments,
            effect_class=effect,
            deterministic=is_deterministic,
            idempotency="yes" if is_idempotent else "no",
        )


# ── Intent Grammar for Constrained Decoding ──────────────────────────

class IntentGrammar:
    """
    Defines a simple grammar for constrained text generation.
    The model is constrained to emit valid intent YAML.
    """

    OPERATIONS = [op.value for op in Operation]

    @classmethod
    def get_prefix(cls) -> str:
        return "operation: "

    @classmethod
    def validate_output(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate that generated text parses as a valid Intent.
        Returns (is_valid, error_message).
        """
        try:
            # Must contain operation: line
            if "operation:" not in text:
                return False, "Missing 'operation:' line"
            
            for line in text.strip().split("\n"):
                line = line.strip()
                if line.startswith("operation:"):
                    op = line.split(":", 1)[1].strip()
                    if op not in cls.OPERATIONS:
                        return False, f"Unknown operation: {op}"
            
            # Try to parse
            Intent.from_yaml_like(text)
            return True, None
        except Exception as e:
            return False, str(e)


# ── Standard Intents (convenience constructors) ──────────────────────

def search_intent(query: str, evidence_refs: Optional[List[str]] = None) -> Intent:
    return Intent(
        operation=Operation.SEARCH,
        arguments={"query": query, "requested_result": "evidence"},
        evidence_refs=evidence_refs or [],
    )

def retrieve_intent(query: str) -> Intent:
    return Intent(
        operation=Operation.RETRIEVE,
        arguments={"query": query},
    )

def invoke_skill_intent(skill: str, arguments: Dict) -> Intent:
    return Intent(
        operation=Operation.TOOL_CALL,
        arguments={"skill": skill, **arguments},
    )

def verify_intent(draft_ref: str, evidence_set_ref: str) -> Intent:
    return Intent(
        operation=Operation.VERIFY,
        arguments={"draft_ref": draft_ref, "evidence_set_ref": evidence_set_ref},
    )

def ask_user_intent(question: str) -> Intent:
    return Intent(
        operation=Operation.ASK_USER,
        arguments={"question": question},
    )

def answer_intent(answer: str, evidence_refs: List[str]) -> Intent:
    return Intent(
        operation=Operation.PURE_CALL,
        arguments={"answer": answer},
        evidence_refs=evidence_refs,
    )


# ── Quick test ───────────────────────────────────────────────────────

def quick_test():
    """Demonstrate the intent system."""
    router = IntentRouter()

    # Example: model emits a search intent
    intent = search_intent("MiniCPM long-context configuration")
    print("=== Model-emitted intent ===")
    print(intent.to_yaml_like())

    # Runtime enriches it
    node = router.enrich(intent)
    print("\n=== Runtime-enriched node ===")
    for k, v in asdict(node).items():
        print(f"  {k}: {v}")

    # Parse back
    text = intent.to_yaml_like()
    parsed = Intent.from_yaml_like(text)
    print(f"\n=== Parsed back ===")
    print(f"  operation: {parsed.operation.value}")
    print(f"  arguments: {parsed.arguments}")

    # Validation
    valid, err = IntentGrammar.validate_output(text)
    print(f"\n=== Validation ===")
    print(f"  valid: {valid}")
    if err:
        print(f"  error: {err}")


if __name__ == "__main__":
    quick_test()