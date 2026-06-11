"""Tests for the --adapter CLI flag (Bug #36 fix).

When the auto-detector picks the wrong primary adapter (e.g. a stray
.java test file tips the tie-break toward java_junit on an otherwise
Python repo), the caller should be able to force a specific adapter.

The flag flows: CLI --adapter → orchestrator.run(adapter_name=...) →
coverage_generate(adapter_name=...) → _primary_adapter(adapter_name=...).
"""
import json
from pathlib import Path

import pytest

from test_factory.cli import build_parser
from test_factory.orchestrator import TestFactoryOrchestrator, _adapter_class_name


def test_adapter_class_name_mapping():
    """The CLI flag values map to the adapter class names."""
    assert _adapter_class_name("python_pytest") == "PythonPytestAdapter"
    assert _adapter_class_name("java_junit") == "JavaJunitAdapter"  # capitalisation comes from adapter module
    assert _adapter_class_name("js_jest_vitest") == "JsJestVitestAdapter"


def test_cli_parser_accepts_adapter_flag():
    """All subcommands should accept --adapter with the three valid choices."""
    parser = build_parser()
    for sub in ("run", "queue", "workitems", "coverage", "score", "validate", "scan", "report"):
        ns = parser.parse_args([sub, "--repo", "/tmp/x", "--out", "/tmp/y", "--adapter", "python_pytest"])
        assert ns.adapter == "python_pytest", f"{sub}: --adapter not parsed"


def test_cli_parser_rejects_unknown_adapter():
    """Unknown adapter names should be rejected by argparse choices=."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--repo", "/tmp/x", "--out", "/tmp/y", "--adapter", "ruby_rspec"])


def test_cli_parser_defaults_to_none():
    parser = build_parser()
    ns = parser.parse_args(["run", "--repo", "/tmp/x", "--out", "/tmp/y"])
    assert ns.adapter is None


def test_primary_adapter_override_returns_named_adapter(tmp_path):
    """Bug #36: _primary_adapter(adapter_name=...) returns the named
    adapter regardless of detect() confidence."""
    repo = tmp_path / "repo"
    repo.mkdir()
    orch = TestFactoryOrchestrator(str(repo), str(tmp_path / "artifacts"))
    try:
        adapter = orch._primary_adapter(adapter_name="python_pytest")
        assert adapter is not None
        assert adapter.__class__.__name__ == "PythonPytestAdapter"
    finally:
        orch.close()


def test_primary_adapter_override_unknown_falls_back_to_auto(tmp_path):
    """If the caller asks for an adapter that isn't loaded, fall back
    to auto-detect rather than silently no-op."""
    repo = tmp_path / "repo"
    repo.mkdir()
    orch = TestFactoryOrchestrator(str(repo), str(tmp_path / "artifacts"))
    try:
        # No such adapter is loaded — should still return one of the
        # three real adapters via the auto-detect path.
        adapter = orch._primary_adapter(adapter_name="ruby_rspec")
        assert adapter is not None
        assert adapter.__class__.__name__ in (
            "PythonPytestAdapter",
            "JavaJUnitAdapter",
            "JsJestVitestAdapter",
        )
    finally:
        orch.close()


def test_run_with_adapter_override_does_not_break_pipeline(tmp_path):
    """End-to-end: orchestrator.run(adapter_name=...) completes the
    full pipeline (no coverage generation here — just verify the flag
    flows through without errors)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n")
    (repo / "foo.py").write_text("def foo():\n    return 1\n")
    (repo / "test_foo.py").write_text("from foo import foo\ndef test_foo():\n    assert foo() == 1\n")
    out = tmp_path / "artifacts"
    orch = TestFactoryOrchestrator(str(repo), str(out))
    try:
        result = orch.run(limit=10, adapter_name="python_pytest")
        assert result["status"] == "ok"
        assert (out / "test_factory.sqlite").exists()
    finally:
        orch.close()
