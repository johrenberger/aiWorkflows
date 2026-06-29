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
