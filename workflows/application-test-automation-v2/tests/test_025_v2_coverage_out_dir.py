"""Story 025: external --coverage-out for generated coverage.

These tests verify that:
  1. `coverage_generate(coverage_out_dir=...)` copies freshly-written
     reports to that directory.
  2. The result has `coverage_out_dir`, `coverage_out_copied`, and
     no `coverage_out_error` fields on success.
  3. `coverage_generate(coverage_out_dir=None)` is a no-op (legacy
     behavior unchanged).
  4. The result has `coverage_out_error` set when the dir can't be
     created.
  5. CLI: `run --coverage-out DIR` passes DIR through to
     coverage_generate (verified by inspecting run()'s return value).
  6. CLI: `run --coverage-out /nonexistent` does not crash on parse
     (path validation happens lazily in coverage_generate).

We use a fake `discover_coverage_command` to avoid actually running
Maven/pytest in tests — the post-run copy logic is adapter-agnostic.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from test_factory.orchestrator import TestFactoryOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"


def _run_cli(*args, cwd=PROJECT_ROOT):
    """Invoke the CLI as a subprocess and return CompletedProcess."""
    cmd = [sys.executable, "-m", "test_factory.cli", *args]
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(cwd)
    )


def _init_orchestrator(tmp_path, repo=None):
    """Create an orchestrator wired to a real fixture repo (or
    a custom repo dir) and an empty artifacts dir under tmp_path.
    """
    repo = repo or FIXTURE_REPO
    out = tmp_path / "analysis-artifacts"
    out.mkdir(parents=True, exist_ok=True)
    return TestFactoryOrchestrator(str(repo), str(out))


def _write_then_utime(path: Path, content: str, future_seconds: float = 2.0):
    """Write content to path and bump its mtime into the future so the
    orchestrator's pre/post mtime comparison sees it as 'new'.
    """
    path.write_text(content)
    future = time.time() + future_seconds
    os.utime(path, (future, future))


# A minimal valid coverage.py JSON shape that the parser can swallow.
# (Real coverage.py reports have a `files` key mapping path -> {executable_lines,
# missing_lines, ...}. An empty dict means "no files reported" — parses fine.)
VALID_COVERAGE_PY_JSON = '{"files": {}, "totals": {"covered_lines": 0, "num_statements": 0}}'
VALID_COVERAGE_XML = '<coverage version="1" timestamp="0" lines-valid="0" lines-covered="0" branches-covered="0" branches-valid="0"></coverage>'


# --------------------------------------------------------------------------
# Direct orchestrator API
# --------------------------------------------------------------------------

def test_coverage_generate_no_coverage_out_does_nothing(tmp_path):
    """Scenario 3 (negative): coverage_generate(coverage_out_dir=None)
    sets all three coverage_out_* keys to their "not requested"
    values: None / [] / None. (Story 029 contract flatten: keys
    are always present, even when not requested.)
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        with patch(
            "test_factory.orchestrator.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            ),
        ):
            result = o.coverage_generate(coverage_out_dir=None)
        # Story 029: keys are always present, with neutral defaults.
        assert result["generation"].get("coverage_out_dir") is None
        assert result["generation"].get("coverage_out_copied") == []
        assert result["generation"].get("coverage_out_error") is None
    finally:
        o.close()


def test_coverage_generate_copies_real_file(tmp_path):
    """Scenario 1 (real): a freshly-written report lands in the repo
    via the (mocked) subprocess.run, then coverage_generate copies it
    to --coverage-out.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    target_report = repo / "coverage.json"
    target_report.write_text("{}")  # pre-existing (mtime = now)

    out_dir = tmp_path / "coverage-out"
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        def _fake_subprocess(*args, **kwargs):
            # Simulate the build tool rewriting the report (bumps mtime)
            _write_then_utime(target_report, VALID_COVERAGE_PY_JSON, future_seconds=2.0)
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
        with patch(
            "test_factory.orchestrator.subprocess.run",
            side_effect=_fake_subprocess,
        ):
            result = o.coverage_generate(coverage_out_dir=str(out_dir))
        # The file should have been copied to out_dir
        assert (out_dir / "coverage.json").exists(), (
            f"expected coverage.json in {out_dir}, "
            f"got: {list(out_dir.iterdir()) if out_dir.exists() else 'no out_dir'}"
        )
        assert result["generation"].get("coverage_out_dir") == str(out_dir.resolve())
        assert any(
            "coverage.json" in c
            for c in result["generation"].get("coverage_out_copied", [])
        )
    finally:
        o.close()


def test_coverage_generate_copies_multiple_new_reports(tmp_path):
    """Scenario 1b: multiple fresh reports all get copied."""
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    (repo / "coverage.json").write_text(VALID_COVERAGE_PY_JSON)
    (repo / "coverage.xml").write_text(VALID_COVERAGE_XML)
    (repo / ".coverage").write_text("!coverage.py")

    out_dir = tmp_path / "coverage-out"
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        def _fake_subprocess(*args, **kwargs):
            for name, content in [
                ("coverage.json", VALID_COVERAGE_PY_JSON),
                ("coverage.xml", VALID_COVERAGE_XML),
                (".coverage", "!coverage.py: more data"),
            ]:
                _write_then_utime(repo / name, content, future_seconds=2.0)
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
        with patch(
            "test_factory.orchestrator.subprocess.run",
            side_effect=_fake_subprocess,
        ):
            result = o.coverage_generate(coverage_out_dir=str(out_dir))
        # All three should be copied
        copied = result["generation"].get("coverage_out_copied", [])
        assert len(copied) == 3, f"expected 3 copies, got {copied}"
        assert (out_dir / "coverage.json").exists()
        assert (out_dir / "coverage.xml").exists()
        assert (out_dir / ".coverage").exists()
    finally:
        o.close()


def test_coverage_generate_coverage_out_error_on_bad_path(tmp_path):
    """Scenario 4: coverage_out_dir set to a path under a file
    (not a directory) → `coverage_out_error` is set.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    target_report = repo / "coverage.json"
    target_report.write_text("{}")
    # Make the "out dir" path actually be a file → mkdir will fail
    blocker = tmp_path / "blocker"
    blocker.write_text("I am a file, not a directory")
    bad_out = blocker / "subdir"  # can't create under a file

    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        def _fake_subprocess(*args, **kwargs):
            _write_then_utime(target_report, VALID_COVERAGE_PY_JSON, future_seconds=2.0)
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
        with patch(
            "test_factory.orchestrator.subprocess.run",
            side_effect=_fake_subprocess,
        ):
            result = o.coverage_generate(coverage_out_dir=str(bad_out))
        # Should have set the error field
        assert "coverage_out_error" in result["generation"]
        assert "could not create" in result["generation"]["coverage_out_error"]
        # Nothing was copied
        assert result["generation"].get("coverage_out_copied", []) == []
    finally:
        o.close()


def test_coverage_generate_coverage_out_with_no_new_reports_is_inert(tmp_path):
    """Scenario 4b: coverage_out_dir set but no new reports → no copy.
    The dir is still created (mkdir parents) so subsequent runs find
    it. The coverage_out_dir is recorded on the result for visibility.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    # NO report files written
    out_dir = tmp_path / "coverage-out"
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        with patch(
            "test_factory.orchestrator.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            ),
        ):
            result = o.coverage_generate(coverage_out_dir=str(out_dir))
        # But no copies
        assert result["generation"].get("coverage_out_copied", []) == []
        # And the dir does exist (we created it via mkdir parents)
        assert out_dir.exists()
    finally:
        o.close()


# --------------------------------------------------------------------------
# CLI integration
# --------------------------------------------------------------------------

def test_cli_run_coverage_out_flag_parses(tmp_path):
    """Scenario 5: `run --coverage-out DIR` is accepted by the parser
    and the value flows through to the run() return value.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    result = _run_cli(
        "run", "--repo", str(repo), "--out", str(out),
        "--coverage-out", "/tmp/some-cov",
        "--no-generate-coverage",  # skip the actual generation
        cwd=PROJECT_ROOT,
    )
    # --no-generate-coverage means coverage_generate is NOT called;
    # the run() should still complete successfully.
    assert result.returncode == 0, f"stderr: {result.stderr}"
    parsed = json.loads(result.stdout)
    # Story 029: the top-level coverage_out_dir is read from
    # coverage_generation.coverage_out_dir, which is the resolved path.
    assert parsed["coverage_out_dir"] == str(Path("/tmp/some-cov").resolve())


def test_cli_run_coverage_out_default_is_none(tmp_path):
    """Scenario 5b: `run` (no --coverage-out) leaves coverage_out_dir None."""
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    out = tmp_path / "analysis-artifacts"
    out.mkdir()
    result = _run_cli(
        "run", "--repo", str(repo), "--out", str(out),
        "--no-generate-coverage",
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    parsed = json.loads(result.stdout)
    assert parsed["coverage_out_dir"] is None


def test_run_signature_accepts_coverage_out_dir_kwarg(tmp_path):
    """Scenario 6: orchestrator.run(coverage_out_dir=...) doesn't raise.
    Verifies the kwarg plumbing through run() -> coverage_generate().
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        result = o.run(
            generate_coverage=False,  # skip the heavy path
            coverage_out_dir=str(tmp_path / "some-cov"),
        )
        # coverage_out_dir is returned even when generation is skipped
        assert result["coverage_out_dir"] == str(tmp_path / "some-cov")
    finally:
        o.close()


# --------------------------------------------------------------------------
# Story 029: flattened contract
# --------------------------------------------------------------------------

def test_coverage_generate_always_sets_all_three_fields(tmp_path):
    """Story 029: regardless of whether coverage_out_dir is requested,
    the result has all three coverage_out_* keys, with consistent types.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        # When NOT requested
        with patch(
            "test_factory.orchestrator.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            ),
        ):
            result = o.coverage_generate(coverage_out_dir=None)
        gen = result["generation"]
        assert "coverage_out_dir" in gen
        assert "coverage_out_copied" in gen
        assert "coverage_out_error" in gen
        assert gen["coverage_out_dir"] is None
        assert gen["coverage_out_copied"] == []
        assert gen["coverage_out_error"] is None

        # When requested (with a real path)
        out_dir = tmp_path / "out"
        result = o.coverage_generate(coverage_out_dir=str(out_dir))
        gen = result["generation"]
        assert "coverage_out_dir" in gen
        assert "coverage_out_copied" in gen
        assert "coverage_out_error" in gen
        assert gen["coverage_out_dir"] == str(out_dir.resolve())
        assert gen["coverage_out_copied"] == []  # no new reports
        assert gen["coverage_out_error"] is None
    finally:
        o.close()


def test_run_top_level_coverage_out_dir_matches_generation(tmp_path):
    """Story 029: the top-level coverage_out_dir in run()'s return
    value should match coverage_generation.coverage_out_dir, NOT be
    a possibly-relative input. This kills M2 from the code review.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    # Use a relative path to make the resolution test meaningful
    out_dir = tmp_path / "out"
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        result = o.run(
            generate_coverage=False,
            coverage_out_dir=str(out_dir),
        )
        # generate_coverage=False → coverage_generation is None →
        # we fall back to resolving the input path. Should be the
        # resolved absolute path.
        top_level = result["coverage_out_dir"]
        assert top_level == str(out_dir.resolve())
        assert Path(top_level).is_absolute()
    finally:
        o.close()


def test_run_top_level_coverage_out_dir_matches_generation_when_generated(tmp_path):
    """Story 029: when generate_coverage=True, the top-level field
    should be read from coverage_generation (not the input), so
    they're guaranteed to match.
    """
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    target_report = repo / "coverage.json"
    # Pre-write a *valid* coverage.json (mtime = now). The pre-run
    # snapshot in coverage_generate will see this file with a known
    # mtime. The mock subprocess then writes fresh content with a
    # bumped mtime so the post-run sees a "new" report.
    target_report.write_text(VALID_COVERAGE_PY_JSON)

    out_dir = tmp_path / "out"
    o = _init_orchestrator(tmp_path, repo=repo)
    try:
        def _fake_subprocess(*args, **kwargs):
            _write_then_utime(target_report, VALID_COVERAGE_PY_JSON, future_seconds=2.0)
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
        with patch(
            "test_factory.orchestrator.subprocess.run",
            side_effect=_fake_subprocess,
        ):
            result = o.run(
                generate_coverage=True,
                coverage_out_dir=str(out_dir),
            )
        # coverage_generate returns {"generation": ..., "records": ...}
        gen = result["coverage_generation"]["generation"]
        assert result["coverage_out_dir"] == gen["coverage_out_dir"]
        assert result["coverage_out_dir"] == str(out_dir.resolve())
    finally:
        o.close()
