from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mutationctl.detection.language import detect_languages
from mutationctl.detection.mutation_tools import detect_mutation_tools
from mutationctl.state.store import StateStore


def test_given_python_repo_when_language_detection_runs_then_python_detected_with_evidence(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_mutmut_basic"
    results = detect_languages(repo)
    assert results[0].language == "python"
    assert "pyproject.toml" in results[0].evidence


def test_given_pyproject_with_mutmut_when_tool_detection_runs_then_mutmut_detected(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_mutmut_basic"
    result = detect_mutation_tools(repo)
    assert result.selected_tool == "mutmut"
    assert result.evidence[0].available is True
    assert "pyproject.toml" in result.evidence[0].evidence


def test_given_python_repo_without_mutation_tool_when_install_disabled_then_blocker_recorded(
    project_root: Path, tmp_path: Path
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_no_mutation_tool"
    store = StateStore(tmp_path)
    store.initialize()
    result = detect_mutation_tools(repo, store=store, allow_dependency_install=False)
    assert result.status == "BLOCKED"
    assert result.selected_tool is None
    assert store.list_blockers()[0].code == "MUTATION_TOOL_NOT_FOUND"


def test_given_package_json_with_stryker_when_tool_detection_runs_then_stryker_detected(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "js_stryker_basic"
    result = detect_mutation_tools(repo)
    assert result.selected_tool == "stryker"
    assert "package.json" in result.evidence[0].evidence


def test_given_pom_with_pit_when_tool_detection_runs_then_pit_detected(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "java_pit_basic"
    result = detect_mutation_tools(repo)
    assert result.selected_tool == "pit"
    assert "pom.xml" in result.evidence[0].evidence


def test_given_detect_cli_when_run_then_fixture_tool_is_reported(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_mutmut_basic"
    completed = subprocess.run(
        [sys.executable, "-m", "mutationctl", "detect", "--repo-path", str(repo)],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "mutmut" in completed.stdout


def test_given_tool_detection_when_store_supplied_then_evidence_is_persisted(
    project_root: Path, tmp_path: Path
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_mutmut_basic"
    store = StateStore(tmp_path)
    store.initialize()
    detect_mutation_tools(repo, store=store)
    persisted = store.get_latest_tool_detection()
    assert persisted is not None
    assert persisted.selected_tool == "mutmut"
