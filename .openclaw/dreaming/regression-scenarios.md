# Regression Scenarios

BDD-style Given/When/Then. Each scenario has a single evidence reference, severity, acceptance criteria, pass/fail criteria, validation method, and owner.

Severities: `blocker | warning | informational`
Owners: `MiniMax | deterministic_tool | human`

---

## RS-001 — SGP mypy permissive-to-strict progression

- **Evidence reference:** EV-001
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

- **Evidence reference:** EV-001
- **Affected workflow or skill:** SGP, any decision-making module
- **Severity:** blocker
- **Given** a module contains routing, scoring, classification, or recommendation logic
- **When** mutation testing is run against that module
- **Then** the survivor rate must be at or below the configured budget (default: ≤50% survivors)
- **Expected behavior:** CI fails when survivor rate exceeds budget.
- **Pass / fail criteria:** Pass if survivor rate ≤ budget. Fail otherwise.
- **Validation method:** mutation-testing CI job
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
