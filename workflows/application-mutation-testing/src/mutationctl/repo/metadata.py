from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from mutationctl.command_runner import SubprocessCommandRunner
from mutationctl.errors import RepoInputError
from mutationctl.models import RepoMetadata


def _run_git_capture(runner: SubprocessCommandRunner, repo_path: Path, *args: str) -> str:
    import subprocess

    completed = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def capture_repo_metadata(
    repo_path: str | Path,
    runner: SubprocessCommandRunner | None = None,
    repo_url: str | None = None,
) -> RepoMetadata:
    del runner
    path = Path(repo_path).resolve()
    git_dir = path / ".git"
    if not git_dir.exists():
        raise RepoInputError(f"Not a git repository: {path}")

    branch = _run_git_capture(SubprocessCommandRunner(), path, "rev-parse", "--abbrev-ref", "HEAD")
    commit_sha = _run_git_capture(SubprocessCommandRunner(), path, "rev-parse", "HEAD")
    status_output = _run_git_capture(SubprocessCommandRunner(), path, "status", "--porcelain")
    return RepoMetadata(
        repo_path=str(path),
        repo_url=repo_url,
        branch=branch,
        commit_sha=commit_sha,
        is_dirty=bool(status_output),
        captured_at=datetime.now(UTC).isoformat(),
    )
