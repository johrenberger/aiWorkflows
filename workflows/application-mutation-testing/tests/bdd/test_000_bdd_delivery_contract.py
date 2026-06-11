from __future__ import annotations

from pathlib import Path


FIRST_PASS_STORIES = [
    "000_bdd_delivery_contract.md",
    "001_cli_and_config_contract.md",
    "002_repo_intake_and_metadata.md",
    "003_state_and_checkpointing.md",
    "004_ledger_rendering.md",
]

FIRST_PASS_TESTS = [
    "test_000_bdd_delivery_contract.py",
    "test_001_cli_and_config_contract.py",
    "test_002_repo_intake_and_metadata.py",
    "test_003_state_and_checkpointing.py",
    "test_004_ledger_rendering.py",
]


def test_given_project_initialized_when_inspected_then_story_files_exist(project_root: Path) -> None:
    stories_dir = project_root / "stories"
    assert stories_dir.is_dir()

    for story_name in FIRST_PASS_STORIES:
        story_text = (stories_dir / story_name).read_text(encoding="utf-8")
        assert "## Goal" in story_text
        assert "## Acceptance Scenarios" in story_text
        assert "## Executable Test Mapping" in story_text
        assert "## Done Criteria" in story_text


def test_given_project_initialized_when_inspected_then_bdd_tests_exist(project_root: Path) -> None:
    bdd_dir = project_root / "tests" / "bdd"
    assert bdd_dir.is_dir()

    for test_name in FIRST_PASS_TESTS:
        assert (bdd_dir / test_name).is_file()


def test_given_bdd_tests_when_pytest_collects_then_collection_succeeds(project_root: Path) -> None:
    bdd_dir = project_root / "tests" / "bdd"
    collected = sorted(path.name for path in bdd_dir.glob("test_*.py"))
    assert set(FIRST_PASS_TESTS).issubset(collected)
