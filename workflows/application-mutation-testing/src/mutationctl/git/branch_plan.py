from __future__ import annotations

import re

from mutationctl.models import BranchPlan


def plan_branch(
    current_branch: str,
    repo_slug: str,
    run_id: str,
    existing_branches: list[str],
    allow_direct_branch_commit: bool = False,
) -> BranchPlan:
    safe_repo = _sanitize(repo_slug)
    safe_run = _sanitize(run_id)
    protected = current_branch in {"main", "master", "develop"}
    proposed = current_branch if allow_direct_branch_commit and not protected else f"mutationctl/{safe_repo}/{safe_run}"
    exists = proposed in existing_branches
    if exists:
        suffix = 2
        candidate = f"{proposed}-{suffix}"
        while candidate in existing_branches:
            suffix += 1
            candidate = f"{proposed}-{suffix}"
        proposed = candidate
    safe = proposed not in {"main", "master", "develop"} or allow_direct_branch_commit
    return BranchPlan(
        current_branch,
        proposed,
        exists,
        safe,
        "Generated workflow branch avoids direct protected-branch commit" if safe else "Direct protected-branch commit is blocked",
        [current_branch, proposed],
    )


def _sanitize(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-./")
    return cleaned or "run"
