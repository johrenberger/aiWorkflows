# Handoff Contracts

This document defines the explicit handoff paths from `component-test-generation` outputs to other workflows and to humans. The handoffs are **manual** in v1 — there is no auto-pipeline. The user reads the manifest and decides what to do next.

## Handoff manifest

Every run of `component-test-generation` produces `handoff-manifest.json` with this structure:

```json
{
  "produced_at": "<ISO-8601>",
  "profile": "safe|balanced|aggressive",
  "analysis_run_id": "<id>",
  "target_repo": "<url>",
  "target_branch": "<branch>",
  "generation_branch": "<branch>",
  "pr_url": "<url or null if DRY_RUN>",
  "dry_run": false,
  "artifacts": [
    {
      "file": "<name>.json",
      "description": "<text>",
      "consumer": "human-review|application-mutation-testing|application-test-coverage|component-test-analysis|none",
      "consumer_input_mapping": "<how to consume>"
    }
  ]
}
```

## Handoff 1: PR → human reviewer

**Source:** The PR opened on the target repo in Phase 8.
**Consumer:** Human (you).
**Goal:** Review and merge the generated tests.

**What to look at, in order:**

1. **The PR description.** It has the summary, the selected gaps, the deferred list, the needs-human-review list, and the test execution summary. Read this first.
2. **`TODO_test-generation.md`** in `OUTPUT_DIR/`. The full ledger — context, detection results, generation log, repair log, PR body. This is the audit trail.
3. **The diff itself.** Each test file. Look for:
   - Tests that use reflection (CTG-VAL-34 should have caught these, but check anyway)
   - Tests that use Thread.sleep / time.sleep (CTG-VAL-35 should have caught these)
   - Tests that are too thin (one-line mocks) — these are usually wrong
   - Tests that are too thick (mocking 6 things for a 2-line method) — these are usually wrong
   - Tests marked `@Disabled` / `pytest.mark.skip` / `it.skip` — these need human attention
4. **`selected-gaps.json`** in `OUTPUT_DIR/`. Cross-check that the selected gaps match what you expected. The `deferred` array tells you what's left to tackle in future runs.

**Merge decision:**

- ✅ Merge if all tests pass and there are no `@Disabled` tests (or you're OK with the `@Disabled` ones).
- 🛑 Request changes if:
  - The generation touched production code without your knowledge (check the PR's `Files changed` tab)
  - There are tests that don't actually test the gap (use the gap's `trigger` and `expected_result` as the spec)
  - The deferred list has surprises (gaps that should have been generated)
- 🗑️ Close without merging if:
  - The detected stack is wrong (re-run the analysis; this run is on stale data)
  - The PR is too large (> 1000 lines of new code) — split it with `MAX_GAPS_PER_RUN`

## Handoff 2: generation branch → application-mutation-testing

**Source:** The generation branch (`test-generation/<runid>`).
**Consumer:** `application-mutation-testing`.
**Goal:** Evaluate the generated tests via mutation. A high mutation score on the new tests means they actually catch bugs; a low score means they're not testing the contract.

**Translation:**

- `INPUT_GITHUB_REPO` = the target repo
- `INPUT_BRANCH` = the generation branch
- `INPUT_MUTATION_TARGETS` = the `CTA-COMP-NNN` IDs from the `selected-gaps.json` `selected[].component_id`
- `INPUT_MUTATION_EXCLUSIONS` = none (the new tests are the point — don't exclude)
- `MUTATION_QUALITY_GATE` = `warn` (v1: this is a measurement, not a block)

**Why this is the right next step:** The generation workflow is good at creating test scaffolding but cannot prove the tests are *meaningful*. Mutation testing is the only way to measure test quality. If the generated tests have a mutation score ≥ 60%, they're catching real bugs. If the score is < 30%, the tests are essentially "did the method get called" checks with no assertion power.

## Handoff 3: generation branch → application-test-coverage

**Source:** The generation branch (`test-generation/<runid>`).
**Consumer:** `application-test-coverage`.
**Goal:** Re-measure coverage on the new branch. The diff between the pre-generation coverage and the post-generation coverage is the measurable value of this run.

**Translation:**

- `INPUT_GITHUB_REPO` = the target repo
- `INPUT_BRANCH` = the generation branch
- `MODULE_LIST` = the modules from the `selected-gaps.json` `selected[].source_file` (group by module)
- `COVERAGE_TARGET_PER_FILE` = the same target the analysis recommended (no point aiming higher than what the analysis said was needed)
- `ENABLE_TESTABILITY_CLASSIFICATION` = true (use the analysis' T1/T2/T3/T4 risk tier)
- `ALLOW_PRODUCTION_FIXES` = false (the coverage run is read-only)

**Expected outcome:** Coverage of the targeted components should increase by 10-30% per `MAX_GAPS_PER_RUN=10` run. If it doesn't, the generated tests are not exercising the right methods (the gap's `trigger` was misinterpreted).

## Handoff 4: needs-human-review list → follow-up

**Source:** The `needs_human_review` list in the PR description and `test-execution-results.json`.
**Consumer:** Human (you) + `component-test-analysis` (re-run with the new info).
**Goal:** Convert the `@Disabled` placeholders into real, passing tests.

**Process:**

1. Read the failure message for each `@Disabled` test.
2. Diagnose: is the failure because (a) the test is wrong, or (b) the source code is wrong?
3. If (a), fix the test. Re-enable it. Commit on the same branch.
4. If (b), the gap is not just a test gap — it's a bug. Open a separate issue/PR for the source code fix. Keep the test `@Disabled` until the source is fixed. Or, in `aggressive` mode, fix the source in the same PR.
5. Re-run the analysis on the updated branch. The new run will reflect the bug fix; the gap may be downgraded or removed.

## Handoff 5: deferred list → next run

**Source:** The `deferred` array in `selected-gaps.json`.
**Consumer:** Next `component-test-generation` run.
**Goal:** Tackle the deferred gaps in a follow-up run.

**Translation:**

- `INPUT_GITHUB_REPO` = same target repo
- `INPUT_BRANCH` = the generation branch from this run (or `main` if this PR was merged)
- `INPUT_ANALYSIS_DIR` = same analysis path (or a re-run if the analysis is stale)
- `GAP_PRIORITY_FILTER` = same as this run, or expand to `P0-P2` if you want to drain more
- `MAX_GAPS_PER_RUN` = same as this run, or expand if you're comfortable with larger PRs

**Why this is iterative, not a one-shot:** The first run captures the easiest gaps. The deferred list tells you what the generator couldn't handle (missing testability, unresolvable dependencies, missing templates). Each iteration of the workflow + improvements to the generator drains more of the backlog.

## Handoff 6: TODO_test-generation.md → audit trail

**Source:** The full ledger in `OUTPUT_DIR/TODO_test-generation.md`.
**Consumer:** Anyone (you, a teammate, an auditor).
**Goal:** Reconstruct what this run did, why, and what the outcome was.

**What it contains:**

- Context: target repo, branch, profile, filter, max gaps, DRY_RUN flag
- Pre-flight tool versions and disk space
- Repository acquisition: clone URL, branch, base commit
- Stack re-detection: full detected stack + diff against the analysis
- Gap selection: filters applied, selected gaps, deferred gaps with reasons
- Templates applied: per-gap template + imports
- Generation log: per-test-file AST parse result, behaviors tested, fixtures added, linter result
- Test execution: build detected, command, results, repair log
- PR assembly: branch, commits, files changed, PR URL, PR body
- Handoff: manifest emitted, consumers

**Retention:** Keep the ledger for the lifetime of the project. It is the audit trail for "where did these tests come from?"

## What does NOT handoff

- **The detection JSONs** (`detected-stack.json`, `templates-applied.json`) are intermediate — they're useful for audit but not consumed by other workflows.
- **The TODO ledger** is documentation, not an input to other workflows.
- **The generated test files in `OUTPUT_DIR/_repo/`** are a copy of what's in the PR — review the PR, not the local copy.

## Manual vs auto handoff

v1 handoffs are **manual**. The user reads the PR, decides whether to merge, and runs the next workflow (mutation testing, coverage) explicitly. Future versions may support `AUTO_HANDOFF=true`:

- After PR is opened, wait for CI to pass.
- Auto-trigger `application-mutation-testing` on the branch.
- Post the mutation results as a PR comment.
- Auto-trigger `application-test-coverage` on the branch.
- Post the coverage delta as a PR comment.

This is deferred because:
- It triples the CI cost of a generation run.
- Mutation testing can be slow (hours for large repos).
- The user usually wants to review the tests before running more automation.
- A bad auto-handoff could generate noise (e.g. mutation results on `@Disabled` tests are meaningless).

If you need auto-handoff for a specific project, do it as a wrapper script, not as workflow logic.
