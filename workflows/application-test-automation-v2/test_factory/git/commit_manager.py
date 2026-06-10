from __future__ import annotations

import subprocess
from pathlib import Path

from ..models import CommitRecord

IGNORED_DIRTY_SEGMENTS = {"coverage", "target", "build", "dist", "__pycache__"}
IGNORED_DIRTY_FILES = {"coverage.xml", ".coverage"}


def _run_git(repo_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(["git", *args], cwd=repo_path, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout or f"git {' '.join(args)} failed")
    return completed


def git_head_sha(repo_path: str | Path) -> str:
    repo_path = Path(repo_path)
    return _run_git(repo_path, "rev-parse", "HEAD").stdout.strip()


def changed_files(repo_path: str | Path) -> list[str]:
    repo_path = Path(repo_path)
    status = _run_git(repo_path, "status", "--short")
    files: list[str] = []
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path.replace("\\", "/"))
    return sorted(set(files))


def _module_matches_path(module: str, path: str) -> bool:
    normalized = path.replace("\\", "/")
    module_token = module.replace("\\", "/").strip("/")
    if module_token and normalized.startswith(f"{module_token}/"):
        return True
    if module_token and f"/{module_token}/" in normalized:
        return True
    return normalized.startswith(("tests/", "test/", "src/test/", "src/integrationTest/"))


def _ignored_dirty_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    name = Path(normalized).name
    if name in IGNORED_DIRTY_FILES:
        return True
    return any(segment in IGNORED_DIRTY_SEGMENTS for segment in normalized.split("/"))


def commit_module(
    repo_path: str | Path,
    module: str,
    message: str | None = None,
    *,
    expected_head_sha: str = "",
    files_to_stage: list[str] | None = None,
    allow_dirty: bool = False,
) -> CommitRecord:
    repo_path = Path(repo_path)
    message = message or f"test: improve coverage for {module}"
    current_head_sha = git_head_sha(repo_path)
    if expected_head_sha and current_head_sha != expected_head_sha:
        raise RuntimeError("repository HEAD changed since validation")
    dirty_files = changed_files(repo_path)
    if not dirty_files:
        raise RuntimeError("no changed files available to commit")
    considered_dirty_files = [path for path in dirty_files if not _ignored_dirty_file(path)]
    requested_files = sorted({path.replace("\\", "/") for path in (files_to_stage or [])})
    if requested_files:
        missing = sorted(set(requested_files) - set(considered_dirty_files))
        if missing:
            raise RuntimeError(f"validated files are no longer dirty: {', '.join(missing)}")
        unexpected = sorted(set(considered_dirty_files) - set(requested_files))
        if unexpected and not allow_dirty:
            raise RuntimeError(f"dirty files are outside the validated change set: {', '.join(unexpected)}")
        stage_candidates = requested_files
    else:
        stage_candidates = [path for path in considered_dirty_files if _module_matches_path(module, path)]
        if not stage_candidates:
            raise RuntimeError(f"no changed files matched module {module}")
    _run_git(repo_path, "add", "--", *stage_candidates)
    staged_files = _run_git(repo_path, "diff", "--cached", "--name-only").stdout.splitlines()
    staged_files = [path.replace("\\", "/") for path in staged_files if path.strip()]
    if not staged_files:
        raise RuntimeError(f"no staged changes available for module {module}")
    unexpected_staged = sorted(set(staged_files) - set(stage_candidates))
    if unexpected_staged:
        raise RuntimeError(f"staged files exceeded validated scope: {', '.join(unexpected_staged)}")
    _run_git(repo_path, "commit", "-m", message)
    sha = git_head_sha(repo_path)
    committed_files = _run_git(repo_path, "diff", "--name-only", "HEAD~1..HEAD").stdout.splitlines()
    committed_files = [path.replace("\\", "/") for path in committed_files if path.strip()]
    return CommitRecord(module=module, message=message, sha=sha, files=committed_files)
