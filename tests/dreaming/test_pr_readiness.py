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
      1. CI-provided DREAMING_MERGE_BASE commit SHA (workflow pre-computes it).
      2. GITHUB_BASE_REF (a branch name). Use it directly if it resolves.
      3. Local 'main' branch (developer-machine case).
      4. 'origin/main' (CI fallback).
    """
    sha = os.environ.get("DREAMING_MERGE_BASE", "").strip()
    if sha and _git_silent("cat-file", "-e", f"{sha}^{{commit}}"):
        return sha
    base = os.environ.get("GITHUB_BASE_REF")
    if base:
        if _git_silent("rev-parse", "--verify", f"{base}^{{commit}}"):
            return base
        # In detached CI checkout the base ref may be at origin/<base_ref>
        if _git_silent("rev-parse", "--verify", f"origin/{base}^{{commit}}"):
            return f"origin/{base}"
    if _git_silent("rev-parse", "--verify", "main^{commit}"):
        return "main"
    if _git_silent("rev-parse", "--verify", "origin/main^{commit}"):
        return "origin/main"
    pytest.skip("Could not resolve a base ref (main / origin/main / GITHUB_BASE_REF / DREAMING_MERGE_BASE).")


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
    """The dreaming branch name must match dreaming/nightly-execution-quality-YYYY-MM-DD
    plus an optional -N cycle suffix."""
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch == "HEAD":
        # Detached HEAD (CI checkout) — fall back to env var on PR.
        branch = os.environ.get("GITHUB_HEAD_REF") or branch
    assert branch.startswith(BRANCH_PREFIX), (
        f"Current branch {branch!r} does not start with {BRANCH_PREFIX!r}"
    )
    # Strip the BRANCH_PREFIX and accept either YYYY-MM-DD or YYYY-MM-DD-suffix.
    suffix = branch[len(BRANCH_PREFIX):]
    assert re.match(r"^\d{4}-\d{2}-\d{2}(-.+)?$", suffix), (
        f"Current branch {branch!r}: suffix {suffix!r} does not match YYYY-MM-DD or YYYY-MM-DD-..."
    )


def test_only_one_dreaming_branch_exists() -> None:
    branches = _git("branch", "--list", f"{BRANCH_PREFIX}*").splitlines()
    branches = [b.strip().lstrip("* ").strip() for b in branches if b.strip()]
    # In CI detached HEAD there is typically one branch (the PR head). On a dev machine
    # there may be 0 or many; the constraint applies to producing exactly one per cycle.
    assert len(branches) <= 1, (
        f"Multiple dreaming branches exist (more than one dreaming cycle on this checkout): {branches}"
    )


def test_commits_use_chore_dreaming_prefix() -> None:
    """All commits on this branch ahead of its base must use the chore(dreaming): prefix.

    Uses HEAD explicitly (not the branch name) because the branch ref may point at
    the same commit as the merge-base on a freshly-checked-out branch.
    """
    merge_base = os.environ.get("DREAMING_MERGE_BASE", "").strip()
    head = os.environ.get("GITHUB_HEAD_REF", "").strip()
    head_commit = _git("rev-parse", "HEAD").strip()  # always defined, regardless of ref state
    if merge_base and head:
        # CI path: pre-computed merge-base from the workflow; the head commit is on disk.
        spec = f"{merge_base}..{head_commit}"
    elif merge_base:
        # Local path with explicit merge-base provided.
        spec = f"{merge_base}..{head_commit}"
    else:
        # Local path: discover base from refs.
        branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
        if branch == "HEAD":
            pytest.skip("DREAMING_MERGE_BASE not set and detached HEAD; cannot compute diff.")
        base_ref = _resolve_base_ref()
        try:
            merge_base = _git("merge-base", head_commit, base_ref).strip()
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Cannot compute merge-base: {e}")
        if not merge_base:
            pytest.skip("Empty merge-base.")
        spec = f"{merge_base}..{head_commit}"
    log = _git("log", "--pretty=%s", spec).strip()
    subjects = [s for s in log.splitlines() if s]
    if not subjects:
        # No commits yet on this branch — not an error. The Makefile target
        # (`make dreaming-pr-ready`) is intended to run BEFORE the first commit
        # too, so a clean branch must skip, not fail.
        pytest.skip(f"No commits yet in range {spec}.")
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
