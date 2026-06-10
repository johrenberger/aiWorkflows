from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from test_factory.orchestrator import TestFactoryOrchestrator
from test_factory.validators import runner as validation_runner


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"


def _copy_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    shutil.copytree(FIXTURE_REPO, repo)
    return repo


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "test_factory.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def test_cli_run_generates_artifacts_from_fixture(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"

    result = _run_cli("run", "--repo", str(repo), "--out", str(out_dir), "--limit", "2", cwd=PROJECT_ROOT)

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert (out_dir / "final_report.md").exists()
    assert (out_dir / "pr_summary.md").exists()
    assert (out_dir / "test_factory.sqlite").exists()
    assert (out_dir / "ai_work_items" / "index.json").exists()


def test_cli_branch_and_commit_from_fixture_repo(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    _git("init", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test User", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "initial snapshot", cwd=repo)

    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        orchestrator.scan()
        orchestrator.coverage()
        orchestrator.score()
        items = orchestrator.workitems(limit=2)
        package_item = next(item for item in items if item.module == "package")
        orchestrator.storage.update_work_item_status(package_item.work_item_id, "passed")
    finally:
        orchestrator.close()

    branch_result = _run_cli("branch", "--repo", str(repo), "--scope", "package", cwd=PROJECT_ROOT)
    branch_payload = json.loads(branch_result.stdout)
    assert branch_payload["created"] is True
    assert branch_payload["branch_name"].startswith("test-automation-v2/")

    (repo / "tests" / "new_test.txt").write_text("hello from branch", encoding="utf-8")
    commit_result = _run_cli("commit", "--repo", str(repo), "--out", str(out_dir), "--module", "package", cwd=PROJECT_ROOT)
    commit_payload = json.loads(commit_result.stdout)
    assert commit_payload["sha"]
    assert commit_payload["message"] == "test: improve coverage for package"
    assert "tests/new_test.txt" in commit_payload["files"]


def test_validate_lifecycle_with_fixture_and_fake_runner(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)

    try:
        orchestrator.scan()
        orchestrator.coverage()
        orchestrator.score()
        items = orchestrator.workitems(limit=1)
        assert items, "expected at least one generated work item"

        original_run = validation_runner.subprocess.run

        def fake_run(cmd, cwd=None, env=None, capture_output=False, text=False, timeout=None, shell=False):
            class Result:
                returncode = 0
                stdout = "validation ok"
                stderr = ""

            return Result()

        validation_runner.subprocess.run = fake_run
        try:
            result = orchestrator.validate(items[0].work_item_id)
        finally:
            validation_runner.subprocess.run = original_run

        assert result["targeted"]["exit_code"] == 0
        assert result["module"]["exit_code"] == 0
        assert result["status"] == "passed"
        assert orchestrator.storage.get_work_item(items[0].work_item_id)["status"] == "passed"
        assert (out_dir / "validation_runs").exists()
        assert any(out_dir.joinpath("validation_runs").glob(f"{items[0].work_item_id}-*.json"))
    finally:
        orchestrator.close()
