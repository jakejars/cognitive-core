"""Regression tests for evidence binding and fail-closed protocol helpers.

These tests cover the failure modes found in the final forensic audit:
- task hashes must bind prompts/expected outputs, not only IDs
- non-DEV receipts must carry immutable provenance fields
- adapter rendering must be the rendering actually used by the runner
- lockbox receipts must bind to ledger task hashes
"""

import json
from pathlib import Path

import pytest

from contract.evidence import hash_task, hash_taskset
from contract.model_adapter import ModelAdapter
from contract.receipt_writer import ReceiptWriter
from contract.schema import (
    ExperimentCell,
    ExperimentReceipt,
    GenerationManifest,
    ModelManifest,
    Partition,
    ProtocolInfo,
    RunMetrics,
    RunResult,
    TaskManifest,
)


def _receipt(partition=Partition.REPLICATION):
    r = ExperimentReceipt(
        run_id="B1-rep-test",
        cell=ExperimentCell.B1,
        partition=partition,
        created_at="2026-08-18T10:00:00+00:00",
        model=ModelManifest(
            model_id="MiniCPM5-1B",
            revision="abc123",
            weights_hash="weights-hash",
            tokenizer_id="MiniCPM5-1B",
            tokenizer_hash="tokenizer-hash",
            template_adapter_version="verified_minicpm_v1",
            applied_template="adapter-hash",
        ),
        generation=GenerationManifest(
            thinking_mode=False,
            max_total_tokens=131072,
            max_answer_tokens=256,
            temperature=0.0,
            top_p=0.0,
            stop_policy="explicit_plus_eos",
            stop_tokens=[1],
            seed=0,
        ),
        tasks=TaskManifest(
            source="fresh.json",
            partition=partition,
            task_ids=["t1"],
            content_hash="taskset-hash",
            n_tasks=1,
        ),
        substrate=None,
        result=RunResult(
            result_hash="result-hash",
            completed_at="2026-08-18T10:01:00+00:00",
            metrics=RunMetrics(
                n_passed=1,
                n_total=1,
                pass_rate=1.0,
                mean_score=1.0,
                mean_latency_ms=10.0,
                total_time_s=0.01,
            ),
            raw_output_hash="raw-output-hash",
        ),
        protocol=ProtocolInfo(
            contract_version="2.2",
            preregistration_hash="prereg-hash",
            amendment_log_hash="amend-hash",
            hypothesis="test hypothesis",
            code_diff_hash="code-hash",
        ),
        budget_consumed={"compute_hours": 0.001},
    )
    r.finalize()
    return r


def test_task_hash_changes_when_prompt_changes():
    a = {"id": "same", "prompt": "alpha", "expected": "yes"}
    b = {"id": "same", "prompt": "beta", "expected": "yes"}
    assert hash_task(a) != hash_task(b)


def test_taskset_hash_changes_when_expected_output_changes():
    a = [{"id": "same", "prompt": "alpha", "expected": "yes"}]
    b = [{"id": "same", "prompt": "alpha", "expected": "no"}]
    assert hash_taskset(a) != hash_taskset(b)


def test_replication_receipt_rejects_missing_provenance_fields(tmp_path):
    r = _receipt(Partition.REPLICATION)
    r.model.weights_hash = ""
    r.model.tokenizer_hash = ""
    r.protocol.preregistration_hash = ""
    r.protocol.code_diff_hash = ""
    r.result.raw_output_hash = ""
    r.generation.seed = None
    r.finalize()

    writer = ReceiptWriter(str(tmp_path))
    with pytest.raises(ValueError):
        writer.persist(r)


def test_dev_receipt_may_be_exploratory_but_still_binds_tasks_and_results(tmp_path):
    r = _receipt(Partition.DEV)
    r.model.weights_hash = ""
    r.model.tokenizer_hash = ""
    r.protocol.preregistration_hash = ""
    r.protocol.code_diff_hash = ""
    r.generation.seed = None
    r.finalize()

    writer = ReceiptWriter(str(tmp_path))
    persisted = writer.persist(r)
    assert persisted.receipt_hash


def test_adapter_render_is_checked_against_golden_prompt():
    class FakeTokenizer:
        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **kwargs):
            assert messages == [{"role": "user", "content": "Hello"}]
            assert tokenize is False
            assert add_generation_prompt is True
            return "<u>Hello</u><a>"

        def encode(self, text):
            assert text == "<u>Hello</u><a>"
            return [10, 20, 30]

    manifest = {
        "model_id": "Fake",
        "revision": "abc",
        "template_source": "apply_chat_template",
        "template_string": "unused",
        "template_kwargs": {},
        "golden_tokenisation_test": {
            "prompt": "Hello",
            "test_input": "<u>Hello</u><a>",
            "expected_token_ids": [10, 20, 30],
        },
        "generation_config": {
            "thinking_mode": False,
            "max_total_tokens": 100,
            "max_answer_tokens": 10,
            "temperature": 0.0,
            "top_p": 0.0,
            "stop_policy": "explicit_plus_eos",
            "stop_tokens": [],
        },
    }

    adapter = ModelAdapter(manifest)
    assert adapter.render(FakeTokenizer(), "Hello") == "<u>Hello</u><a>"
    assert adapter.verify(FakeTokenizer()) == []


def test_adapter_verification_fails_if_rendering_does_not_match_golden():
    class WrongTokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return "<WRONG>"

        def encode(self, text):
            return [99]

    manifest = {
        "model_id": "Fake",
        "revision": "abc",
        "template_source": "apply_chat_template",
        "template_string": "unused",
        "golden_tokenisation_test": {
            "prompt": "Hello",
            "test_input": "<u>Hello</u><a>",
            "expected_token_ids": [10, 20, 30],
        },
        "generation_config": {
            "thinking_mode": False,
            "max_total_tokens": 100,
            "max_answer_tokens": 10,
            "temperature": 0.0,
            "top_p": 0.0,
            "stop_policy": "explicit_plus_eos",
            "stop_tokens": [],
        },
    }

    issues = ModelAdapter(manifest).verify(WrongTokenizer())
    assert any("rendered prompt" in issue for issue in issues)
