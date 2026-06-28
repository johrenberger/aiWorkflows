"""Verify that all required nightly dreaming artifacts exist and are non-empty."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DREAMING_DIR = REPO_ROOT / ".openclaw" / "dreaming"

REQUIRED_FILES = [
    "README.md",
    "workflow-nightly-dreaming.md",
    "evidence-index.md",
    "nightly-summary.md",
    "lessons-learned.md",
    "failure-patterns.md",
    "success-patterns.md",
    "inefficiency-patterns.md",
    "skill-usage-scorecard.md",
    "workflow-scorecard.md",
    "regression-scenarios.md",
    "minimax-consumption-brief.md",
    "proposed-improvements.md",
    "pr-change-log.md",
    "validation-checklist.md",
]


@pytest.mark.parametrize("rel_path", REQUIRED_FILES)
def test_required_artifact_exists(rel_path: str) -> None:
    target = DREAMING_DIR / rel_path
    assert target.is_file(), f"Missing required artifact: {target}"


@pytest.mark.parametrize("rel_path", REQUIRED_FILES)
def test_required_artifact_non_empty(rel_path: str) -> None:
    target = DREAMING_DIR / rel_path
    assert target.is_file(), f"Missing required artifact: {target}"
    content = target.read_text(encoding="utf-8").strip()
    assert content, f"Required artifact is empty: {target}"


def test_dreaming_md_exists_at_repo_root() -> None:
    assert (REPO_ROOT / "DREAMING.md").is_file()


def test_dreaming_md_non_empty() -> None:
    content = (REPO_ROOT / "DREAMING.md").read_text(encoding="utf-8").strip()
    assert content
