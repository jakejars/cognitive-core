"""
Gauntlet evaluators — functions that score model outputs against expected results.

Each evaluator takes (output_text: str, expected: Any) and returns
  {
    "passed": bool,
    "score": float,          # 0.0 to 1.0
    "details": str           # human-readable explanation
  }
"""

import re
from typing import Any, List

from tools.intents import Intent, IntentGrammar


def _remove_chat_markup(text: str) -> str:
    """Remove chat wrappers without deciding how whitespace is normalized."""
    text = re.sub(r'<\|[^>]*\|?>?', '', text)
    text = re.sub(r'</?\|im_(start|end)\|?>?', '', text)
    text = re.sub(r'<\|endoftext\|>?', '', text)
    text = re.sub(r'^\s*(?:thinking|response)\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^[Tt]hinking [Pp]rocess:.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*{1,3}\s*[Tt]hinking\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'<[^>]*>', '', text)
    return text


def strip_chat_markup(text: str) -> str:
    """
    Remove chat template markup from model output.
    Handles <|user|>, <|assistant|>, <|end|>, <|im_start|>, <|im_end|>,
    <|endoftext|>, <|fim_middle|>, response/thinking tokens,
    and partial/incomplete tags.
    """
    text = _remove_chat_markup(text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    result = '\n'.join(lines).strip()
    return result[:500]


def strip_structured_markup(text: str) -> str:
    """Remove wrappers but preserve indentation needed by the existing Intent parser."""
    text = _remove_chat_markup(text)
    lines = [line.rstrip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines).strip()[:2000]


def exact_match(output: str, expected: str) -> dict:
    """Check if the output equals the expected string (case-insensitive, stripped)."""
    stripped = strip_chat_markup(output)
    out = stripped.lower()
    exp = expected.strip().lower()
    passed = out == exp
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "details": f"Expected '{expected}', got '{stripped[:80]}'" if not passed else f"Exact match: '{expected}'"
    }


def contains(output: str, expected: str) -> dict:
    """Check if the expected string is contained in the output (case-insensitive)."""
    out = strip_chat_markup(output).lower()
    exp = expected.lower()
    passed = exp in out
    stripped = strip_chat_markup(output)
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "details": f"Expected to contain '{expected}', got '{stripped[:120]}'" if not passed else f"Contains '{expected}'"
    }


def contains_all(output: str, expected: List[str]) -> dict:
    """Check if ALL expected strings are contained in the output (case-insensitive)."""
    out = strip_chat_markup(output).lower()
    found = 0
    missing = []
    for exp in expected:
        if exp.lower() in out:
            found += 1
        else:
            missing.append(exp)
    score = found / len(expected) if expected else 1.0
    passed = score >= 1.0
    return {
        "passed": passed,
        "score": score,
        "details": f"Found {found}/{len(expected)}: missing={missing}" if not passed else f"All {len(expected)} items found"
    }


def contains_any(output: str, expected: List[str]) -> dict:
    """Check if ANY of the expected strings are contained in the output."""
    out = strip_chat_markup(output).lower()
    found = [e for e in expected if e.lower() in out]
    score = len(found) / len(expected) if expected else 1.0
    passed = len(found) > 0
    return {
        "passed": passed,
        "score": score,
        "details": f"Found {len(found)}/{len(expected)}: {found[:3]}" if not passed else f"Found: {found[:3]}"
    }


def numeric_match(output: str, expected: str) -> dict:
    """Check if a number in the output matches expected."""
    stripped = strip_chat_markup(output)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', stripped)
    exp_num = re.findall(r'-?\d+(?:\.\d+)?', expected)[0] if re.findall(r'-?\d+(?:\.\d+)?', expected) else expected
    passed = exp_num in numbers
    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "details": f"Expected number '{expected}', found numbers {numbers}" if not passed else f"Numeric match: {exp_num}"
    }


def step_by_step(output: str, expected: str) -> dict:
    """
    For reasoning tasks: check that the model shows working AND reaches the right answer.
    Expected format: "final_answer|keyword1,keyword2"
    """
    parts = expected.split("|")
    final_answer = parts[0].strip()
    keywords = [k.strip() for k in parts[1].split(",")] if len(parts) > 1 else []

    out_lower = strip_chat_markup(output).lower()
    has_answer = final_answer.lower() in out_lower
    found_keywords = [k for k in keywords if k.lower() in out_lower]
    keyword_score = len(found_keywords) / len(keywords) if keywords else 1.0
    has_working = any(marker in out_lower for marker in ["step", "first", "then", "finally", "therefore"]) or output.count("\n") >= 3

    score = (0.5 * (1.0 if has_answer else 0.0) +
             0.3 * keyword_score +
             0.2 * (1.0 if has_working else 0.0))

    passed = has_answer and keyword_score >= 0.5
    return {
        "passed": passed,
        "score": round(score, 2),
        "details": (f"Answer in output: {has_answer}, "
                    f"Keywords: {found_keywords}/{keywords}, "
                    f"Working shown: {has_working}")
    }


def intent_fields(
    output: str,
    expected: dict,
    *,
    abstention_operations: List[str] | None = None,
    allow_abstention: bool = False,
) -> dict:
    """Deterministically score an existing grammar-constrained Intent by fields."""
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
    passed = intent.operation.value == expected_operation and intent.arguments == expected_arguments
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


# Registry of evaluators by name
EVALUATORS = {
    "exact_match": exact_match,
    "contains": contains,
    "contains_all": contains_all,
    "contains_any": contains_any,
    "numeric_match": numeric_match,
    "step_by_step": step_by_step,
}


def evaluate_task(output: str, task: dict, *, allow_abstention: bool = False) -> dict:
    """Run the appropriate evaluator for a task."""
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


def quick_test():
    """Test all legacy evaluators."""
    print("=== Evaluator + Stripper Tests ===\n")
    tests = [
        ("yes\n<|user|>", "yes"),
        ("no\n</|end|>", "no"),
        ("  Yes  ", "Yes"),
        ("answer: 47\n\n<|endoftext|>", "answer: 47"),
        ("Thinking...\n\nResponse: The capital is Paris.", "The capital is Paris."),
    ]
    for raw, expected in tests:
        stripped = strip_chat_markup(raw)
        status = "✅" if stripped.lower() == expected.lower() else "❌"
        print(f"{status} strip({raw!r}) → {stripped!r} (expected {expected!r})")

    r = exact_match("yes\n<|user|>", "yes")
    print(f"exact_match: passed={r['passed']}")
    r = contains("The capital of France is Paris.", "Paris")
    print(f"contains: {r}")
    r = contains_all("Alice and Charlie are assigned.", ["Alice", "Charlie"])
    print(f"contains_all: {r}")
    r = step_by_step("First Diana reports to Charlie. Then Charlie reports to Bob.", "Bob|reports")
    print(f"step_by_step: {r}")


if __name__ == "__main__":
    quick_test()
