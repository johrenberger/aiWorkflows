from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


HTTPS_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")
SSH_RE = re.compile(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$")


def parse_github_url(url: str) -> tuple[str, str]:
    url = url.strip()
    match = HTTPS_RE.match(url) or SSH_RE.match(url)
    if not match:
        raise ValueError(f"Unsupported GitHub URL: {url}")
    return match.group(1), match.group(2)


def commit_pinned_prefix(owner: str, repo: str, commit: str) -> str:
    return f"https://github.com/{owner}/{repo}/blob/{commit}/"


def url_for_path(owner: str, repo: str, commit: str, rel_path: str) -> str:
    return commit_pinned_prefix(owner, repo, commit) + rel_path.replace("\\", "/").lstrip("/")


def detect_default_branch(repo_path: Path) -> str | None:
    candidates = [
        ["git", "-C", str(repo_path), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        ["git", "-C", str(repo_path), "remote", "show", "origin"],
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except OSError:
            continue
        if result.returncode == 0:
            if "symbolic-ref" in cmd:
                value = result.stdout.strip()
                if value.startswith("origin/"):
                    return value.split("/", 1)[1]
                if value:
                    return value
            else:
                for line in result.stdout.splitlines():
                    if "HEAD branch:" in line:
                        return line.split(":", 1)[1].strip()
    return None


def build_links_by_path(owner: str, repo: str, commit: str, paths: list[str]) -> dict[str, str]:
    return {path: url_for_path(owner, repo, commit, path) for path in sorted(paths)}

