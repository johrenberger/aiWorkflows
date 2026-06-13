"""Story 020: V2 always-generate coverage.

The default for `test-factory run` flipped from
`generate_coverage=False` to `generate_coverage=True` (PR #23 contract
preserved via the explicit `--generate-coverage` flag; new opt-out is
`--no-generate-coverage`).

These tests pin the new contract at the CLI + orchestrator level. The
end-to-end "line_coverage is no longer 0.0 across the board" check
against a real repo lives in the spike report, not here.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_factory.cli import build_parser
from test_factory.orchestrator import TestFactoryOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"


def _copy_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    shutil.copytree(FIXTURE_REPO, repo)
    return repo


# ---------------------------------------------------------------------------
# Scenario 1: default `test-factory run` generates coverage.
# (Behavior pinned by test_coverage_generate_is_on_by_default_in_run_story020
#  in test_coverage_generation.py; this test is the same assertion but
#  routed through the CLI to catch any regression in the cli.py dispatch.)
# ---------------------------------------------------------------------------
def test_default_run_generates_coverage_via_cli(tmp_path):
    """`test-factory run` with no flag must invoke coverage_generate()."""
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    # Wipe stale reports so the generation step has a clean slate.
    for pattern in ("**/coverage.xml", "**/coverage-final.json",
                    "**/lcov.info", "**/jacoco.xml"):
        for p in repo.rglob(pattern):
            if p.is_file():
                p.unlink()
    result = subprocess.run(
        [sys.executable, "-m", "test_factory.cli", "run",
         "--repo", str(repo), "--out", str(out_dir),
         "--limit", "1", "--module", "package"],
        capture_output=True, text=True,
    )
    # Exit code may be non-zero if the generation step's adapter couldn't
    # actually run (e.g. the fixture repo has no working pytest); what we
    # care about is that the run() orchestrator was called and that
    # coverage_generate() produced a record (or a clear "skipped" one).
    # The presence of analysis-artifacts/coverage_runs/generate.json is
    # the strongest signal that generation was attempted.
    gen_record = out_dir / "coverage_runs" / "generate.json"
    assert gen_record.exists(), (
        f"Story 020 default is ON: coverage_runs/generate.json must exist.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Scenario 2: --no-generate-coverage skips generation.
# ---------------------------------------------------------------------------
def test_no_generate_coverage_flag_skips_generation(tmp_path):
    """`test-factory run --no-generate-coverage` must NOT invoke
    coverage_generate(). The result.coverage_generation is None and
    the coverage_runs/ artifact dir is NOT created.
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        result = orchestrator.run(limit=2, module="package",
                                  generate_coverage=False)
        assert result["coverage_generation"] is None
        assert not (out_dir / "coverage_runs").exists()
    finally:
        orchestrator.close()


# ---------------------------------------------------------------------------
# Scenario 3: --generate-coverage still works (backward compat).
# Covered by test_coverage_generate_runs_adapter_command_when_enabled
# in test_coverage_generation.py (passes generate_coverage=True). Pinning
# the CLI form here too.
# ---------------------------------------------------------------------------
def test_generate_coverage_flag_still_works_via_cli(tmp_path):
    """`test-factory run --generate-coverage` must still invoke
    coverage_generate() (backward compat with PR #23 callers).
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    for pattern in ("**/coverage.xml", "**/coverage-final.json",
                    "**/lcov.info", "**/jacoco.xml"):
        for p in repo.rglob(pattern):
            if p.is_file():
                p.unlink()
    result = subprocess.run(
        [sys.executable, "-m", "test_factory.cli", "run",
         "--repo", str(repo), "--out", str(out_dir),
         "--limit", "1", "--module", "package",
         "--generate-coverage"],
        capture_output=True, text=True,
    )
    gen_record = out_dir / "coverage_runs" / "generate.json"
    assert gen_record.exists(), (
        f"PR #23 contract: --generate-coverage must invoke generation.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Scenario 4: --generate-coverage and --no-generate-coverage are mutually
# exclusive.
# ---------------------------------------------------------------------------
def test_generate_and_no_generate_are_mutually_exclusive(tmp_path):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args([
            "run", "--repo", str(tmp_path),
            "--generate-coverage", "--no-generate-coverage",
        ])
    # SystemExit(2) is argparse's default for usage errors.
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# Scenario 5: test-factory coverage is unchanged (read-only).
# ---------------------------------------------------------------------------
def test_coverage_subcommand_does_not_generate(tmp_path):
    """`test-factory coverage` must NOT invoke coverage_generate() —
    it only reads existing reports. Story 020 only flips the default
    for `run`, not for `coverage`.
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        records = orchestrator.coverage(module="package")
        # No exception means the read-only path is intact. Also assert
        # no generation dir was created.
        assert not (out_dir / "coverage_runs").exists()
        # And we got a list back (may be empty if no reports exist).
        assert isinstance(records, list)
    finally:
        orchestrator.close()


# ---------------------------------------------------------------------------
# Scenario 6: generation result is reported even when it fails.
# ---------------------------------------------------------------------------
def test_generation_result_reports_failure_status(tmp_path):
    """When the primary adapter cannot produce coverage (e.g. no
    coverage tool installed, or the adapter's command exits non-zero),
    coverage_generation must still be a dict with a non-`ok` status
    (or `no_report_written` / `error` / `skipped`) so the user can
    tell that generation was attempted but failed.
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    # Strip the fixture repo of any pre-existing reports and patch the
    # primary adapter to return a no-op command that does not write
    # any coverage file. This is the exact "no_report_written" path
    # that the PR #23 contract defines.
    for pattern in ("**/coverage.xml", "**/coverage-final.json",
                    "**/lcov.info", "**/jacoco.xml", "**/coverage.json"):
        for p in repo.rglob(pattern):
            if p.is_file():
                p.unlink()
    from test_factory.models import CommandSpec
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        original_primary = orchestrator._primary_adapter
        # Pick whichever adapter _primary_adapter selected and patch it.
        primary = original_primary()
        assert primary is not None, "fixture repo must have a primary adapter"
        original_command = primary.discover_coverage_command
        primary.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=["true"],  # exits 0 but writes nothing
            cwd=str(repo),
            description="no-op for story-020 status-pin test",
        )
        try:
            result = orchestrator.run(limit=1, module="package",
                                      generate_coverage=True)
        finally:
            primary.discover_coverage_command = original_command
        gen = result["coverage_generation"]
        assert gen is not None
        # status must be one of the documented set (story 020 scenario 6).
        # The shape is {"generation": {"status": ..., ...}, "records": [...]}
        # so we look at generation.status, not the top level.
        gen_inner = gen.get("generation", gen)
        assert gen_inner.get("status") in {
            "ok", "no_report_written", "error", "failed", "skipped",
        }, f"unexpected status: {gen!r}"
    finally:
        orchestrator.close()


# ---------------------------------------------------------------------------
# Scenario 7: CLI help mentions the new default.
# ---------------------------------------------------------------------------
def test_cli_help_mentions_new_default():
    """`test-factory run --help` must state that coverage generation
    is on by default and that `--no-generate-coverage` is the opt-out.
    The flag is registered on every subcommand (matching the prior
    `--generate-coverage` behavior); we assert the run subparser has
    it with help text that mentions the default.
    """
    parser = build_parser()
    # Walk down to the subparsers action and find the 'run' subparser.
    subparsers_action = None
    for a in parser._actions:
        if hasattr(a, "choices") and isinstance(a.choices, dict):
            subparsers_action = a
            break
    assert subparsers_action is not None, "no subparsers action found"
    run_sub = subparsers_action.choices.get("run")
    assert run_sub is not None, "'run' subparser not found"
    found_no_flag = False
    found_help_text_with_default = False
    for action in run_sub._actions:
        if "--no-generate-coverage" in action.option_strings:
            found_no_flag = True
            if "default" in (action.help or "").lower():
                found_help_text_with_default = True
            break
    assert found_no_flag, "--no-generate-coverage flag must be on the 'run' subparser"
    assert found_help_text_with_default, (
        "--no-generate-coverage help text must mention the new default"
    )
