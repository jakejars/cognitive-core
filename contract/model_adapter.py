"""Model adapter loading, prompt rendering, and runtime generation manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from contract.evidence import hash_json
from contract.schema import GenerationManifest


class ModelAdapter:
    def __init__(self, manifest: dict, source_path: str = ""):
        self.manifest = manifest
        self.source_path = source_path

    @property
    def model_id(self) -> str:
        return self.manifest["model_id"]

    @property
    def revision(self) -> str:
        return self.manifest.get("revision", "")

    @property
    def adapter_hash(self) -> str:
        return hash_json(self.manifest)

    @classmethod
    def load(cls, project_root: str, model_id: str) -> "ModelAdapter":
        adapter_dir = Path(project_root) / "contract" / "adapters"
        for path in sorted(adapter_dir.glob("*.json")):
            with path.open() as f:
                data = json.load(f)
            if data.get("model_id") == model_id:
                return cls(data, str(path))
        raise ValueError(f"No adapter manifest found for model_id={model_id!r}")

    def render(self, tokenizer: Any, prompt: str) -> str:
        source = self.manifest.get("template_source", "")
        if source == "apply_chat_template":
            if not hasattr(tokenizer, "apply_chat_template"):
                raise ValueError(
                    f"Tokenizer for {self.model_id} has no apply_chat_template(), "
                    "but the verified adapter requires it"
                )
            kwargs = dict(self.manifest.get("template_kwargs", {}))
            return tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
                **kwargs,
            )
        if source.startswith("hardcoded_adapter"):
            template = self.manifest.get("template_string", "")
            if "{prompt}" not in template:
                raise ValueError(f"Adapter for {self.model_id} is missing {{prompt}} placeholder")
            return template.format(prompt=prompt)
        raise ValueError(f"Unsupported template_source={source!r} for {self.model_id}")

    def generation_manifest(self, seed: int = 0) -> GenerationManifest:
        cfg = self.manifest.get("generation_config", {})
        required = (
            "thinking_mode",
            "max_total_tokens",
            "max_answer_tokens",
            "temperature",
            "top_p",
            "stop_policy",
            "stop_tokens",
        )
        missing = [key for key in required if key not in cfg]
        if missing:
            raise ValueError(f"Adapter {self.model_id} missing generation config fields: {missing}")
        return GenerationManifest(
            thinking_mode=bool(cfg["thinking_mode"]),
            max_total_tokens=int(cfg["max_total_tokens"]),
            max_answer_tokens=int(cfg["max_answer_tokens"]),
            temperature=float(cfg["temperature"]),
            top_p=float(cfg["top_p"]),
            stop_policy=str(cfg["stop_policy"]),
            stop_tokens=[int(x) for x in cfg.get("stop_tokens", [])],
            seed=seed,
        )

    def verify(self, tokenizer: Any) -> List[str]:
        issues: List[str] = []
        golden = self.manifest.get("golden_tokenisation_test", {})
        prompt = golden.get("prompt")
        expected_rendered = golden.get("test_input")
        expected_ids = golden.get("expected_token_ids")
        if not prompt or not expected_rendered or not isinstance(expected_ids, list) or not expected_ids:
            return [f"{self.model_id}: golden test requires prompt, test_input, and expected_token_ids"]

        try:
            rendered = self.render(tokenizer, prompt)
        except Exception as exc:
            return [f"{self.model_id}: adapter render failed: {exc}"]

        if rendered != expected_rendered:
            issues.append(
                f"{self.model_id}: rendered prompt does not match golden test input"
            )

        try:
            actual_ids = list(tokenizer.encode(rendered))
        except Exception as exc:
            issues.append(f"{self.model_id}: tokenizer encode failed: {exc}")
            return issues

        if actual_ids != expected_ids:
            issues.append(
                f"{self.model_id}: golden token IDs differ; expected {expected_ids}, got {actual_ids}"
            )
        return issues
