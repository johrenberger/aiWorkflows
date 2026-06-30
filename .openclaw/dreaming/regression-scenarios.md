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
