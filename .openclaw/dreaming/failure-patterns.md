# Failure Patterns

Each pattern has a single evidence reference. Severity comes from observed impact in the review window; recurrence classification follows `workflow-nightly-dreaming.md` §Stage 4.

---

## P-F-001 — Concurrency race conditions not caught by BDD

- **Pattern ID:** P-F-001
- **Evidence reference:** EV-003 (CRITICAL #1 in slice 3.1 review)
- **Affected workflow / skill:** any feature touching `finalize*` / `findFirst` / `findUnique` paths; observed in `BusinessOperationsDashboard` sync runner
- **Observed failure:** `findFirst({status:'failure'})` returned the wrong SyncRun under concurrent finalize. BDD scenarios had 43/43 green; sub-agent review caught the race.
- **Recurrence:** one_off (this cycle), but matches a known class; candidate_regression
- **Impact:** CRITICAL — silent data integrity corruption (wrong SyncRun updated)
- **Prevention strategy:** Always run a sub-agent code review on finalize/finalizeFailure paths before declaring a slice done. Add at least one concurrency BDD scenario per finalize path.
- **Regression scenario link:** RS-005

---

## P-F-002 — Undocumented state-machine transitions in skill specs

- **Pattern ID:** P-F-002
- **Evidence reference:** EV-002 (Finding 1)
- **Affected workflow / skill:** `task-state-management`
- **Observed failure:** Allowed-transitions table listed no forward path to `closed` from any post-`in_progress` state. The transition.py validator implemented what the table said.
- **Recurrence:** one_off, but generic to any skill with a state machine; candidate_regression
- **Impact:** warning — feature works after fix; pre-fix, tasks could not close via the forward path
- **Prevention strategy:** SKILL.md must include a complete transition table or an explicit "no path" assertion for every (from, to) pair.
- **Regression scenario link:** RS-003

---

## P-F-003 — DOTALL regex matching across section boundaries

- **Pattern ID:** P-F-003
- **Evidence reference:** EV-002 (Finding 2)
- **Affected workflow / skill:** `task-state-management/scripts/lint-task-state.py`
- **Observed failure:** `re.DOTALL` regex matched content from `## Notes` into `## Resolution`, allowing placeholder text to satisfy the validator.
- **Recurrence:** one_off; candidate_regression
- **Impact:** warning — validator passed without the artifact being valid
- **Prevention strategy:** Prefer line-by-line scanners with explicit section detection over `re.DOTALL` for structured-document validators.
- **Regression scenario link:** RS-004

---

## P-F-004 — Multi-tenant info leak in `/health` endpoint

- **Pattern ID:** P-F-004
- **Evidence reference:** EV-003 (HIGH #3 in slice 3.1 review)
- **Affected workflow / skill:** `BusinessOperationsDashboard` worker `/health`
- **Observed failure:** `/health` returned a `tenants` count derived from per-tenant rows on a `0.0.0.0`-bound service.
- **Recurrence:** one_off; systemic in pattern (any management endpoint on multi-tenant code); candidate_regression
- **Impact:** HIGH — information disclosure to unauthenticated callers
- **Prevention strategy:** Strict `/health` and `/ready` contracts: no tenant-derived fields, no row counts. Probe only `SELECT 1` (or equivalent).
- **Regression scenario link:** RS-006
