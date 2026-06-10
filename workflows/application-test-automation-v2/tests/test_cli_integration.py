from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from test_factory.models import CommandSpec
from test_factory.orchestrator import TestFactoryOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"
IMPROVED_COVERAGE_XML = """<coverage>
  <packages>
    <package name="package">
      <classes>
        <class filename="package/foo.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1" branch="true" condition-coverage="100% (2/2)"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


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


def _write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def _patch_python_validation_commands(orchestrator: TestFactoryOrchestrator, repo: Path, mode: str) -> tuple[object, object, object]:
    adapter = orchestrator.adapter_for_language("python")
    targeted_script = _write_script(
        repo / "targeted_runner.py",
        "print('targeted ok')\n",
    )
    if mode == "improve":
        coverage_body = (
            "from pathlib import Path\n"
            f"Path('coverage.xml').write_text({IMPROVED_COVERAGE_XML!r}, encoding='utf-8')\n"
            "print('coverage improved')\n"
        )
    else:
        coverage_body = "print('coverage unchanged')\n"
    coverage_script = _write_script(repo / "coverage_runner.py", coverage_body)
    original_test = adapter.discover_test_command
    original_coverage = adapter.discover_coverage_command
    adapter.discover_test_command = lambda repo_path, module: CommandSpec(command=[sys.executable, str(targeted_script)], cwd=str(repo), description="fixture targeted validation")
    adapter.discover_coverage_command = lambda repo_path, module: CommandSpec(command=[sys.executable, str(coverage_script)], cwd=str(repo), description="fixture coverage validation")
    return adapter, original_test, original_coverage


def _restore_python_validation_commands(adapter, original_test, original_coverage) -> None:
    adapter.discover_test_command = original_test
    adapter.discover_coverage_command = original_coverage


def _prepare_python_work_item(orchestrator: TestFactoryOrchestrator) -> object:
    orchestrator.scan()
    orchestrator.coverage()
    orchestrator.score()
    items = orchestrator.workitems(limit=3)
    return next(item for item in items if item.module == "package")


def test_cli_run_generates_artifacts_from_fixture(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"

    result = _run_cli("run", "--repo", str(repo), "--out", str(out_dir), "--limit", "2", "--module", "package", cwd=PROJECT_ROOT)

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["module_scope"] == "package"
    assert (out_dir / "final_report.md").exists()
    assert (out_dir / "pr_summary.md").exists()
    assert (out_dir / "test_factory.sqlite").exists()
    assert (out_dir / "ai_work_items" / "index.json").exists()
    assert (out_dir / "validation_runs").exists()


def test_validate_fails_gracefully_when_runner_missing(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)

    try:
        item = _prepare_python_work_item(orchestrator)
        adapter = orchestrator.adapter_for_language("python")
        original_test = adapter.discover_test_command
        adapter.discover_test_command = lambda repo_path, module: CommandSpec(command=["definitely-not-a-real-command"], cwd=str(repo), description="missing runner")
        try:
            result = orchestrator.validate(item.work_item_id)
        finally:
            adapter.discover_test_command = original_test
        assert result["status"] == "failed"
        assert result["targeted"]["exit_code"] == 127
        assert result["module"]["status"] == "skipped"
        assert orchestrator.storage.get_work_item(item.work_item_id)["status"] == "failed"
        assert any(out_dir.joinpath("validation_runs").glob(f"{item.work_item_id}-*.json"))
    finally:
        orchestrator.close()


def test_validate_requires_strict_coverage_improvement(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)

    try:
        item = _prepare_python_work_item(orchestrator)
        adapter, original_test, original_coverage = _patch_python_validation_commands(orchestrator, repo, mode="unchanged")
        try:
            result = orchestrator.validate(item.work_item_id)
        finally:
            _restore_python_validation_commands(adapter, original_test, original_coverage)
        assert result["status"] == "failed"
        assert "line coverage did not improve" in result["reason"]
        assert orchestrator.storage.get_work_item(item.work_item_id)["status"] == "failed"
    finally:
        orchestrator.close()


def test_validate_records_change_set_and_commit_uses_it(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    _git("init", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test User", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "initial snapshot", cwd=repo)
    new_test = repo / "tests" / "test_generated.py"
    new_test.write_text("def test_generated():\n    assert True\n", encoding="utf-8")

    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        item = _prepare_python_work_item(orchestrator)
        adapter, original_test, original_coverage = _patch_python_validation_commands(orchestrator, repo, mode="improve")
        try:
            result = orchestrator.validate(item.work_item_id)
        finally:
            _restore_python_validation_commands(adapter, original_test, original_coverage)
        assert result["status"] == "passed"
        commit_result = orchestrator.commit("package")
        assert commit_result["sha"]
        assert "tests/test_generated.py" in commit_result["files"]
    finally:
        orchestrator.close()


def test_commit_rejects_unrelated_dirty_files_after_validation(tmp_path):
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    _git("init", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test User", cwd=repo)
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "initial snapshot", cwd=repo)
    (repo / "tests" / "test_generated.py").write_text("def test_generated():\n    assert True\n", encoding="utf-8")

    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        item = _prepare_python_work_item(orchestrator)
        adapter, original_test, original_coverage = _patch_python_validation_commands(orchestrator, repo, mode="improve")
        try:
            result = orchestrator.validate(item.work_item_id)
        finally:
            _restore_python_validation_commands(adapter, original_test, original_coverage)
        assert result["status"] == "passed"
        (repo / "package" / "foo.py").write_text("def add(a, b):\n    return a + b + 1\n", encoding="utf-8")
        try:
            orchestrator.commit("package")
            assert False, "expected commit to reject unrelated dirty files"
        except RuntimeError as exc:
            assert "outside the validated change set" in str(exc)
    finally:
        orchestrator.close()
