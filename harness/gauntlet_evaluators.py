"""Gauntlet evaluators — deterministic scoring for model outputs."""

import re
from typing import Any, List

from tools.intents import Intent, IntentGrammar


def _remove_chat_markup(text: str) -> str:
    text = re.sub(r'<\|[^>]*\|?>?', '', text)
    text = re.sub(r'</?\|im_(start|end)\|?>?', '', text)
    text = re.sub(r'<\|endoftext\|>?', '', text)
    text = re.sub(r'^\s*(?:thinking|response)\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^[Tt]hinking [Pp]rocess:.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*{1,3}\s*[Tt]hinking\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'<[^>]*>', '', text)
    return text


def strip_chat_markup(text: str) -> str:
    text = _remove_chat_markup(text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines).strip()[:1000]


def strip_structured_markup(text: str) -> str:
    """Remove chat wrappers while preserving YAML-like argument indentation."""
    text = _remove_chat_markup(text)
    lines = [line.rstrip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines).strip()[:2000]


def exact_match(output: str, expected: str) -> dict:
    stripped = strip_chat_markup(output)
    passed = stripped.lower() == expected.strip().lower()
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "details": f"Expected '{expected}', got '{stripped[:80]}'" if not passed else f"Exact match: '{expected}'",
    }


def contains(output: str, expected: str) -> dict:
    stripped = strip_chat_markup(output)
    passed = expected.lower() in stripped.lower()
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "details": f"Expected to contain '{expected}', got '{stripped[:120]}'" if not passed else f"Contains '{expected}'",
    }


def contains_all(output: str, expected: List[str]) -> dict:
    out = strip_chat_markup(output).lower()
    found = [exp for exp in expected if exp.lower() in out]
    missing = [exp for exp in expected if exp.lower() not in out]
    score = len(found) / len(expected) if expected else 1.0
    return {
        "passed": score >= 1.0,
        "score": score,
        "details": f"Found {len(found)}/{len(expected)}: missing={missing}" if missing else f"All {len(expected)} items found",
    }


def contains_any(output: str, expected: List[str]) -> dict:
    out = strip_chat_markup(output).lower()
    found = [exp for exp in expected if exp.lower() in out]
    score = len(found) / len(expected) if expected else 1.0
    return {
        "passed": bool(found),
        "score": score,
        "details": f"Found: {found[:3]}" if found else f"Found 0/{len(expected)}",
    }


def numeric_match(output: str, expected: str) -> dict:
    stripped = strip_chat_markup(output)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', stripped)
    expected_numbers = re.findall(r'-?\d+(?:\.\d+)?', expected)
    exp_num = expected_numbers[0] if expected_numbers else expected
    passed = exp_num in numbers
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "details": f"Expected number '{expected}', found numbers {numbers}" if not passed else f"Numeric match: {exp_num}",
    }


def step_by_step(output: str, expected: str) -> dict:
    parts = expected.split("|")
    final_answer = parts[0].strip()
    keywords = [k.strip() for k in parts[1].split(",")] if len(parts) > 1 else []
    out_lower = strip_chat_markup(output).lower()
    has_answer = final_answer.lower() in out_lower
    found_keywords = [k for k in keywords if k.lower() in out_lower]
    keyword_score = len(found_keywords) / len(keywords) if keywords else 1.0
    has_working = any(marker in out_lower for marker in ["step", "first", "then", "finally", "therefore"]) or output.count("\n") >= 3
    score = 0.5 * float(has_answer) + 0.3 * keyword_score + 0.2 * float(has_working)
    return {
        "passed": has_answer and keyword_score >= 0.5,
        "score": round(score, 2),
        "details": f"Answer={has_answer}; keywords={found_keywords}/{keywords}; working={has_working}",
    }


def intent_fields(
    output: str,
    expected: dict,
    *,
    abstention_operations: List[str] | None = None,
    allow_abstention: bool = False,
) -> dict:
    """Score the existing typed Intent grammar by exact operation/argument fields.

    This intentionally does not use an LLM judge. Supersession tasks therefore
    cannot pass by mentioning both stale and current values in prose.
    """
    stripped = strip_structured_markup(output)
    valid, error = IntentGrammar.validate_output(stripped)
    if not valid:
        return {
            "passed": False,
            "score": 0.0,
            "outcome": "invalid",
            "details": f"Invalid typed intent: {error}",
        }

    intent = Intent.from_yaml_like(stripped)
    abstentions = set(abstention_operations or [])
    if allow_abstention and intent.operation.value in abstentions:
        return {
            "passed": False,
            "score": 0.0,
            "outcome": "correct_abstention",
            "details": f"Correct abstention via operation={intent.operation.value}",
        }

    expected_operation = str(expected.get("operation", "pure_call"))
    expected_arguments = dict(expected.get("arguments", {}))
    operation_ok = intent.operation.value == expected_operation
    arguments_ok = intent.arguments == expected_arguments
    passed = operation_ok and arguments_ok

    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "outcome": "supported_correct" if passed else "confident_wrong",
        "details": (
            f"Typed intent matched {expected_operation} {expected_arguments}"
            if passed
            else f"Expected {expected_operation} {expected_arguments}; got {intent.operation.value} {intent.arguments}"
        ),
    }


EVALUATORS = {
    "exact_match": exact_match,
    "contains": contains,
    "contains_all": contains_all,
    "contains_any": contains_any,
    "numeric_match": numeric_match,
    "step_by_step": step_by_step,
}


def evaluate_task(output: str, task: dict, *, allow_abstention: bool = False) -> dict:
    evaluator_name = task.get("evaluator", "contains")
    if evaluator_name == "intent_fields":
        return intent_fields(
            output,
            task["expected"],
            abstention_operations=task.get("abstention_operations", []),
            allow_abstention=allow_abstention,
        )

    evaluator_fn = EVALUATORS.get(evaluator_name, contains)
    result = evaluator_fn(output, task["expected"])
    result.setdefault("outcome", "supported_correct" if result["passed"] else "confident_wrong")
    return result
