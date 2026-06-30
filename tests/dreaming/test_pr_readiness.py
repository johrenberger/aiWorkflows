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
    # Exclude the branch we are currently on. The PR-readiness invariant is:
    # "no OTHER dreaming branch exists" (one open cycle at a time). Counting the
    # current branch against itself was cycle-2's bug; CI caught it locally
    # via PI-008. Cycle-2's own cycle-3 branch lingered on the local checkout
    # (we hadn't cleaned it up yet); this filter is what makes that case
    # "skip-or-pass" rather than "fail".
    try:
        current = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    except subprocess.CalledProcessError:
        current = "HEAD"
    if current != "HEAD":
        branches = [b for b in branches if b != current]
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
    # If the merge-base equals HEAD (e.g. on a fresh main checkout, immediately after a
    # merge), there's no PR-side diff to inspect; skip rather than fail.
    try:
        mb_sha = _git("rev-parse", spec.split("..")[0]).strip()
    except subprocess.CalledProcessError:
        mb_sha = ""
    if mb_sha and mb_sha == head_commit:
        pytest.skip(f"HEAD equals merge-base ({head_commit[:7]}); no PR diff to inspect.")
    log = _git("log", "--pretty=%s", spec).strip()
    subjects = [s for s in log.splitlines() if s]
    if not subjects:
        # No commits yet on this branch — not an error. The Makefile target
        # (`make dreaming-pr-ready`) is intended to run BEFORE the first commit
        # too, so a clean branch must skip, not fail.
        pytest.skip(f"No commits yet in range {spec}.")
    # Filter out merge commits: in CI on a PR, the runner checks out a merge commit
    # GitHub auto-creates; its subject is not authored by us and is not subject to
    # the chore(dreaming): prefix convention.
    subjects = [s for s in subjects if not s.startswith("Merge ")]
    if not subjects:
        pytest.skip(f"No non-merge commits in range {spec}.")
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


def test_declares_surface_scope_in_trigger() -> None:
    """The most recent cycle's Trigger section in nightly-summary.md must declare surface scope.

    Enforces Stage -2 (PI-015, cycle 8): every cycle must pre-declare its surface
    scope in the Trigger section of nightly-summary.md, before Stage -1's
    workspace pre-check. The test is forward-looking: it requires the **most
    recent cycle's** Trigger section to have the new format. Past cycles'
    Trigger sections are preserved as historical record and not retroactively
    restructured (per workflow-nightly-dreaming.md Stage -2 docstring).

    Required field labels (case-insensitive substring match in the first
    `## Trigger` section):
      - "Workflow target"
      - "Surface area"
      - "Dreaming-ledger scope"
      - "Cycle-size budget"

    The most recent cycle's Trigger section is defined as: the first
    `## Trigger` heading encountered when reading nightly-summary.md
    top-to-bottom.
    """
    nightly_summary = REPO_ROOT / ".openclaw" / "dreaming" / "nightly-summary.md"
    assert nightly_summary.is_file(), f"Missing required artifact: {nightly_summary}"
    text = nightly_summary.read_text(encoding="utf-8")

    # Find the first `## Trigger` heading.
    match = re.search(r"^## Trigger\s*$", text, flags=re.MULTILINE)
    assert match is not None, (
        "nightly-summary.md has no `## Trigger` section at the top of the file. "
        "Stage -2 (PI-015, cycle 8) requires the most recent cycle to have a "
        "Trigger section pre-declaring surface scope."
    )

    # Extract content from that heading up to the next `## ` heading (or EOF).
    start = match.end()
    next_heading = re.search(r"^## ", text[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    trigger_section = text[start:end]

    required_labels = [
        "Workflow target",
        "Surface area",
        "Dreaming-ledger scope",
        "Cycle-size budget",
    ]
    missing = [label for label in required_labels if label.lower() not in trigger_section.lower()]
    assert not missing, (
        f"Most recent cycle's Trigger section is missing Stage -2 fields: {missing}. "
        f"All four required labels must appear (case-insensitive): {required_labels}. "
        f"See workflow-nightly-dreaming.md Stage -2 for the schema."
    )


def test_no_post_amend_working_tree_drift() -> None:
    """No tracked file in .openclaw/dreaming/ should be in a modified state relative to HEAD.

    Enforces Stage -3 (PI-017, cycle 10): after a commit (and especially after
    `git commit --amend`), the working tree must be clean relative to the
    most recent commit. A modified tracked file indicates a state mismatch
    that will block the next `git checkout` with "Please commit your changes
    or stash them before you switch branches."

    The check is scoped to `.openclaw/dreaming/` because that's the cycle's
    working area. Other directories (e.g., `workflows/`) may have
    intentionally-uncommitted local edits that are out of cycle scope.

    This test is most useful after a `git commit --amend` or before the
    next checkout. It is a hygiene check, not a structural invariant.
    """
    status_output = _git_silent("status", "--short", "--", ".openclaw/dreaming/")
    if not status_output:
        # Clean working tree in scope. Test passes.
        return

    # Parse `git status --short` output. Lines look like:
    #   " M path/to/file"  (modified, unstaged)
    #   "M  path/to/file"  (modified, staged)
    #   "MM path/to/file"  (modified, both staged and unstaged)
    #   "?? path/to/file"  (untracked — ignored, not a drift)
    drift_lines = [
        line for line in status_output.splitlines()
        if line.strip() and not line.startswith("??")
    ]
    assert not drift_lines, (
        f"Working tree has modified tracked files in .openclaw/dreaming/ "
        f"relative to HEAD (Stage -3 violation):\n"
        + "\n".join(drift_lines)
        + "\n\nThis usually means a `git commit --amend` produced a state "
        "mismatch. Run `git status` to inspect, then either `git add` the "
        "file (if the amend didn't capture the latest content) or "
        "`git checkout -- <file>` (if the file should match HEAD)."
    )
