"""
Adapter Verifier — executable tokenizer verification for model adapters.

Contract §2, §3.4: Every model must have a verified adapter with golden
tokenisation tests. This module loads the actual tokenizer and verifies
that encoding produces the expected token IDs.

The research agent cannot modify this verifier — it is in the contract/
package which is read-only to the researcher in production.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple


class AdapterVerifier:
    """
    Verifies model adapter manifests against actual tokenizers.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.adapters_dir = os.path.join(project_root, "contract", "adapters")
        self.models_dir = os.path.join(project_root, "models")

    def verify_all(self) -> List[str]:
        """
        Verify every adapter in contract/adapters/.
        Returns a list of issue strings (empty if all pass).
        """
        issues = []
        if not os.path.isdir(self.adapters_dir):
            return ["No contract/adapters/ directory."]

        for af in sorted(os.listdir(self.adapters_dir)):
            if not af.endswith(".json"):
                continue
            path = os.path.join(self.adapters_dir, af)
            with open(path) as f:
                data = json.load(f)
            mid = data.get("model_id", af.replace(".json", ""))
            adapter_issues = self._verify_single(mid, data)
            issues.extend(adapter_issues)

        return issues

    def _verify_single(self, model_id: str, data: dict) -> List[str]:
        """Verify a single adapter manifest."""
        issues = []

        # Structural checks
        if not data.get("template_source"):
            issues.append(f"  {model_id}: missing template_source")
        if not data.get("template_string"):
            issues.append(f"  {model_id}: missing template_string")
        if not data.get("generation_config"):
            issues.append(f"  {model_id}: no generation_config")

        # Golden tokenisation test
        g = data.get("golden_tokenisation_test", {})
        test_input = g.get("test_input")
        expected_ids = g.get("expected_token_ids")

        if not test_input:
            issues.append(f"  {model_id}: golden_tokenisation_test missing test_input")
        if not expected_ids:
            issues.append(f"  {model_id}: golden_tokenisation_test missing expected_token_ids")
        elif not isinstance(expected_ids, list):
            issues.append(f"  {model_id}: expected_token_ids must be a list")
        elif len(expected_ids) == 0:
            issues.append(f"  {model_id}: expected_token_ids is empty")

        # If we have both test_input and expected_ids, try to verify with the actual tokenizer
        if test_input and expected_ids and isinstance(expected_ids, list) and len(expected_ids) > 0:
            tokenizer_issues = self._verify_tokenizer(model_id, test_input, expected_ids)
            issues.extend(tokenizer_issues)

        return issues

    def _verify_tokenizer(
        self,
        model_id: str,
        test_input: str,
        expected_ids: List[int],
    ) -> List[str]:
        """Load the actual tokenizer and verify encoding matches expected token IDs."""
        model_path = os.path.join(self.models_dir, model_id)
        if not os.path.isdir(model_path):
            return [f"  {model_id}: model directory not found at {model_path}"]

        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        except Exception as e:
            return [f"  {model_id}: failed to load tokenizer: {e}"]

        try:
            actual_ids = tokenizer.encode(test_input)
        except Exception as e:
            return [f"  {model_id}: tokenizer encode failed: {e}"]

        issues = []
        if len(actual_ids) < len(expected_ids):
            issues.append(
                f"  {model_id}: expected {len(expected_ids)} tokens but got {len(actual_ids)}"
            )
        else:
            for i, (actual, expected) in enumerate(zip(actual_ids[:len(expected_ids)], expected_ids)):
                if actual != expected:
                    issues.append(
                        f"  {model_id}: token mismatch at position {i}: "
                        f"expected {expected}, got {actual}"
                    )
                    break

        return issues