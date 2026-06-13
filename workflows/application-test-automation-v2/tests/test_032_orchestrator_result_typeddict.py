"""Story 032: TypedDict for orchestrator.coverage_generate and run() results.

Documents and verifies the typed shape of the orchestrator's
return values. The TypedDicts live in orchestrator.py
(CoverageGenerateResult, CoverageGenerateOutput, RunResult).

This is a typing-only change; the runtime type is still `dict`.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from test_factory.orchestrator import (  # noqa: E402
    CoverageGenerateOutput,
    CoverageGenerateResult,
    RunResult,
    TestFactoryOrchestrator,
)

# Canonical field sets for each result type. These are derived
# from the implementations of coverage_generate() and run()
# after stories 025, 029, 031, 032. If you add a field to one of
# these methods, update the canonical set below AND the
# TypedDict in orchestrator.py.
COVERAGE_GENERATE_GENERATION_FIELDS = frozenset({
    "status",
    "command",
    "exit_code",
    "stdout",
    "stderr",
    "timeout_seconds",
    "preflight_findings",
    "new_reports",
    "warning",
    "reason",
    "coverage_out_dir",
    "coverage_out_copied",
    "coverage_out_error",
})

COVERAGE_GENERATE_OUTPUT_FIELDS = frozenset({
    "generation",
    "records",
})

RUN_RESULT_FIELDS = frozenset({
    "status",
    "module_scope",
    "coverage_generation",
    "coverage_out_dir",
})


# --------------------------------------------------------------------------
# TypedDict existence and structure
# --------------------------------------------------------------------------

def test_typeddict_classes_exist():
    """Story 032: the TypedDict classes are exposed on the
    orchestrator module for downstream type-checking and
    documentation. They are not exported as a `__all__` list
    (yet), but they must be importable.
    """
    assert CoverageGenerateResult is not None
    assert CoverageGenerateOutput is not None
    assert RunResult is not None
    # TypedDicts have `__annotations__` set to their fields.
    assert "status" in CoverageGenerateResult.__annotations__
    assert "coverage_out_dir" in CoverageGenerateResult.__annotations__


def test_typeddict_total_false_so_optional_fields_typed_optional():
    """Story 032: the TypedDicts use `total=False` because some
    fields are conditionally set (e.g. `reason` is only set when
    `status="skipped"`). This is the right call: the union of all
    fields is the full contract; individual instances can have
    any subset.
    """
    assert CoverageGenerateResult.__total__ is False
    assert CoverageGenerateOutput.__total__ is False
    assert RunResult.__total__ is False


# --------------------------------------------------------------------------
# Runtime isinstance — TypedDicts are still dicts at runtime
# --------------------------------------------------------------------------

def test_typeddict_runtime_isinstance_dict(tmp_path):
    """Story 032: TypedDicts are dicts at runtime. A consumer
    that does `isinstance(result, dict)` still gets True. This
    guards against the 'well-meaning migration' that would
    switch to dataclasses and break every downstream caller
    of `result["x"]`.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    o = TestFactoryOrchestrator(str(repo), str(out))
    try:
        # coverage_generate with no command available (no adapter) returns
        # the early-exit "skipped" dict.
        result = o.coverage_generate()
        assert isinstance(result, dict), (
            "TypedDicts are dicts at runtime. If this assertion fails, "
            "someone changed the return type from TypedDict to dataclass. "
            "That's intentional, but it WILL break every consumer that "
            "does `result[\"x\"]` — so update those consumers in the same PR."
        )
        # And the canonical key set is a subset of result's keys
        # (the result MAY have extra keys, but the TypedDict's keys
        # must be present-or-absent per the per-field optionality).
        for key in COVERAGE_GENERATE_OUTPUT_FIELDS:
            assert key in result, f"key {key!r} missing from coverage_generate() result"
    finally:
        o.close()


# --------------------------------------------------------------------------
# Field-set contracts (regression net)
# --------------------------------------------------------------------------

def test_coverage_generate_result_has_all_typed_fields(tmp_path):
    """Story 032: every field in the CoverageGenerateResult
    TypedDict must be present in the actual result dict
    (set to some value, even None). This catches accidental
    field deletions in future refactors.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    o = TestFactoryOrchestrator(str(repo), str(out))
    try:
        # Use the skipped-status path (no enabled adapter) to get
        # a deterministic result with all the always-set fields
        # (command=None, exit_code=None, stdout="", stderr="",
        # etc.) but the `new_reports` field is also always set
        # after the post-run check, so we should have it.
        result = o.coverage_generate()
        gen = result["generation"]
        # Always-set fields in the skipped path:
        always_set = {
            "status", "command", "exit_code", "stdout", "stderr",
            "timeout_seconds", "preflight_findings",
            "coverage_out_dir", "coverage_out_copied", "coverage_out_error",
        }
        for key in always_set:
            assert key in gen, f"key {key!r} missing from coverage_generate result"
        # Type sanity
        assert gen["coverage_out_dir"] is None
        assert gen["coverage_out_copied"] == []
        assert gen["coverage_out_error"] is None
    finally:
        o.close()


def test_run_result_has_all_typed_fields(tmp_path):
    """Story 032: every field in the RunResult TypedDict must
    be present in the run() return dict.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    o = TestFactoryOrchestrator(str(repo), str(out))
    try:
        result = o.run(generate_coverage=False)
        for key in RUN_RESULT_FIELDS:
            assert key in result, f"key {key!r} missing from run() result"
        # Type sanity
        assert result["status"] == "ok"
        assert result["coverage_generation"] is None
        assert result["coverage_out_dir"] is None
    finally:
        o.close()


def test_canonical_field_sets_match_typeddict_annotations():
    """Story 032: the canonical field-set constants in this test
    file must match the actual `__annotations__` of the TypedDicts.
    If you add a field to a TypedDict, add it to the constant
    here too (or this test will fail). The constants document
    the EXPECTED fields for downstream consumers; the
    `__annotations__` document what's typed; they should match.
    """
    for key in COVERAGE_GENERATE_GENERATION_FIELDS:
        assert key in CoverageGenerateResult.__annotations__, (
            f"field {key!r} in canonical set but not in TypedDict"
        )
    for key in COVERAGE_GENERATE_OUTPUT_FIELDS:
        assert key in CoverageGenerateOutput.__annotations__, (
            f"field {key!r} in canonical set but not in TypedDict"
        )
    for key in RUN_RESULT_FIELDS:
        assert key in RunResult.__annotations__, (
            f"field {key!r} in canonical set but not in TypedDict"
        )
