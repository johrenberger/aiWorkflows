from __future__ import annotations

from pathlib import Path

from mutationctl.command_runner import SubprocessCommandRunner
from mutationctl.errors import RepoInputError


def run_git(repo_path: str | Path, *args: str, runner: SubprocessCommandRunner | None = None) -> str:
    command_runner = runner or SubprocessCommandRunner()
    result = command_runner.run(["git", *args], cwd=repo_path)
    if result.exit_code != 0:
        raise RepoInputError(f"git {' '.join(args)} failed for {repo_path}")
    return ""
