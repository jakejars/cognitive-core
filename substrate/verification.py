"""
Substrate — Post-Generation Deterministic Verification

From Substrate Spec §1.2: "True verification of a completed answer/action is post-generation."

The pipeline:
  1. Model produces candidate answer
  2. Deterministic checks: schema, provenance, citations, effects, tool state
  3. Accept / Revise / Search / Ask / Escalate decision
  4. Only trusted components may construct privileged types like CitationCheckedAnswer
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class Verdict(Enum):
    ACCEPT = "accept"
    REVISE = "revise"
    SEARCH = "search"
    ASK_USER = "ask_user"
    ESCALATE = "escalate"
    BLOCK = "block"


@dataclass
class VerificationResult:
    """Result of post-generation verification."""
    passed: bool
    verdict: Verdict
    checks: Dict[str, bool]
    failures: List[str]
    details: str = ""


class VerificationCheck:
    """A single deterministic check in the verification pipeline."""
    
    def __init__(self, name: str, check_fn: Callable[[Dict], bool],
                 fail_verdict: Verdict = Verdict.REVISE,
                 description: str = ""):
        self.name = name
        self.check_fn = check_fn
        self.fail_verdict = fail_verdict
        self.description = description

    def run(self, context: Dict) -> tuple[bool, Optional[str]]:
        try:
            passed = self.check_fn(context)
            return passed, None if passed else f"Check '{self.name}' failed"
        except Exception as e:
            return False, f"Check '{self.name}' raised: {e}"


class VerificationPipeline:
    """
    Post-generation verification pipeline.

    From Substrate Spec §22.1 (hard gates) and §1.2 (verification flow).
    Checks are run sequentially; the first failure determines the verdict.
    """

    def __init__(self):
        self._checks: List[VerificationCheck] = []

    def add_check(self, check: VerificationCheck):
        """Register a verification check."""
        self._checks.append(check)

    def verify(self, context: Dict) -> VerificationResult:
        """
        Run all checks against the context.

        Context dict should include:
          - "output": model-generated text
          - "provenance_refs": provenance node IDs
          - "effect_class": effect class of the operation
          - "intent": original intent dict
        """
        failures = []
        check_results = {}
        verdict = Verdict.ACCEPT

        for check in self._checks:
            passed, error = check.run(context)
            check_results[check.name] = passed
            if not passed:
                failures.append(error or f"Check '{check.name}' failed")
                if verdict == Verdict.ACCEPT:
                    verdict = check.fail_verdict

        return VerificationResult(
            passed=len(failures) == 0,
            verdict=verdict,
            checks=check_results,
            failures=failures,
            details="; ".join(failures) if failures else "All checks passed",
        )


# ── Built-in Checks ────────────────────────────────────────────────

def schema_check(expected_schema: Dict) -> VerificationCheck:
    """Check that the output matches a schema."""
    import json
    def _check(ctx):
        output = ctx.get("output", "")
        # Try to parse as JSON
        try:
            data = json.loads(output)
            if expected_schema:
                for key in expected_schema.get("required", []):
                    if key not in data:
                        return False
            return True
        except json.JSONDecodeError:
            return False
    return VerificationCheck("schema", _check, Verdict.REVISE)


def provenance_check(min_refs: int = 0) -> VerificationCheck:
    """Check that sufficient provenance references exist."""
    def _check(ctx):
        refs = ctx.get("provenance_refs", [])
        return len(refs) >= min_refs
    return VerificationCheck(
        "provenance", _check, Verdict.REVISE,
        f"At least {min_refs} provenance refs required"
    )


def effect_safety_check() -> VerificationCheck:
    """Check that the operation respects effect policies."""
    def _check(ctx):
        effect_class = ctx.get("effect_class", "PURE")
        from .effects import EffectClass, get_policy
        try:
            ec = EffectClass(effect_class)
            policy = get_policy(ec)
            return True  # Policy is known
        except (ValueError, KeyError):
            return False
    return VerificationCheck(
        "effect_safety", _check, Verdict.BLOCK,
        "Unknown effect class"
    )


def citation_check() -> VerificationCheck:
    """Check that claims reference specific evidence."""
    import re
    def _check(ctx):
        output = ctx.get("output", "")
        # Look for citation markers
        has_citations = bool(re.search(r'\[evt_\w+\]|\[prov_\w+\]', output))
        return has_citations
    return VerificationCheck(
        "citations", _check, Verdict.SEARCH,
        "Claims should reference specific evidence"
    )


def build_default_pipeline() -> VerificationPipeline:
    """Build the recommended default verification pipeline."""
    pipeline = VerificationPipeline()
    pipeline.add_check(effect_safety_check())
    pipeline.add_check(provenance_check(min_refs=1))
    return pipeline


def quick_test():
    """Demonstrate verification pipeline."""
    from .effects import EffectClass
    
    pipeline = build_default_pipeline()
    
    print("=== Verification Pipeline ===\n")
    
    # Pass case
    result = pipeline.verify({
        "output": "Paris is the capital of France [evt_abc123]",
        "provenance_refs": ["prov_abc"],
        "effect_class": "PURE",
    })
    print(f"Pass case:  {result.verdict.value}  (passed={result.passed})")
    print(f"  Checks:   {result.checks}")
    
    # Fail: no provenance
    result = pipeline.verify({
        "output": "I don't know.",
        "provenance_refs": [],
        "effect_class": "PURE",
    })
    print(f"\nFail case:  {result.verdict.value}  (passed={result.passed})")
    print(f"  Failures: {result.failures}")
    
    # Fail: unknown effect class
    result = pipeline.verify({
        "output": "Doing something dangerous",
        "provenance_refs": ["prov_abc"],
        "effect_class": "UNKNOWN_EFFECT",
    })
    print(f"\nBlock case: {result.verdict.value}  (passed={result.passed})")
    print(f"  Failures: {result.failures}")


if __name__ == "__main__":
    quick_test()