from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from mutationctl.command_runner import SubprocessCommandRunner
from mutationctl.errors import RepoInputError
from mutationctl.repo.intake import validate_repo_input
from mutationctl.repo.metadata import capture_repo_metadata


def test_given_valid_github_url_when_validated_then_url_is_normalized() -> None:
    repo_input = validate_repo_input("https://github.com/example/project.git")
    assert repo_input.repo_url == "https://github.com/example/project"


def test_given_invalid_repo_url_when_validated_then_error_is_raised() -> None:
    with pytest.raises(RepoInputError):
        validate_repo_input("https://example.com/not-github/project")


@pytest.mark.skipif(not hasattr(subprocess, "run"), reason="subprocess unavailable")
def test_given_clean_local_git_repo_when_metadata_captured_then_branch_commit_and_clean_status_recorded(
    tmp_path: Path, git_available: bool
) -> None:
    if not git_available:
        pytest.skip("git is unavailable")

    repo_dir = tmp_path / "synthetic_git_repo"
    repo_dir.mkdir()
    _run_git(repo_dir, "init", "-b", "main")
    _run_git(repo_dir, "config", "user.name", "Test User")
    _run_git(repo_dir, "config", "user.email", "test@example.com")
    (repo_dir / "README.md").write_text("hello\n", encoding="utf-8")
    _run_git(repo_dir, "add", "README.md")
    _run_git(repo_dir, "commit", "-m", "initial commit")

    metadata = capture_repo_metadata(repo_dir, SubprocessCommandRunner())

    assert metadata.branch == "main"
    assert len(metadata.commit_sha) >= 7
    assert metadata.is_dirty is False
    assert metadata.captured_at


def test_given_dirty_local_git_repo_when_metadata_captured_then_dirty_status_is_true(
    tmp_path: Path, git_available: bool
) -> None:
    if not git_available:
        pytest.skip("git is unavailable")

    repo_dir = tmp_path / "synthetic_git_repo"
    repo_dir.mkdir()
    _run_git(repo_dir, "init", "-b", "main")
    _run_git(repo_dir, "config", "user.name", "Test User")
    _run_git(repo_dir, "config", "user.email", "test@example.com")
    (repo_dir / "README.md").write_text("hello\n", encoding="utf-8")
    _run_git(repo_dir, "add", "README.md")
    _run_git(repo_dir, "commit", "-m", "initial commit")
    (repo_dir / "README.md").write_text("changed\n", encoding="utf-8")

    metadata = capture_repo_metadata(repo_dir, SubprocessCommandRunner())

    assert metadata.is_dirty is True


def _run_git(repo_dir: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
