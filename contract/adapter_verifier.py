"""Executable verification of model adapters against the actual tokenizer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from contract.model_adapter import ModelAdapter


class AdapterVerifier:
    """Verify every adapter manifest against its local pinned tokenizer."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.adapters_dir = self.project_root / "contract" / "adapters"
        self.models_dir = self.project_root / "models"

    def verify_all(self) -> List[str]:
        issues: List[str] = []
        if not self.adapters_dir.is_dir():
            return ["No contract/adapters/ directory."]

        manifests = sorted(self.adapters_dir.glob("*.json"))
        if not manifests:
            return ["No adapter manifests found."]

        for path in manifests:
            try:
                with path.open() as f:
                    data = json.load(f)
                issues.extend(self._verify_single(ModelAdapter(data, str(path))))
            except Exception as exc:
                issues.append(f"{path.name}: failed to load adapter: {exc}")
        return issues

    def _verify_single(self, adapter: ModelAdapter) -> List[str]:
        model_path = self.models_dir / adapter.model_id
        if not model_path.is_dir():
            return [f"{adapter.model_id}: model directory not found at {model_path}"]

        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        except Exception as exc:
            return [f"{adapter.model_id}: failed to load tokenizer: {exc}"]

        return adapter.verify(tokenizer)
