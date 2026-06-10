from __future__ import annotations

import subprocess
from pathlib import Path

from ..models import CommitRecord


def _module_matches_path(module: str, path: str) -> bool:
    normalized = path.replace("\\", "/")
    module_token = module.replace("\\", "/").strip("/")
    if module_token and module_token in normalized:
        return True
    return normalized.startswith(("tests/", "test/", "src/test/", "src/integrationTest/"))


def commit_module(repo_path: str | Path, module: str, message: str | None = None, files_to_stage: list[str] | None = None) -> CommitRecord:
    repo_path = Path(repo_path)
    message = message or f"test: improve coverage for {module}"
    status = subprocess.run(["git", "status", "--short"], cwd=repo_path, capture_output=True, text=True)
    if status.returncode != 0:
        raise RuntimeError(status.stderr)
    changed_files = [line[3:].strip() for line in status.stdout.splitlines() if len(line) >= 4]
    stage_candidates = files_to_stage or [path for path in changed_files if _module_matches_path(module, path)]
    if not stage_candidates:
        raise RuntimeError(f"no changed files matched module {module}")
    staged = subprocess.run(["git", "add", "--", *stage_candidates], cwd=repo_path, capture_output=True, text=True)
    if staged.returncode != 0:
        raise RuntimeError(staged.stderr)
    staged_files = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=repo_path, capture_output=True, text=True)
    if staged_files.returncode != 0:
        raise RuntimeError(staged_files.stderr)
    if not staged_files.stdout.strip():
        raise RuntimeError(f"no staged changes available for module {module}")
    commit = subprocess.run(["git", "commit", "-m", message], cwd=repo_path, capture_output=True, text=True)
    if commit.returncode != 0:
        raise RuntimeError(commit.stderr or commit.stdout or "git commit failed")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True).stdout.strip()
    files = subprocess.run(["git", "diff", "--name-only", "HEAD~1..HEAD"], cwd=repo_path, capture_output=True, text=True).stdout.splitlines()
    return CommitRecord(module=module, message=message, sha=sha, files=files)
