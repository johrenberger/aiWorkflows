from __future__ import annotations

import re
from pathlib import Path

from mutationctl.errors import RepoInputError
from mutationctl.models import RepoInput

GITHUB_REPO_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def normalize_github_url(url: str) -> str:
    cleaned = url.strip()
    match = GITHUB_REPO_PATTERN.match(cleaned)
    if not match:
        raise RepoInputError(f"Unsupported repository URL: {url}")
    owner = match.group("owner")
    repo = match.group("repo")
    return f"https://github.com/{owner}/{repo}"


def validate_repo_input(repo: str) -> RepoInput:
    candidate = repo.strip()
    if candidate.startswith("https://"):
        return RepoInput(original=repo, repo_url=normalize_github_url(candidate))

    path = Path(candidate).expanduser()
    if not path.exists():
        raise RepoInputError(f"Repository path does not exist: {repo}")
    return RepoInput(original=repo, repo_path=str(path.resolve()))
