# Lessons Learned

Compact, evidence-backed. No vague lessons. Each lesson has a single evidence reference.

---

## L-001 — Lock permissive state in tests before flipping to strict

- **Evidence:** EV-001, commit `efd083d` ("lock in mypy permissive state + script to track strict progression") and `a965c13` ("chore(sgp): flip mypy to strict=true + add full type annotations")
- **Observed behavior:** SGP shipped v1.0.0 with mypy in permissive mode. The permissive state was captured as a test (asserting the exact set of untyped modules), then a script tracked the progression, and only then was strict mode flipped. This avoided any "we forgot to type module X" surprise.
- **Interpretation:** When tightening validation, capture the prior lenient state as an explicit test before flipping the gate. Otherwise the gate flip appears to silently break things.
- **Future execution guidance:** Any time a "permissive → strict" transition is contemplated, first write the "current permissive state" test, then add a progression script, then flip the gate.
- **Affected workflow / skill:** SGP, generic validation-discipline pattern
- **Regression scenario link:** RS-001

---

## L-002 — Mutation testing surfaces real coverage gaps the unit tests miss

- **Evidence:** EV-001, memory/2026-06-14.md line "261 survived (99.6%), 0 killed, 1 timeout"
- **Observed behavior:** After SGP v1.0 shipped, mutation testing on the codebase produced 261 survivors / 0 killed on first run. Unit-test coverage had been reported as high; mutation testing exposed that the tests passed without meaningfully exercising production branches.
- **Interpretation:** Line/branch coverage is necessary but not sufficient evidence of test quality. Mutation testing is the appropriate additional gate for code that makes routing or governance decisions.
- **Future execution guidance:** Apply mutation testing to any module that makes decisions (router, classifier, scorer, recommender). Treat >50% survivors as a CI blocker for decision code.
- **Affected workflow / skill:** SGP, generic validation discipline
- **Regression scenario link:** RS-002

---

## L-003 — Document the full state machine before any validator lands

- **Evidence:** EV-002, Finding 1 ("state machine had no path to `closed` from any post-`in_progress` state")
- **Observed behavior:** `task-state-management` SKILL.md's "Allowed transitions" table listed transitions but had no forward path from `testing_done` to `closed`. The transition.py validator implemented what the table said; the gap was real, not a tooling bug.
- **Interpretation:** Spec gaps become validator bugs. A spec gap caught by an exercise is cheaper than the same gap caught in production.
- **Future execution guidance:** For any skill with a state machine, the SKILL.md must include a complete transition table or an explicit "no path" assertion for every (from, to) pair.
- **Affected workflow / skill:** `task-state-management`
- **Regression scenario link:** RS-003

---

## L-004 — DOTALL regexes match across section boundaries; use line-by-line scanners

- **Evidence:** EV-002, Finding 2 ("DOTALL regex bug... allowed leaving `blocked` without a real Resolution note")
- **Observed behavior:** The original `find_blocker_with_resolution` used a `re.DOTALL` regex that matched content from a `## Notes` section into a `## Resolution` section, allowing the placeholder text "(filled in when status moves to `resolved`)" to satisfy the validator.
- **Interpretation:** A regex that crosses structural boundaries will eventually match content that shouldn't satisfy the rule. A line-by-line scanner with explicit section detection is harder to fool.
- **Future execution guidance:** Prefer line-by-line scanners over `re.DOTALL` for any validator that consumes a structured document. Where regex is unavoidable, anchor matches to the section being validated.
- **Affected workflow / skill:** `task-state-management`, generic validator discipline
- **Regression scenario link:** RS-004

---

## L-005 — Sub-agent reviewers catch concurrency bugs BDD does not

- **Evidence:** EV-003, CRITICAL #1 in slice 3.1 review ("runner updated the wrong SyncRun on finalizeFailure")
- **Observed behavior:** Slice 3 had 43/43 BDD scenarios green. The sub-agent code reviewer flagged two CRITICAL and four HIGH findings — including a race in the runner's `findFirst({status:'failure'})` that BDD had not exercised. The slice 3.1 commit then added a BDD scenario for double-click idempotency that **specifically prevents regression** of the reviewer-only finding.
- **Interpretation:** BDD is necessary but not sufficient for concurrency-heavy code. A code-review sub-agent is a structurally different validator that catches classes of bugs (races, info leaks, hardcoded values) that BDD typically misses.
- **Future execution guidance:** For any feature touching `finalize*`, `findFirst`, `findUnique`, or externalized state, run a sub-agent code review **before** declaring the slice done. Treat CRITICAL/HIGH findings as blocking.
- **Affected workflow / skill:** `code-review-slice-N` (emergent), `BusinessOperationsDashboard`
- **Regression scenario link:** RS-005, RS-007

---

## L-006 — Multi-tenant `/health` and `/ready` endpoints must not leak tenant-derived data

- **Evidence:** EV-003, HIGH #3 in slice 3.1 review ("worker `/health` exposed `tenants` count (multi-tenant info leak on 0.0.0.0)")
- **Observed behavior:** The worker `/health` endpoint reported a `tenants` count that was derived from per-tenant rows. On a `0.0.0.0`-bound service, that count is observable to anyone who can hit the port.
- **Interpretation:** Health and readiness endpoints are typically bound on the management network — but "typically" is the failure mode. The endpoint contract should be reviewed with "what would a non-authenticated caller see?" as the question.
- **Future execution guidance:** Define a strict shape for `/health` and `/ready`: no tenant-derived fields, no row counts, no last-sync timestamps that could correlate to a tenant. Probe only `SELECT 1` (or equivalent).
- **Affected workflow / skill:** `BusinessOperationsDashboard`, generic API-design discipline
- **Regression scenario link:** RS-006

---

## L-007 — Dreaming requires structured run logs to do its full job

- **Evidence:** EV-004
- **Observed behavior:** This first cycle could only use Git history and `memory/*.md` notes. Per-tool-call retries, timeouts, blocked states, and selected skills at the run level were not directly observable. The patterns surfaced are real but coarse-grained.
- **Interpretation:** Dreaming's evidence rules intentionally exclude hidden chain-of-thought — but they also require observable run logs. The two constraints together imply a logging discipline, not just a dreaming discipline.
- **Future execution guidance:** Add a structured OpenClaw run log that records (at minimum) start, completion, selected skills, tool errors, retries, and outcome for each turn. Treat this log as the primary Stage-1 evidence source.
- **Affected workflow / skill:** dreaming workflow itself
- **Regression scenario link:** RS-008

---

## L-008 — Tracked-but-untested limitations become untested assumptions

- **Evidence:** EV-005
- **Observed behavior:** `memory/2026-06-20.md` lists "Cron schedules (currently interval-only)" and "`WORKER_MAX_ATTEMPTS` config (skipped from slice 3.1)" as known open items. Neither has a regression test exercising the limitation. The next slice that touches these areas will discover the gap as a bug, not as a tracked TODO.
- **Interpretation:** "Known limitation" tracking without a regression test is a half-measure. The test is what makes the limitation knowable at the right moment.
- **Future execution guidance:** For each tracked limitation, add at least one regression test that documents the current behavior. When the limitation is fixed, the test becomes the acceptance criterion.
- **Affected workflow / skill:** `BusinessOperationsDashboard`, generic task-hygiene discipline
- **Regression scenario link:** RS-009
