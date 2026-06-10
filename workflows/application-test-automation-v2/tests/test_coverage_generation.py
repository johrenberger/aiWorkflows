from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from test_factory.orchestrator import TestFactoryOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"


def _copy_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    shutil.copytree(FIXTURE_REPO, repo)
    return repo


def test_coverage_generate_is_off_by_default_in_run(tmp_path):
    """Regression for PR #23: by default, `run()` should not invoke
    `discover_coverage_command`. The previous behavior was that the
    coverage() step only *reads* existing reports; the user had to
    manually run `coverage run -m pytest && coverage json` before
    `test-factory run`. We preserve that behavior by default; the new
    opt-in `generate_coverage=True` flag triggers the generation step.
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        result = orchestrator.run(limit=2, module="package")
        # generate_coverage not requested, so coverage_generation is None
        assert result["coverage_generation"] is None
        # The coverage_runs/ artifact dir should NOT have been created
        # (orchestrator.coverage_generate was not called).
        assert not (out_dir / "coverage_runs").exists()
    finally:
        orchestrator.close()


def test_coverage_generate_runs_adapter_command_when_enabled(tmp_path):
    """When `generate_coverage=True`, run() invokes the primary adapter's
    `discover_coverage_command` to actually produce a coverage report. We
    patch whichever adapter _primary_adapter() selects for the fixture
    repo and verify:
    1. coverage_generate returns a generation record
    2. the artifact file is written
    3. coverage records are parsed (the post-generation records may
       be empty if no report is produced, but the call must not crash)
    """
    repo = _copy_fixture_repo(tmp_path)
    # The fixture repo has pre-existing coverage reports (coverage.xml,
    # coverage-final.json, lcov.info) used by other tests. For THIS test
    # we want to verify the new-report detection, so wipe them first.
    for stale in repo.rglob("coverage.xml"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("coverage-final.json"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("lcov.info"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("jacoco.xml"):
        if stale.is_file():
            stale.unlink()
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        from test_factory.models import CommandSpec

        primary = orchestrator._primary_adapter()
        assert primary is not None, "fixture should have a detectable primary language"
        coverage_script = repo / "fake_coverage.py"
        coverage_script.write_text(
            "from pathlib import Path\n"
            "xml = '''<coverage><packages><package name=\"package\"><classes><class filename=\"package/foo.py\"><lines><line number=\"1\" hits=\"1\"/><line number=\"2\" hits=\"1\" branch=\"true\" condition-coverage=\"100% (2/2)\"/></lines></class></classes></package></packages></coverage>'''\n"
            "Path('coverage.xml').write_text(xml, encoding='utf-8')\n",
            encoding="utf-8",
        )
        original = primary.discover_coverage_command
        primary.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=[sys.executable, str(coverage_script)],
            cwd=str(repo),
            description="fixture coverage generator",
        )
        try:
            result = orchestrator.run(limit=2, module="package", generate_coverage=True)
        finally:
            primary.discover_coverage_command = original
        gen = result["coverage_generation"]
        assert gen is not None
        assert gen["generation"]["status"] == "completed"
        assert gen["generation"]["exit_code"] == 0
        assert any("coverage.xml" in p for p in gen["generation"].get("new_reports", []))
        # After generation, parsed records should include the package/foo.py
        # entry from the freshly-written coverage.xml.
        paths = {r["path"] for r in gen["records"]}
        assert "package/foo.py" in paths
        # The artifact file was written.
        assert (out_dir / "coverage_runs" / "generate.json").exists()
    finally:
        orchestrator.close()


def test_coverage_generate_handles_missing_binary(tmp_path):
    """If the adapter's discover_coverage_command references a binary
    that doesn't exist, coverage_generate must record a clean failure
    and not crash the pipeline."""
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        from test_factory.models import CommandSpec

        primary = orchestrator._primary_adapter()
        assert primary is not None
        original = primary.discover_coverage_command
        primary.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=["definitely-not-a-real-binary-xyz"],
            cwd=str(repo),
            description="missing binary",
        )
        try:
            result = orchestrator.run(limit=1, module="package", generate_coverage=True)
        finally:
            primary.discover_coverage_command = original
        gen = result["coverage_generation"]
        assert gen is not None
        assert gen["generation"]["status"] == "missing_binary"
        assert gen["generation"]["exit_code"] == 127
        # Pipeline must still complete with status=ok
        assert result["status"] == "ok"
    finally:
        orchestrator.close()
