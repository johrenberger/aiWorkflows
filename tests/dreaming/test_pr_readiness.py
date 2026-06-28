"""Verify PR readiness: branch naming, single PR per cycle, change-log mapping, blocked-change separation."""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PR_CHANGE_LOG = REPO_ROOT / ".openclaw" / "dreaming" / "pr-change-log.md"

BRANCH_PREFIX = "dreaming/nightly-execution-quality-"
BRANCH_DATE_RE = re.compile(r"^dreaming/nightly-execution-quality-(\d{4}-\d{2}-\d{2})$")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO_ROOT), *args], text=True)


def _git_silent(*args: str) -> str:
    """Run git and return empty string on non-zero exit (used for fallbacks)."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def _resolve_base_ref() -> str:
    """Resolve the ref that 'main' (or whatever the PR targets) points to.

    Order of preference:
      1. GITHUB_BASE_REF environment variable (set on PR runs).
      2. Local 'main' branch (developer-machine case).
      3. 'origin/main' (fetched in CI).
      4. The merge-base of the current branch with origin/HEAD as a last resort.
    """
    base = os.environ.get("GITHUB_BASE_REF")
    if base:
        if _git_silent("rev-parse", "--verify", f"{base}^{{commit}}"):
            return base
    # Local main
    if _git_silent("rev-parse", "--verify", "main^{commit}"):
        return "main"
    # Origin main (CI)
    if _git_silent("rev-parse", "--verify", "origin/main^{commit}"):
        return "origin/main"
    pytest.skip("Could not resolve a base ref (main / origin/main / GITHUB_BASE_REF).")


def test_pr_change_log_exists() -> None:
    assert PR_CHANGE_LOG.is_file()


def test_pr_change_log_maps_changes_to_evidence() -> None:
    text = PR_CHANGE_LOG.read_text(encoding="utf-8")
    commit_headers = re.findall(r"^## Commit:", text, re.MULTILINE)
    assert commit_headers, "pr-change-log.md must contain at least one '## Commit:' section"
    assert "Evidence reference" in text or "Evidence references" in text, (
        "pr-change-log.md must include evidence references"
    )


def test_pr_change_log_separates_safety_classes() -> None:
    text = PR_CHANGE_LOG.read_text(encoding="utf-8")
    assert "review-required" in text.lower() or "review_required" in text.lower(), (
        "pr-change-log.md must explicitly separate review-required changes"
    )
    assert "Blocked changes" in text or "blocked-class changes" in text.lower(), (
        "pr-change-log.md must explicitly handle blocked changes"
    )


def test_current_branch_uses_dreaming_prefix() -> None:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch == "HEAD":
        # Detached HEAD (CI checkout) — fall back to env var on PR.
        base = os.environ.get("GITHUB_HEAD_REF") or branch
        branch = base
    assert branch.startswith(BRANCH_PREFIX), (
        f"Current branch {branch!r} does not start with {BRANCH_PREFIX!r}"
    )
    m = BRANCH_DATE_RE.match(branch)
    assert m, f"Current branch {branch!r} does not match {BRANCH_DATE_RE.pattern!r}"


def test_only_one_dreaming_branch_exists() -> None:
    branches = _git("branch", "--list", f"{BRANCH_PREFIX}*").splitlines()
    branches = [b.strip().lstrip("* ").strip() for b in branches if b.strip()]
    # In CI detached HEAD there is typically one branch (the PR head). On a dev machine
    # there may be 0 or many; the constraint applies to producing exactly one per cycle.
    assert len(branches) <= 1, (
        f"Multiple dreaming branches exist (more than one dreaming cycle on this checkout): {branches}"
    )


def test_commits_use_chore_dreaming_prefix() -> None:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch == "HEAD":
        branch = os.environ.get("GITHUB_HEAD_REF") or "HEAD"
    base_ref = _resolve_base_ref()
    try:
        merge_base = _git("merge-base", branch, base_ref).strip()
    except subprocess.CalledProcessError:
        pytest.skip(f"Cannot compute merge-base of {branch} and {base_ref}.")
    if not merge_base:
        pytest.skip(f"Empty merge-base of {branch} and {base_ref}.")
    log = _git("log", "--pretty=%s", f"{merge_base}..{branch}").strip()
    subjects = [s for s in log.splitlines() if s]
    assert subjects, "Branch has no commits ahead of base"
    for s in subjects:
        assert s.startswith("chore(dreaming):"), (
            f"Commit subject {s!r} does not use chore(dreaming): prefix"
        )


def test_no_blocked_changes_applied_in_pr_change_log() -> None:
    text = PR_CHANGE_LOG.read_text(encoding="utf-8")
    m = re.search(r"## Blocked changes\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    assert m, "pr-change-log.md must contain a '## Blocked changes' section"
    body = m.group(1).strip()
    assert "None" in body or "not applied" in body.lower(), (
        f"Blocked changes section must explicitly state none are applied; got: {body!r}"
    )
