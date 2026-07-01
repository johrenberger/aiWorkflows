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
    """No tracked file in .openclaw/dreaming/ should be in an UNSTAGED modified state relative to HEAD.

    Enforces Stage -3 (PI-017, cycle 10): after a commit (and especially after
    `git commit --amend`), the working tree must be clean relative to the
    most recent commit. An unstaged tracked file indicates a state mismatch
    that will block the next `git checkout` with "Please commit your changes
    or stash them before you switch branches." Staged-only changes are
    excluded: those are part of the cycle author's normal authoring flow
    (edit → `git add` → validate → commit) and the staged content will
    land in the next commit, so no drift remains post-commit.

    The cycle-8 and cycle-9 working-tree-rescue pattern was specifically
    UNSTAGED drift: after `git commit --amend`, the local working tree had
    a stale line that didn't make it into the commit. `git status` shows
    this as `" M file"` (modified, unstaged). Staged-only changes (`"M  file"`)
    are not drift — they're about-to-be-committed work.

    The check is scoped to `.openclaw/dreaming/` because that is the cycle's
    primary working area — the cycle-8 and cycle-9 closeout memos both
    disclosed drift in `nightly-summary.md` (a `.openclaw/dreaming/` file).
    Other directories (e.g., `workflows/`, `tests/dreaming/`) may have
    intentionally-uncommitted local edits that are out of cycle scope.
    A future cycle may broaden the scope if evidence surfaces that
    `tests/dreaming/` (or another path) has the same drift pattern.

    Note: this test fires on UNSTAGED modifications. Staged-only changes
    are fine. Mixed (staged + unstaged) changes are drift (the unstaged
    portion is the problem). The test enforces "after every commit, your
    working tree should match HEAD, with staged-only changes being
    acceptable during authoring."
    """
    status_output = _git_silent("status", "--short", "--", ".openclaw/dreaming/")
    if not status_output:
        # Clean working tree in scope (empty `git status` output). Test passes.
        # This includes the fresh-clone and post-merge-on-main cases where
        # the working tree matches HEAD by construction.
        return

    # Parse `git status --short` output. Lines look like:
    #   " M path/to/file"  (modified, UNSTAGED — drift)
    #   "M  path/to/file"  (modified, STAGED — fine, about-to-be-committed)
    #   "MM path/to/file"  (modified, both — drift, the unstaged portion is the problem)
    #   "?? path/to/file"  (untracked — ignored, not a drift)
    #   "D  path/to/file"  (deleted, staged — fine)
    #   " D path/to/file"  (deleted, unstaged — drift)
    # The first character of the two-character status column is the index
    # (staged) state; the second is the working-tree (unstaged) state.
    # A drift line is one where the second character is non-space and
    # not '?' (untracked).
    drift_lines = []
    for line in status_output.splitlines():
        line = line.rstrip()
        if not line or len(line) < 3:
            continue
        # Two-character status is `XY` where X is index, Y is worktree.
        # We care about Y != ' ' (working tree differs from index).
        index_state = line[0]
        worktree_state = line[1]
        # Skip untracked entirely (`??`).
        if index_state == "?" and worktree_state == "?":
            continue
        # If the worktree differs from the index, it's a drift.
        if worktree_state != " ":
            drift_lines.append(line)

    assert not drift_lines, (
        f"Working tree has UNSTAGED modified tracked files in "
        f".openclaw/dreaming/ relative to HEAD (Stage -3 violation):\n"
        + "\n".join(drift_lines)
        + "\n\nThis fires when there are unstaged modifications to tracked "
        "files in .openclaw/dreaming/. Common cases:\n"
        "  1. A `git commit --amend` produced a state mismatch (the cycle-8 "
        "/cycle-9 working-tree-rescue pattern). Run `git status` to inspect, "
        "then either `git add <file>` (if the amend didn't capture the "
        "latest content) or `git checkout -- <file>` (if the file should "
        "match HEAD).\n"
        "  2. You have leftover state from a prior cycle's working tree "
        "(e.g., a stale `nightly-summary.md` line that didn't make it into "
        "the cycle's commit). Discard with `git checkout -- <file>` after "
        "verifying the file on `origin/main` (post-merge) has the content "
        "you want.\n"
        "Note: STAGED changes (lines starting with `M `, second column "
        "space) are NOT drift. They're about-to-be-committed work and the "
        "test ignores them."
    )


def test_pr_change_log_forecasts_main_post_merge_count() -> None:
    """The most recent committed cycle row in pr-change-log.md must forecast a `main` post-merge count.

    Enforces PI-016 (cycle 9) and PI-018 (cycle 11 amendment): every cycle's
    row in pr-change-log.md must contain a `main` post-merge forecast. The
    forecast is verified against the actual `main` post-merge count after
    the merge lands, per Stage 11 of workflow-nightly-dreaming.md.

    The test is forward-looking: it checks the most recent committed cycle
    row. It does NOT retroactively check past cycles (those are cycle-11's
    PI-018 retroactive-correction deliverable).

    The test asserts the FORECAST exists in pr-change-log.md AND that it
    contains a numeric count of tests in `<digit> passed` shape. It does
    NOT assert the forecast was correct (that requires running
    `make dreaming-validate` on the actual post-merge `main`, which is a
    manual discipline enforced by Stage 11, not by an automated test).
    Placeholders (`TBD`, `XXX`, `to be determined`) are NOT acceptable;
    the test requires an explicit numeric count.

    Cycle-authoring note: this test fires during cycle authoring if the
    cycle's row in pr-change-log.md doesn't yet contain the forecast OR
    if the forecast is a placeholder. Add a forecast WITH actual
    predicted counts (e.g., "main post-merge (forecast): 130 passed + 1
    skipped + 1 expected-fail-on-main") before committing. The forecast
    is later verified by running `make dreaming-validate` on the actual
    post-merge `main` per Stage 11.

    Detection rationale: the regexes are anchored to line-start and match
    a "forecast line" (heading, bullet, or plain line) followed by a
    numeric count shape (`<digit> passed`), not a narrative mention or
    a placeholder. A cycle row that mentions "PI-016 forecast" or
    "main post-merge count" in passing prose does NOT pass the test —
    only an explicit forecast line with a numeric count does. The
    cycle-10 cycle row uses the bullet form
    (`**`main` post-merge (forecast, per PI-016):** 125 passed + 1
    skipped + 1 expected-fail-on-main`); the cycle-11 cycle row uses a
    heading (`### Main post-merge (forecast)`) plus a bullet
    (`**`main` post-merge (forecast):** 127 passed + ...`). Both are
    detected. Placeholder forecasts like `- main post-merge (forecast):
    TBD` or `- **`main` post-merge (forecast):** to be determined` do
    NOT satisfy the test.

    Three failure modes the test catches:
      (a) Missing forecast line entirely.
      (b) Forecast present as a placeholder (TBD, XXX, to be determined)
          without a numeric count.
      (c) Narrative mention only (no explicit forecast line).
    """
    if not PR_CHANGE_LOG.exists():
        pytest.fail(
            f"pr-change-log.md not found at {PR_CHANGE_LOG}. "
            "Create it before running this test."
        )

    log_text = PR_CHANGE_LOG.read_text(encoding="utf-8")

    # Split into cycle rows. Each cycle row starts with a `## Cycle-N`
    # heading. We want the most recent one (the LAST one in the file).
    cycle_sections = re.split(r"^## (Cycle-\d+)", log_text, flags=re.MULTILINE)
    # cycle_sections alternates: [preamble, "Cycle-N", content, "Cycle-N+1", content, ...]
    if len(cycle_sections) < 3:
        pytest.fail(
            "pr-change-log.md has no cycle sections. Expected at least one "
            "`## Cycle-N` heading."
        )

    # The most recent cycle is the last "Cycle-N" heading + its content.
    last_cycle_label = cycle_sections[-2]
    last_cycle_content = cycle_sections[-1]

    # Look for a main-post-merge forecast LINE (not narrative mention).
    # Acceptable forms, anchored to line-start to avoid matching narrative
    # mentions like "PI-016 established the convention of forecasting main
    # post-merge counts":
    #   - Heading:   `### Main post-merge (forecast)` followed (on the
    #                same or a subsequent body line) by a numeric count
    #                in `<digit> passed` shape (e.g., `127 passed + 1
    #                skipped + 1 expected-fail-on-main`). The heading
    #                alone (with a placeholder body) is NOT acceptable.
    #   - Bullet:    `- **`main` post-merge (forecast):** 130 passed + 1
    #                skipped + 1 expected-fail-on-main`. Numeric count
    #                must be on the SAME line as the forecast.
    #   - Plain:     `main post-merge (forecast): 130 passed + 1 skipped
    #                + 1 expected-fail-on-main`. Numeric count on the
    #                SAME line.
    # The `main` token may be backtick-wrapped (`` `main` ``) and may have
    # markdown bold (`**`) prefix in the bullet form. Whitespace and backticks
    # between `main` and `post-merge` are accepted. A `, per PI-016` (or
    # similar) qualifier is allowed between `forecast` and `)`.
    #
    # The numeric-count requirement is the cycle-11 round-5 fix:
    # placeholder forecasts (TBD, XXX, to be determined) and
    # heading-only-without-numbers forecasts were passing the original
    # three regexes. The fallback search (numeric count in the same
    # cycle section) catches stray forecast lines that happen to include
    # numbers later.
    NUMERIC_FORECAST = r"\d+\s+passed"
    forecast_patterns = [
        # Heading form (level 2-4 markdown headings): `### Main post-merge
        # (forecast)` followed by a body line (within the same cycle
        # section) containing `<digit> passed`. The header itself does
        # NOT need the numbers; the next body line does.
        r"(?:^|\n)\s*#{2,4}\s+main[\s`]*post[- ]merge[\s`]*\(forecast[^)]*\)[^\n]*\n[^\n]*"
        + NUMERIC_FORECAST,
        # Bullet form (with optional ** bold, backtick-wrapped `main`,
        # optional post-forecast qualifier like ", per PI-016").
        # Numeric count on the SAME line as the forecast.
        # `- **`main` post-merge (forecast, per PI-016):** 125 passed + 1
        # skipped + 1 expected-fail-on-main`
        r"(?:^|\n)\s*[-*]\s+\S*?main[\s`]*post[- ]merge[\s`]*\(forecast[^)]*\)[^\n]*"
        + NUMERIC_FORECAST,
        # Plain line form (no list marker, no heading). Numeric count on
        # the SAME line. `main post-merge (forecast): 130 passed + ...`
        r"(?:^|\n)\s*`{0,1}main`{0,1}[\s`]+\s*post[- ]merge[\s`]*\(forecast[^)]*\)[^\n]*"
        + NUMERIC_FORECAST,
    ]
    found_forecast = False
    matched_pattern = None
    for pattern in forecast_patterns:
        if re.search(pattern, last_cycle_content, flags=re.IGNORECASE | re.DOTALL):
            found_forecast = True
            matched_pattern = pattern
            break

    assert found_forecast, (
        f"Most recent cycle section (`{last_cycle_label}`) in pr-change-log.md "
        f"does not contain a `main post-merge (forecast)` line with a numeric count. "
        f"Per PI-016 (cycle 9) and PI-018 (cycle 11 amendment), every cycle "
        f"row must forecast a `main` post-merge count with actual numbers "
        f"(e.g., '125 passed + 1 skipped + 1 expected-fail-on-main').\n\n"
        f"Add ONE of the following forms to the `{last_cycle_label}` section:\n"
        f"  - A heading (with numbers in the body):\n"
        f"      ### Main post-merge (forecast)\n"
        f"      - **`main` post-merge (forecast):** 125 passed + 1 skipped + 1 expected-fail-on-main\n"
        f"  - A bullet (with numbers on the same line):\n"
        f"      - **`main` post-merge (forecast, per PI-016):** 125 passed + 1 skipped + 1 expected-fail-on-main\n"
        f"  - A plain line (with numbers on the same line):\n"
        f"      main post-merge (forecast): 125 passed + 1 skipped + 1 expected-fail-on-main\n\n"
        f"Three failure modes this test catches:\n"
        f"  (a) Missing forecast line entirely.\n"
        f"  (b) Forecast present as a placeholder (TBD, XXX, to be determined)\n"
        f"      without a numeric count.\n"
        f"  (c) Narrative mention only (no explicit forecast line).\n\n"
        f"Note: narrative mentions of 'main post-merge' or 'forecast' do NOT\n"
        f"satisfy this test. The forecast must be on its own line in one of\n"
        f"the three forms above with a numeric count in `<digit> passed` shape.\n"
        f"See workflow-nightly-dreaming.md Stage 11 for the convention."
    )


def test_pr_change_log_includes_collect_only_forecast_baseline() -> None:
    """Most recent cycle section in pr-change-log.md must include a captured
    collect-only baseline (PI-020, cycle 12).

    Cycle authors capture the precise baseline by running:
        python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"
    and quote the captured count as `Collected-test baseline (forecast): <N> tests collected`.

    The captured baseline is the precise forecast, not a reasoned estimate.
    PI-018 / Stage 11 then verifies the actual `main` count against this captured baseline.

    Real-world fitness (cycle-12 review round 5): the captured number must also be
    PLAUSIBLE — within ±25 of the current collect-only count. This catches wildly
    wrong baselines (e.g., a cycle author who writes "999 tests collected" without
    actually running the command) while accommodating legitimate drift from
    reviewer-driven test additions. Per the cycle-12 author’s own forecast
    (cycle-12 row "Main post-merge (forecast)"), the captured baseline is the
    count at forecast-time and is expected to drift by small amounts as reviewer
    rounds add tests; a drift of ±25 is a reasonable upper bound for a 5-round
    review (each round typically adds 1-5 tests, plus parametrized-expansion
    additions from any new files in `.openclaw/dreaming/`).
    """
    import subprocess
    from pathlib import Path

    pr_change_log = (Path(__file__).resolve().parents[2] / ".openclaw" / "dreaming" / "pr-change-log.md").read_text()
    sections = re.split(r"^## Cycle-\d+", pr_change_log, flags=re.MULTILINE)
    assert len(sections) > 1, "pr-change-log.md must have at least one Cycle- section"
    last_section = sections[-1]
    cycle_match = re.search(r"^## (Cycle-\d+)", pr_change_log[pr_change_log.rindex("## Cycle-"):], flags=re.MULTILINE)
    last_cycle_label = cycle_match.group(1) if cycle_match else "Cycle-?"

    # The numeric-count requirement (the cycle-12 round-2 fix) is on the
    # SAME line as the baseline marker; the cycle-11 round-2 / round-5
    # fix for `main post-merge (forecast)` uses the same shape. The
    # cycle-12 round-2 fix adds three forms to mirror cycle-11's three
    # regexes: heading + body, bullet (with optional markdown-bold
    # prefix), and plain line. The cycle-12 round-5 fix extracts the
    # captured number from the matched line for the real-world-fitness
    # drift check below, AND widens the bullet regex to actually accept
    # the bold form `**Collected-test baseline (forecast):** N tests
    # collected` (the cycle-12 round-2 review log claimed this form
    # passed, but the regex actually rejected it — second-pass catch).
    NUMERIC_BASELINE_RE = re.compile(r"(\d+)[ \t]+tests?[ \t]+collected")
    # Match the baseline MARKER (without requiring a number on the same line).
    # The bullet form allows optional `**` markdown-bold AROUND the label
    # (e.g., `**Collected-test baseline (forecast):**` or `**Collected-test
    # baseline (forecast, per PI-020):**`). The Round-2 review log claimed
    # these forms passed, but the original regex did not actually accept
    # them — second-pass catch.
    marker_re = re.compile(
        r"(?:^|\n)[ \t]*(?:"
        r"#{2,4}[ \t]+\*?Collected-test baseline[ \t]+\(forecast\)\*?:?"  # heading form (with optional bold + colon)
        r"|[-*][ \t]+(?:\*+\s*)?Collected-test baseline[ \t]+\(forecast\)(?:\s*\**)?:"  # bullet form (with optional bold around label, ** after colon)
        r"|Collected-test baseline[ \t]+\(forecast\):"  # plain line form
        r")",
        flags=re.IGNORECASE,
    )
    captured_count: int | None = None
    marker_m = marker_re.search(last_section)
    if marker_m:
        # Find the body line for the heading form (the next non-empty line
        # after the heading), or the same line for bullet/plain forms.
        marker_end = marker_m.end()
        # Find the next newline AFTER marker_end (using marker_end + 1 to
        # avoid matching a newline at marker_end itself, which can happen
        # when the regex consumed the leading newline via (?:^|\n)).
        next_newline = last_section.find("\n", marker_end + 1)
        if next_newline == -1:
            next_newline = len(last_section)
        same_line_text = last_section[marker_end:next_newline]
        num_m = NUMERIC_BASELINE_RE.search(same_line_text)
        if num_m:
            captured_count = int(num_m.group(1))
        else:
            # Heading form: look at the next non-empty body line.
            body_start = next_newline + 1
            # Skip blank lines.
            while body_start < len(last_section) and last_section[body_start] == "\n":
                body_start += 1
            body_end = last_section.find("\n", body_start)
            if body_end == -1:
                body_end = len(last_section)
            body_text = last_section[body_start:body_end]
            num_m = NUMERIC_BASELINE_RE.search(body_text)
            if num_m:
                captured_count = int(num_m.group(1))
    assert captured_count is not None, (
        f"Most recent cycle section (`{last_cycle_label}`) in pr-change-log.md "
        f"does not contain a `Collected-test baseline (forecast): <N> tests collected` "
        f"line with a numeric count.\n\n"
        f"Per PI-020 (cycle 12), every cycle row must capture the precise baseline by running:\n"
        f"    python3 -m pytest tests/dreaming/ --collect-only -q | grep 'tests collected'\n\n"
        f"and quoting the captured count. The captured baseline is the precise forecast,\n"
        f"not a reasoned estimate. This is the symmetry partner of PI-018 / Stage 11\n"
        f"(post-merge verification): pre-merge baseline-capture + post-merge verification.\n\n"
        f"Add ONE of the following forms to the `{last_cycle_label}` section:\n"
        f"  - A heading (with numbers in the body):\n"
        f"      ### Collected-test baseline (forecast)\n"
        f"      - **Collected-test baseline (forecast):** 132 tests collected\n"
        f"  - A bullet (with numbers on the same line):\n"
        f"      - **Collected-test baseline (forecast, per PI-020):** 132 tests collected\n"
        f"  - A plain line (with numbers on the same line):\n"
        f"      Collected-test baseline (forecast): 132 tests collected\n\n"
        f"Three failure modes this test catches:\n"
        f"  (a) Missing baseline line entirely.\n"
        f"  (b) Baseline present as a placeholder (TBD, XXX, to be determined)\n"
        f"      without a numeric count.\n"
        f"  (c) Narrative mention only (no explicit baseline line).\n\n"
        f"Note: narrative mentions of 'Collected-test baseline' or 'forecast' do NOT\n"
        f"satisfy this test. The baseline must be on its own line in one of the three\n"
        f"forms above with a numeric count in `<digit> tests collected` shape.\n"
        f"See workflow-nightly-dreaming.md Stage 0a for the convention."
    )

    # Real-world fitness check (cycle-12 review round 5): re-run collect-only
    # at validation-time and verify the captured baseline is within a
    # reasonable tolerance of the current count. The cycle author captures
    # the baseline at forecast-time, so legitimate drift is expected as
    # reviewer rounds add tests. A drift of ±25 is the upper bound for a
    # 5-round review (each round typically adds 1-5 tests for new test
    # functions, plus parametrized-expansion additions from any new files
    # in `.openclaw/dreaming/`).
    repo_root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/dreaming/", "--collect-only", "-q"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    current_match = re.search(r"(\d+) tests collected", proc.stdout)
    assert current_match, (
        f"Could not parse current collect-only count from pytest output:\n"
        f"  stdout: {proc.stdout!r}\n"
        f"  stderr: {proc.stderr!r}"
    )
    current_count = int(current_match.group(1))
    drift = abs(captured_count - current_count)
    MAX_DRIFT = 25  # cycle-12 round-5 tolerance
    assert drift <= MAX_DRIFT, (
        f"Most recent cycle section (`{last_cycle_label}`) has a captured baseline of "
        f"{captured_count} tests, but the current collect-only count is {current_count} "
        f"tests (drift: {drift}). This exceeds the round-5 tolerance of ±{MAX_DRIFT} tests.\n\n"
        f"This usually means one of:\n"
        f"  (a) The cycle author wrote a baseline number without actually running\n"
        f"      `python3 -m pytest tests/dreaming/ --collect-only -q | grep 'tests collected'`.\n"
        f"      Re-run the command and update the captured baseline in the cycle row.\n"
        f"  (b) Reviewer-driven changes have legitimately drifted the test count beyond\n"
        f"      ±{MAX_DRIFT} since the cycle author captured the baseline. Re-run the command\n"
        f"      and update the captured baseline to reflect the current count. The\n"
        f"      'Main post-merge (forecast)' section should also be updated to explain\n"
        f"      the drift (per PI-018 / Stage 11).\n\n"
        f"Per PI-020, the captured baseline must be a captured number, not a reasoned\n"
        f"estimate. The tolerance of ±{MAX_DRIFT} accommodates legitimate drift from\n"
        f"reviewer-driven test additions (each round typically adds 1-5 tests, plus\n"
        f"parametrized-expansion additions from any new files in `.openclaw/dreaming/`);\n"
        f"a larger drift indicates either a stale capture or a wildly wrong baseline.\n"
        f"See workflow-nightly-dreaming.md Stage 0a for the convention."
    )
