# Regression Scenarios

BDD-style Given/When/Then. Each scenario has a single evidence reference, severity, acceptance criteria, pass/fail criteria, validation method, and owner.

Severities: `blocker | warning | informational`
Owners: `MiniMax | deterministic_tool | human`

RS-001 through RS-009 are carried from cycle 1. RS-010 through RS-012 are new in cycle 2.

---

## RS-001 — SGP mypy permissive-to-strict progression

- **Evidence reference:** EV-001, EV-007
- **Affected workflow or skill:** SGP, generic validation discipline
- **Severity:** blocker
- **Given** a project is about to flip a validation gate (mypy, lint, coverage, mutation budget) from permissive to strict
- **When** the gate is flipped
- **Then** the previous permissive state must be captured as an explicit test before the flip
- **Expected behavior:** `git log` shows: (a) commit adding "lock in permissive state" test, (b) progression script, (c) strict-flip commit, in that order.
- **Pass / fail criteria:** Pass if all three commit types exist and are in order. Fail if the strict-flip commit precedes the permissive-lock-in commit.
- **Validation method:** `git log --grep` + custom check script
- **Owner:** deterministic_tool

---

## RS-002 — SGP mutation-testing survival budget

- **Evidence reference:** EV-001, EV-007
- **Affected workflow or skill:** SGP, any decision-making module
- **Severity:** blocker
- **Given** a module contains routing, scoring, classification, or recommendation logic
- **When** mutation testing is run against that module
- **Then** the survivor rate must be at or below the configured budget (default: ≤50% survivors); **additionally the project's gate-stack (unit + branch coverage + mutation + mypy strict + ruff + ≥1 property test for invariants) must survive** — see cycle-2 reframing in L-002 and L-011.
- **Expected behavior:** CI fails when survivor rate exceeds budget; failing on any single gate without the others also fails the gate-stack.
- **Pass / fail criteria:** Pass if the gate-stack as a whole passes. Fail if any single gate is missing from the stack.
- **Validation method:** mutation-testing CI job + gate-stack presence check
- **Owner:** deterministic_tool

---

## RS-003 — task-state-management skip-state rule

- **Evidence reference:** EV-002
- **Affected workflow or skill:** `task-state-management`
- **Severity:** blocker
- **Given** a task in any post-`in_progress` state (e.g., `testing_done`)
- **When** a transition to `closed` is requested via the skip-state rule
- **Then** a `decisions/<id>.md` entry must exist naming the skipped states
- **Expected behavior:** `transition.py closed <task_id>` succeeds only when the decision entry exists and names each skipped state.
- **Pass / fail criteria:** Pass if decision entry exists with all skipped states named. Fail otherwise.
- **Validation method:** `lint-task-state.py`
- **Owner:** deterministic_tool

---

## RS-004 — DOTALL-regex anti-pattern in task-state validators

- **Evidence reference:** EV-002
- **Affected workflow or skill:** `task-state-management/scripts/lint-task-state.py` (and any future validator)
- **Severity:** warning
- **Given** a validator script under the skills tree
- **When** the script is reviewed
- **Then** it must not use `re.DOTALL` to match across named sections (`## Notes`, `## Resolution`, etc.)
- **Expected behavior:** Validators use line-by-line scanning with explicit section detection. `re.DOTALL` matches are flagged in code review.
- **Pass / fail criteria:** Pass if no `re.DOTALL` use in validator scripts. Fail otherwise.
- **Validation method:** `grep -n "re.DOTALL" skills/**/scripts/*.py` returns empty.
- **Owner:** deterministic_tool

---

## RS-005 — wrong-SyncRun update on finalizeFailure

- **Evidence reference:** EV-003 (CRITICAL #1, slice 3.1 review)
- **Affected workflow or skill:** `BusinessOperationsDashboard` sync runner
- **Severity:** blocker
- **Given** two `SyncRun` rows for the same `(tenantId, connectorId)` are concurrently in `running` state
- **When** the runner finalizes one as failure
- **Then** it must update the SyncRun it owns (by id), not `findFirst({status:'failure'})`
- **Expected behavior:** FinalizeFailure updates the SyncRun whose id was returned by `runConnectorIngest`. No other SyncRun is touched.
- **Pass / fail criteria:** Pass if the BDD scenario exercising concurrent finalize asserts that the correct SyncRun id is updated. Fail otherwise.
- **Validation method:** BDD scenario `tests/features/sync/concurrent-finalize.feature`
- **Owner:** deterministic_tool

---

## RS-006 — `/health` multi-tenant info leak

- **Evidence reference:** EV-003 (HIGH #3, slice 3.1 review)
- **Affected workflow or skill:** `BusinessOperationsDashboard` worker `/health`
- **Severity:** blocker
- **Given** the worker `/health` endpoint is reachable on a `0.0.0.0` bind
- **When** an unauthenticated caller issues `GET /health`
- **Then** the response must not contain any tenant-derived field (tenant count, tenant list, last-sync-by-tenant, etc.)
- **Expected behavior:** Response shape is exactly `{status, db, lastTickAt, inFlight}` (or smaller). `db` is `true`/`false`. No aggregation across tenants.
- **Pass / fail criteria:** Pass if response contains zero tenant-derived fields. Fail otherwise.
- **Validation method:** BDD scenario `tests/features/worker/health-contract.feature`
- **Owner:** deterministic_tool

---

## RS-007 — double-click idempotency on `POST /connectors/:provider/sync`

- **Evidence reference:** EV-003 (CRITICAL #2, slice 4.1 review)
- **Affected workflow or skill:** `BusinessOperationsDashboard` sync endpoint
- **Severity:** blocker
- **Given** a queued `SyncRun` exists for `(tenantId, provider)`
- **When** a second `POST /connectors/:provider/sync` is issued before the first finishes
- **Then** the second response returns the existing queued `runId` (idempotent)
- **Expected behavior:** Same `runId` returned for both POSTs; only one SyncRun row created.
- **Pass / fail criteria:** Pass if both POSTs return the same `runId` and the DB has exactly one queued run for `(tenantId, provider)`. Fail otherwise.
- **Validation method:** BDD scenario `tests/features/sync/double-click-idempotency.feature`
- **Owner:** deterministic_tool

---

## RS-008 — OpenClaw run log evidence minimum

- **Evidence reference:** EV-004
- **Affected workflow or skill:** dreaming workflow Stage 1
- **Severity:** warning
- **Given** a dreaming cycle is about to run
- **When** Stage 1 collects evidence
- **Then** an OpenClaw run log must exist and contain at minimum: per-turn start timestamp, completion timestamp, selected skills, tool errors, retries, and outcome
- **Expected behavior:** `find` returns at least one JSONL file under the configured log directory; each line contains the required fields.
- **Pass / fail criteria:** Pass if the log exists, is JSONL, and each line has the required fields. Fail otherwise.
- **Validation method:** deterministic JSONL parser
- **Owner:** deterministic_tool

---

## RS-009 — cron tick observable side-effect

- **Evidence reference:** EV-005
- **Affected workflow or skill:** `BusinessOperationsDashboard` scheduler
- **Severity:** informational
- **Given** the scheduler is configured to run every N seconds
- **When** a tick fires
- **Then** a deterministic, observable side-effect must occur (e.g., `lastTickAt` updated in `/health`, audit row written, or similar)
- **Expected behavior:** After a configured interval without any other activity, the side-effect is present and equal to the most recent tick.
- **Pass / fail criteria:** Pass if a deterministic side-effect can be observed for a tick. Fail if the tick is silent (no observable trace).
- **Validation method:** BDD scenario with time-based assertion
- **Owner:** deterministic_tool

---

## RS-010 (NEW) — Makefile local-validation prereq degradation

- **Evidence reference:** EV-008, EV-009
- **Affected workflow or skill:** dreaming workflow + any workflow following PI-008 pattern
- **Severity:** warning
- **Given** the Makefile target (`make dreaming-validate` or equivalent) needs `gh` CLI to fetch the merge-base via GitHub API
- **When** a developer runs the target on a machine without `gh`
- **Then** the target must degrade to `git merge-base HEAD origin/main` (or skip gracefully), not fail
- **Expected behavior:** Target exits 0 with a clear message that the API path was skipped and the local-merge-base path was used. If neither is available, the target prompts the developer to install `gh` or set `DREAMING_MERGE_BASE` explicitly.
- **Pass / fail criteria:** Pass if `gh` missing → degrades to `git merge-base` path → exit 0; if both unavailable → exit 0 with "skip" message. Fail if missing `gh` causes hard exit.
- **Validation method:** Run `make dreaming-validate` with `PATH` stripped of `gh` (or with `gh` aliased to `false`).
- **Owner:** deterministic_tool

---

## RS-011 (NEW) — branch-name regex accepts cycle suffix

- **Evidence reference:** EV-008, L-010
- **Affected workflow or skill:** dreaming workflow
- **Severity:** informational
- **Given** a dreaming branch is named `dreaming/nightly-execution-quality-YYYY-MM-DD`
- **When** an optional `-N` cycle suffix is appended (e.g., `-cycle-2`, `-r2`)
- **Then** the test must accept the suffix and not fail
- **Expected behavior:** Test passes for `dreaming/nightly-execution-quality-2026-06-29`, `dreaming/nightly-execution-quality-2026-06-29-cycle-2`, `dreaming/nightly-execution-quality-2026-06-29-r2`, etc.
- **Pass / fail criteria:** Pass for all three forms above. Fail for branch names not matching the prefix.
- **Validation method:** parametrized pytest case (currently `test_current_branch_uses_dreaming_prefix`).
- **Owner:** deterministic_tool

---

## RS-012 (NEW) — commit-prefix test skips on empty range

- **Evidence reference:** EV-008, L-013
- **Affected workflow or skill:** dreaming workflow
- **Severity:** informational
- **Given** a branch has no commits ahead of its merge-base (e.g., freshly-checked-out or pre-first-commit)
- **When** `test_commits_use_chore_dreaming_prefix` is run
- **Then** the test must skip, not fail
- **Expected behavior:** `pytest.skip("No commits yet in range ...")` is emitted. Exit code 0. Test is reported as `s` (skipped), not `F` (failed).
- **Pass / fail criteria:** Pass on freshly-checked-out branch with no commits. Fail only when there ARE commits and at least one does not start with `chore(dreaming):`.
- **Validation method:** checkout a freshly-created branch without committing; run `make dreaming-validate`.
- **Owner:** deterministic_tool

---

## RS-013 — Branch-name test must not execute on `main` pushes (NEW)

- **Evidence reference:** EV-010
- **Affected workflow or skill:** `nightly-dreaming-validation.yml`, `tests/dreaming/test_pr_readiness.py::test_current_branch_uses_dreaming_prefix`
- **Severity:** blocker
- **Given** the nightly-dreaming-validation workflow runs the dreaming test suite
- **When** it is triggered by a push to `main`
- **Then** `test_current_branch_uses_dreaming_prefix` must either skip or be filtered by a workflow-level guard; it must not fail with "Current branch 'main' does not start with 'dreaming/nightly-execution-quality-'"
- **Expected behavior:** On a `push` event where the ref is `main`, the test for branch naming either (a) does not run because the workflow `on: push: branches:` excludes main, or (b) skips if it does run, with a clear "skipped on main push" message.
- **Pass / fail criteria:** Pass if the suite reports 0 failures on a push to `main`. Fail otherwise.
- **Validation method:** `gh run list --workflow=nightly-dreaming-validation --limit=10 --json conclusion,headBranch` shows zero `failure` rows on `headBranch=main`.
- **Owner:** deterministic_tool

---

## RS-014 — Branch-uniqueness test must exclude the current branch from the count (NEW)

- **Evidence reference:** EV-011
- **Affected workflow or skill:** `tests/dreaming/test_pr_readiness.py::test_only_one_dreaming_branch_exists`
- **Severity:** warning
- **Given** a developer has more than one dreaming branch on their local checkout (e.g., cycle-2 not yet deleted; cycle-3 freshly created)
- **When** the test enumerates dreaming branches
- **Then** the current branch must be excluded from the count
- **Expected behavior:** The test counts "other dreaming branches" — never the branch we are on. A pre-existing cycle's branch is fine; only multiple *other* branches fails the invariant.
- **Pass / fail criteria:** Pass if the test passes with cycle-2 and cycle-3 both on disk, on a fresh cycle-3 checkout. Fail otherwise.
- **Validation method:** `git checkout dreaming/nightly-execution-quality-2026-06-29-cycle-3 && make dreaming-validate` returns 105 passed, 0 failed.
- **Owner:** deterministic_tool

---

## RS-015 — Workspace precheck must surface prior-cycle branch remains (NEW)

- **Evidence reference:** EV-012
- **Affected workflow or skill:** `Makefile::dreaming-precheck`
- **Severity:** informational
- **Given** a developer starts a new dreaming cycle while a prior cycle's branch remains on disk
- **When** they run `make dreaming-precheck`
- **Then** the output must list the prior branch by name (not just the total count)
- **Expected behavior:** The precheck `Dreaming branches on disk:` section enumerates all matching branches; the dev sees the lingering branch and removes it before validation-time.
- **Pass / fail criteria:** Pass if `make dreaming-precheck` reports the lingering branch by name. Fail if it only reports a count.
- **Validation method:** `make dreaming-precheck` run on a workspace with two dreaming branches.
- **Owner:** deterministic_tool

---

## RS-016 — Long-carried PIs must surface their scope splits (NEW)

- **Evidence reference:** EV-014, L-016
- **Affected workflow or skill:** `.openclaw/dreaming/proposed-improvements.md`
- **Severity:** informational
- **Given** a PI is carried forward through 3+ cycles without applying
- **When** it's reviewed in any later cycle
- **Then** the PI body must either (a) list all its constituent scope pieces as separate sub-items, or (b) explicitly note it is unified (single owner, single package)
- **Expected behavior:** PIs in `proposed-improvements.md` either enumerate their work packages or carry a "single-package" note.
- **Pass / fail criteria:** Pass if the carried PI either enumerates packages or says "single package". Fail if it lumps multiple work units behind one PI title.
- **Validation method:** Manual review of `proposed-improvements.md`; cycle-5 audit produced the PI-006 split; cycle-6 elevated the runtime piece to **PI-006a** (own entry, own status, own handoff document).
- **Owner:** human


## RS-017 — `cyber-signal-daily` cron deliverable freshness (NEW, cycle 7)

- **Evidence reference:** EV-016, PI-014, cron `cyber-signal-daily` runs history
- **Affected workflow or skill:** the `cyber-signal-daily` cron + the brief-delivery contract to Telegram chat 8654084485
- **Severity:** warning (currently `failing` — the gate is unmet, but the cron still delivers a brief; the failure mode is "stale brief" not "no brief")
- **Given** the `cyber-signal-daily` cron fires at 06:30 America/Chicago daily
- **And** the pre-fetched feed file at `/tmp/cyber-signal-feeds.json` should be refreshed by `scripts/cyber-signal-fetch-feeds.sh` (or equivalent) before each cron run
- **When** a delivered Telegram brief is inspected for the `pubDate_ts` of its HIGH/MEDIUM items
- **Then** at least one selected item must have `pubDate_ts` within 48 hours of the cron's `runAtMs`
- **Expected behavior:** daily briefs contain at least one fresh item. The 19-day-stale condition observed in cycle 7 (last fresh fetch 2026-06-11) is the failure this scenario pins.
- **Pass / fail criteria:**
  - **Pass** if any selected item in the delivered brief has `pubDate_ts` within 48 hours of the cron's `runAtMs`.
  - **Fail** if all selected items are older than 48 hours (the cycle-7 condition).
  - **Fail** if the brief was not delivered at all.
- **Validation method:** Inspect the most recent cron-run summary (cron `runs` history). The `summary` field for the `ok` run already calls out staleness in plain English ("Feed data is N days stale"). RS-017 is a structured check on the same property.
- **Owner:** human (this is a cron/tooling health check, not a code-side invariant)
- **Status:** failing (cycle 7 baseline; expected to flip to `passing` when PI-014 is applied)


## RS-018 — Most recent cycle's Trigger section must declare surface scope (NEW, cycle 8)

- **Evidence reference:** EV-017, PI-015, Stage -2 in `workflow-nightly-dreaming.md`
- **Affected workflow or skill:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage -2); `.openclaw/dreaming/nightly-summary.md` (Trigger section of the most recent cycle)
- **Severity:** warning (currently `failing` baseline; expected to flip to `passing` when cycle 8 merges)
- **Given** a cycle is being authored
- **And** the cycle author's Trigger section in `nightly-summary.md` is the first place the cycle scope becomes visible
- **When** the Trigger section is reviewed
- **Then** it must contain all four Stage -2 field labels: "Workflow target", "Surface area", "Dreaming-ledger scope", "Cycle-size budget"
- **Expected behavior:** Every new cycle pre-declares its scope before Stage -1's workspace pre-check, so scope decisions are made at human time, not retrofit at audit time.
- **Pass / fail criteria:**
  - **Pass** if all four labels appear in the most recent cycle's Trigger section (case-insensitive substring match).
  - **Fail** if any of the four labels are missing.
  - **Fail** if there is no Trigger section at the top of `nightly-summary.md`.
- **Validation method:** `tests/dreaming/test_pr_readiness.py::test_declares_surface_scope_in_trigger`. The test is forward-looking: it requires the **most recent cycle's** Trigger section to have the new format. Past cycles' Trigger sections are preserved as historical record.
- **Owner:** human (the cycle author)
- **Status:** failing (cycle 8 baseline; expected to flip to `passing` when cycle 8's Trigger is written in the new format)


## RS-019 — Working tree in `.openclaw/dreaming/` must be clean relative to HEAD after commits (NEW, cycle 10)

- **Evidence reference:** EV-019, PI-017, Stage -3 in `workflow-nightly-dreaming.md`
- **Affected workflow or skill:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage -3); `.openclaw/dreaming/` (cycle working area); `git commit --amend` workflow
- **Severity:** warning (currently `failing` baseline; expected to flip to `passing` when cycle 10 merges and the cycle-10 commit is in sync with the working tree)
- **Given** a cycle author has just run `git commit` or `git commit --amend`
- **And** the cycle working area is `.openclaw/dreaming/`
- **When** `git status --short -- .openclaw/dreaming/` is run
- **Then** the output must contain no modified tracked files (lines starting with `M`, ` M`, `MM`, `A`, etc.; untracked `??` lines are excluded)
- **Expected behavior:** The working tree matches HEAD after every commit/amend. Future cycles don't reproduce the cycle-8/cycle-9 working-tree-rescue pattern.
- **Pass / fail criteria:**
  - **Pass** if `git status --short -- .openclaw/dreaming/` produces only `??` (untracked) lines or empty output.
  - **Fail** if any line indicates a modified, added, deleted, or renamed tracked file.
- **Validation method:** `tests/dreaming/test_pr_readiness.py::test_no_post_amend_working_tree_drift`. The test scopes to `.openclaw/dreaming/`; other directories (e.g., `workflows/`) may have intentionally-uncommitted local edits that are out of cycle scope.
- **Owner:** human (the cycle author)
- **Status:** failing (cycle 10 baseline; expected to flip to `passing` after cycle 10's commit lands and the working tree is in sync)


---

## RS-020 — Cycle closeout memos must quote validator output twice with explicit branch context and a forecast-accuracy section (NEW, cycle 11)

- **Evidence reference:** EV-020 (cross-cycle actual-vs-claimed validator count measurements, 2026-07-01)
- **PI reference:** PI-018 (NEW, cycle 11), PI-016 (cycle 9, amended by PI-018)
- **Affected workflow or skill:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage 11); closeout memos in `memory/`; `pr-change-log.md` cycle rows
- **Severity:** warning (forecast-discipline failure is a documentation quality issue, not a runtime failure)
- **Given** a cycle author has just merged PR #N to `main` (the cycle's branch tip becomes `main`'s HEAD)
- **And** the cycle's `pr-change-log.md` row contains a `main post-merge (forecast)` line (per PI-016)
- **When** the cycle author writes the cycle's closeout memo (in `memory/`)
- **Then** the memo must (a) quote `make dreaming-validate` output twice with explicit branch context — once for branch-local (on the cycle's branch tip) and once for `main` post-merge; (b) include a forecast-accuracy section comparing the actual `main` post-merge count to the cycle author's forecast; (c) if the forecast did not match, correct the closeout memo with the actual measured count and document the delta
- **Expected behavior:** Every closeout memo quotes both counts honestly, and any forecast-accuracy delta is recorded (not silently corrected). Future cycles can quote PI-016 numbers with confidence.
- **Pass / fail criteria:**
  - **Pass** if the closeout memo contains both counts (branch-local + main post-merge) with explicit branch context AND a forecast-accuracy section that documents whether the forecast matched.
  - **Fail** if either count is missing, has no branch context, or the forecast-accuracy section is absent.
- **Validation method:** `tests/dreaming/test_pr_readiness.py::test_pr_change_log_forecasts_main_post_merge_count` enforces the forecast-presence discipline in `pr-change-log.md` (forward-looking). The actual forecast-accuracy verification (running `make dreaming-validate` on the actual post-merge `main`) is a manual discipline enforced by Stage 11 of `workflow-nightly-dreaming.md`.
- **Owner:** human (the cycle author)
- **Status:** failing (cycles 6-10 baseline; cycle 11's PI-018 retroactive correction addresses cycles 6-10; expected to flip to `passing` on all cycles 11+)
- **Cycle:** 11

---

## RS-021 — Code-reviewer sub-agent runs 5 rounds with fixed round-4 and round-5 purposes (NEW, cycle 11)

- **Improvement ID:** PI-019
- **Evidence reference:** EV-021, Telegram msgs #11647 (workflow adopted), #11644 (per-round-summary directive), #11770 (5-round budget chosen arbitrarily), #11772 (rounds 4 and 5 locked as fixed purposes). Cycle-10 reviewer log: `.openclaw/dreaming/cycle-10-review-log.md`. Cycle-11 reviewer log: `.openclaw/dreaming/cycle-11-review-log.md`.
- **Severity:** informational
- **Statement:** Every substantive cycle must spawn a code-reviewer sub-agent that runs 5 rounds of review, with per-round summaries dropped back to the parent session after each round. Rounds 1-3 are flex (target the specific risk surface of the cycle's scope). Round 4 is fixed: retroactive-correction accuracy / cross-cycle bookkeeping verification. Round 5 is fixed: real-world fitness / false-positive simulation. The second-pass discipline (verify claimed code changes by reading actual code, not just commit messages) is a default reviewer behavior.
- **Given** a cycle that adds a new test, stage, PI, RS, or EV
- **When** the cycle author has committed the substantive change and is preparing to open the PR
- **Then** the cycle author must spawn a code-reviewer sub-agent that:
  - Reads the cycle's diff between the branch and `main`
  - Runs 5 rounds of review with per-round summaries
  - Applies fix-up commits to the branch as findings warrant (or records "no issues" rounds)
  - Pushes after each fix-up commit
  - Writes a reviewer log to `.openclaw/dreaming/cycle-N-review-log.md` (committed to the cycle's PR)
  - Final summary at the top of the reviewer log with: rounds completed, fix-up commits, no-issue rounds, recommendation
- **Expected behavior:** Every substantive cycle gets a deterministic spine of review rounds (numerical-correctness check + empirical-failure-mode check) regardless of scope. Reviewer logs become artifacts that future cycles can read to understand prior review patterns.
- **Pass / fail criteria:**
  - **Pass** if the reviewer log enumerates 5 rounds, each with a documented finding or no-issue acknowledgment, with at least rounds 4 and 5 explicitly labeled as fixed-purposes (cross-cycle bookkeeping + empirical failure-mode simulation respectively).
  - **Fail** if the reviewer ran fewer than 5 rounds, or rounds 4 and 5 are not labeled as fixed purposes, or no per-round summaries were dropped.
- **Validation method:** Manual review of `.openclaw/dreaming/cycle-N-review-log.md`. The cycle-N reviewer log structure is documented in `.openclaw/dreaming/workflow-nightly-dreaming.md` Stage 12.
- **Owner:** human
- **Status:** passing (cycles 10 and 11 baseline; PI-019 codifies the convention as a workflow stage going forward)
- **Cycle:** 11

---

## RS-022 — Cycle row must include a captured collect-only baseline as the forecast (NEW, cycle 12)

- **Improvement ID:** PI-020
- **Evidence reference:** EV-022, cycle-11 closeout memo (`memory/2026-07-01-cycle-11-closeout.md`).
- **Severity:** informational
- **Statement:** Every cycle row in `pr-change-log.md` must include a `Collected-test baseline (forecast): <N> tests collected` line, where `<N>` is the captured baseline from running `python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"` at forecast-time. The captured baseline is the precise forecast, not a reasoned estimate. The post-merge verification step (PI-018) compares the actual `main` collected count to this captured baseline; if they diverge, the closeout memo must be corrected with the actual measured count and a Forecast-accuracy section explaining the delta.
- **Given** a cycle is being authored
- **When** the cycle author writes the cycle row in `pr-change-log.md`
- **Then** the cycle row must include a `Collected-test baseline (forecast): <N> tests collected` line where `<N>` is the captured baseline from `python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"` at the time the row is written. The line must include a numeric count (not a placeholder like `TBD` or `to be determined`).
- **Expected behavior:** Future cycles' forecasts are captured numbers, not reasoned estimates. Parametrized-test expansions (e.g., from `_all_dreaming_files()`) are reflected in the captured baseline. The post-merge verification step (PI-018) has a deterministic baseline to compare against.
- **Pass / fail criteria:**
  - **Pass** if the cycle row contains a `Collected-test baseline (forecast): <N> tests collected` line with `<N>` being a positive integer that matches the captured baseline from `python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"`.
  - **Fail** if the line is missing, has no numeric count, has a placeholder (`TBD`, `XXX`, `to be determined`), or the captured baseline diverges from the actual `main` collected count without a Forecast-accuracy section in the closeout memo.
- **Validation method:** `tests/dreaming/test_pr_readiness.py::test_pr_change_log_includes_collect_only_forecast_baseline` enforces the forecast-baseline presence. The post-merge verification step (PI-018 / Stage 11) is a manual discipline enforced by the cycle author.
- **Owner:** human
- **Status:** proposed (cycle 12, NEW; PI-020 applies-this-cycle)
- **Cycle:** 12

## RS-023 — Cycle row's `Main post-merge (forecast)` line must use an explicit `collected` or `passed` label with consistent arithmetic (NEW, cycle 13)

- **Improvement ID:** PI-021
- **Evidence reference:** EV-023, cycle-12 final closeout memo (`memory/2026-07-07-cycle-12-final-closeout.md`).
- **Severity:** informational
- **Statement:** Every cycle row's `Main post-merge (forecast)` line in `pr-change-log.md` must use one of three explicit formats: (Format A, preferred) `Main post-merge (forecast): N collected → (N-2) passed + 1 skipped + 1 expected-fail-on-main`, with the explicit `collected → passed` arithmetic shown inline; (Format B, legacy-compatible) `Main post-merge (forecast): N passed + 1 skipped + 1 expected-fail-on-main` paired with a separate `Collected-test baseline (forecast): N tests collected` line in the same cycle row (per Stage 0a), with the arithmetic `N collected → (N-2) passed + 1 + 1` derivable from the row; (Format C, collected-only) `Main post-merge (forecast): N collected` with no `passed` count in the forecast, with the post-merge verification computing the actual `passed` count from the actual collect-only baseline. The forecast's numeric value must be unambiguously either `collected` or `passed`, never both without explicit arithmetic. The cycle-12 row's forecast line was written as `136 passed + 1 skipped + 1 expected-fail-on-main` where `136` was actually the **collected** count (133 branch-local baseline + 3 parametrized-test expansion delta), producing a −2 delta against the actual post-PR #72 count (`134 passed + 1 skipped + 1 expected-fail-on-main`). The arithmetic `136 collected → 134 passed + 1 + 1` matches the actual perfectly; the cycle-12 row's −2 was a forecast-format labeling bug, not a methodology or merge-state failure. PI-021 / RS-023 prevents recurrence by enforcing the label convention going forward.
- **Given** a cycle is being authored with a `Main post-merge (forecast)` line in `pr-change-log.md`
- **When** the cycle author writes the forecast line
- **Then** the line must match Format A (preferred, `N collected → (N-2) passed + 1 skipped + 1 expected-fail-on-main`), Format B (legacy-compatible, `N passed + 1 skipped + 1 expected-fail-on-main` paired with a separate `Collected-test baseline (forecast): N tests collected` line in the same cycle row), or Format C (`N collected` only). The forecast's numeric value must be unambiguously labeled as either `collected` or `passed`, and the post-merge verification step (PI-018 / Stage 11) must be able to compute the actual `passed` count from the actual collect-only baseline.
- **Expected behavior:** Future cycles' forecasts are unambiguously labeled, with explicit `collected → passed` arithmetic. The post-merge verification step (PI-018) compares the actual `main` collect-only count to the forecast's `collected` value (or the row's separate `Collected-test baseline (forecast)` line) and computes the actual `passed` count from the actual collect-only baseline. Format mismatches are caught deterministically.
- **Pass / fail criteria:**
  - **Pass** if the cycle row's `Main post-merge (forecast)` line matches Format A, Format B (with separate baseline line), or Format C, AND the arithmetic between `collected` and `passed` counts is explicit or trivially derivable from a separate baseline line in the same cycle row.
  - **Fail** if the forecast line uses a numeric count without an unambiguous `collected` or `passed` label, or uses a `passed` count whose value is inconsistent with the row's separate `Collected-test baseline (forecast)` line (or with the actual `main` collect-only baseline + the standard −1 skipped −1 expected-fail-on-main deduction).
- **Validation method:** `tests/dreaming/test_pr_readiness.py::test_pr_change_log_forecast_uses_explicit_collected_or_passed_label` (cycle 13 NEW) enforces the label convention. The post-merge verification step (PI-018 / Stage 11) is a manual discipline enforced by the cycle author.
- **Owner:** human
- **Status:** proposed (cycle 13, NEW; PI-021 applies-this-cycle)
- **Cycle:** 13

## RS-024 — Cycle row's `Code-reviewer` section must document inline-review deviation or reviewer-sub-agent run (NEW, cycle 14)

- **Improvement ID:** PI-023
- **Evidence reference:** EV-024, cycle-13 closeout memo (`memory/2026-07-07-cycle-13-closeout.md` "Code-reviewer sub-agent deviation" section).
- **Severity:** informational
- **Statement:** Every cycle row in `pr-change-log.md` must include a `### Cycle-N code-reviewer` section that documents whether the Stage 12 / PI-019 reviewer-sub-agent convention was followed or deviated from. Acceptable values:
  - `Inline review deviation justification`: cycle deviated from the convention by skipping the reviewer-sub-agent and doing inline review instead. The section must list which of PI-023 criteria (a)-(d) apply and demonstrate inline round-4 (retroactive-correction accuracy) + round-5 (real-world fitness / false-positive simulation) verification.
  - `Reviewer-sub-agent run`: cycle followed the convention by running the reviewer-sub-agent. The section must reference the cycle-N-review-log.md and the rounds completed.

  Cycles that satisfy all of PI-023's inline-acceptable criteria (a) no new stages, (b) ≤1 new mechanical test, (c) mechanical substantive change (workflow-doc + ledger + cycle-row backfill only), and (d) inline round-4 + round-5 verification demonstrated in PR body, may skip the sub-agent and use the `Inline review deviation justification` phrase. Cycles that don't satisfy one or more criteria must run the sub-agent and use the `Reviewer-sub-agent run` phrase. The deviation is now reproducible rather than judgment-call.
- **Given** a cycle is being authored with a `### Cycle-N code-reviewer` section in `pr-change-log.md`
- **When** the cycle author writes the code-reviewer section
- **Then** the section must include either `Inline review deviation justification` (with PI-023 criteria (a)-(d) justification and round-4 + round-5 verification documentation) or `Reviewer-sub-agent run` (with cycle-N-review-log.md reference and rounds completed).
- **Expected behavior:** Future cycles' code-reviewer sections are unambiguous about whether the convention was followed or deviated from. The enforcing test (`tests/dreaming/test_pr_readiness.py::test_pr_change_log_includes_inline_review_deviation_justification_or_reviewer_subagent_run`) catches cycles that omit the code-reviewer section or use ambiguous phrasing.
- **Pass / fail criteria:**
  - **Pass** if the cycle row's `Code-reviewer` section includes one of the two phrases AND the inline-review-deviation section documents PI-023 criteria (a)-(d) + round-4 + round-5 verification (if deviation was used).
  - **Fail** if the code-reviewer section is missing, uses ambiguous phrasing, or uses inline-review-deviation without documenting criteria (a)-(d) + round-4 + round-5 verification.
- **Validation method:** `tests/dreaming/test_pr_readiness.py::test_pr_change_log_includes_inline_review_deviation_justification_or_reviewer_subagent_run` (cycle 14 NEW) enforces the code-reviewer section convention. PI-023 application also amends Stage 12 of `workflow-nightly-dreaming.md` with the inline-acceptable + reviewer-required criteria.
- **Owner:** human
- **Status:** applied (cycle 14, NEW; PI-023 applies-this-cycle)
- **Cycle:** 14
