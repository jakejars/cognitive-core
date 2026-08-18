"""Canonical evidence hashing helpers for Cognitive Core experiment receipts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable, Sequence


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_json(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_bytes(canonical.encode("utf-8"))


def hash_task(task: dict) -> str:
    """Bind a task to its full definition, not merely its task ID."""
    return hash_json(task)


def hash_taskset(tasks: Sequence[dict]) -> str:
    """Hash the ordered set of canonical per-task hashes."""
    return hash_json([hash_task(task) for task in tasks])


def hash_files(paths: Iterable[str | os.PathLike[str]], base: str | os.PathLike[str] | None = None) -> str:
    """Hash file names and file contents into one deterministic digest."""
    base_path = Path(base).resolve() if base is not None else None
    rows = []
    for raw in sorted(Path(p).resolve() for p in paths):
        if not raw.is_file():
            continue
        name = str(raw.relative_to(base_path)) if base_path and raw.is_relative_to(base_path) else str(raw)
        rows.append((name, sha256_file(raw)))
    if not rows:
        raise ValueError("no files available to hash")
    return hash_json(rows)


def hash_model_weights(model_dir: str | os.PathLike[str]) -> str:
    """Cryptographically fingerprint local weight bytes.

    This is intentionally expensive the first time; confirmation evidence should
    bind to the exact checkpoint bytes that were evaluated.
    """
    root = Path(model_dir)
    candidates = []
    for pattern in ("*.safetensors", "*.npz", "*.bin"):
        candidates.extend(root.glob(pattern))
    return hash_files(candidates, root)


def hash_tokenizer(model_dir: str | os.PathLike[str]) -> str:
    root = Path(model_dir)
    names = (
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "tokenizer.model",
        "spiece.model",
    )
    files = [root / name for name in names if (root / name).is_file()]
    return hash_files(files, root)


def hash_tree(root: str | os.PathLike[str], suffixes: tuple[str, ...] = (".py", ".json", ".toml", ".yaml", ".yml")) -> str:
    base = Path(root)
    files = [p for p in base.rglob("*") if p.is_file() and p.suffix in suffixes]
    return hash_files(files, base)


def git_code_diff_hash(project_root: str | os.PathLike[str]) -> str:
    """Bind a run to HEAD plus the exact working-tree diff.

    Raises if git metadata is unavailable rather than silently recording an empty
    value for confirmatory evidence.
    """
    root = str(Path(project_root).resolve())
    head = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
    diff = subprocess.check_output(
        ["git", "-C", root, "diff", "--binary", "HEAD"],
        text=True,
        errors="replace",
    )
    return hash_json({"head": head, "diff": diff})
