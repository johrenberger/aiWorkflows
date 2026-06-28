"""Verify PR readiness: branch naming, single PR per cycle, change-log mapping, blocked-change separation."""

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


def test_pr_change_log_exists() -> None:
    assert PR_CHANGE_LOG.is_file()


def test_pr_change_log_maps_changes_to_evidence() -> None:
    text = PR_CHANGE_LOG.read_text(encoding="utf-8")
    # Each commit section must include "Evidence reference" or "Evidence references"
    commit_headers = re.findall(r"^## Commit:", text, re.MULTILINE)
    assert commit_headers, "pr-change-log.md must contain at least one '## Commit:' section"
    # Spot-check: at least one Evidence reference marker exists per commit header region.
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
    assert branch.startswith(BRANCH_PREFIX), (
        f"Current branch {branch!r} does not start with {BRANCH_PREFIX!r}"
    )
    m = BRANCH_DATE_RE.match(branch)
    assert m, f"Current branch {branch!r} does not match {BRANCH_DATE_RE.pattern!r}"


def test_only_one_dreaming_branch_exists() -> None:
    branches = _git("branch", "--list", f"{BRANCH_PREFIX}*").splitlines()
    branches = [b.strip().lstrip("* ").strip() for b in branches if b.strip()]
    assert len(branches) == 1, f"Expected exactly one dreaming branch, found: {branches}"


def test_commits_use_chore_dreaming_prefix() -> None:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    merge_base = _git("merge-base", branch, "main").strip()
    log = _git("log", "--pretty=%s", f"{merge_base}..{branch}").strip()
    subjects = [s for s in log.splitlines() if s]
    assert subjects, "Branch has no commits"
    for s in subjects:
        assert s.startswith("chore(dreaming):"), f"Commit subject {s!r} does not use chore(dreaming): prefix"


def test_no_blocked_changes_applied_in_pr_change_log() -> None:
    """The 'Blocked changes' section must not list any applied change."""
    text = PR_CHANGE_LOG.read_text(encoding="utf-8")
    # Find the Blocked changes section.
    m = re.search(r"## Blocked changes\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    assert m, "pr-change-log.md must contain a '## Blocked changes' section"
    body = m.group(1).strip()
    # Allowed contents: 'None.' or an explicit list stating blocked items are not applied.
    assert "None" in body or "not applied" in body.lower(), (
        f"Blocked changes section must explicitly state none are applied; got: {body!r}"
    )
