# Evidence Index

Cycle: 2026-06-29
Review window: 2026-06-12 → 2026-06-20

Each entry is an evidence record. Every recommendation, lesson, pattern, scenario, and proposed improvement in other artifacts references one of the `EV-####` IDs below.

---

## EV-001 — Skill Governance Pipeline v1.0.0 ship

- **Run identifier:** sgp-v1.0.0-ship
- **Date:** 2026-06-14
- **Source files reviewed:**
  - `memory/2026-06-14.md` (lines 7–124, lines covering SGP v1.0.0 section)
  - Git commits: `01d1c34` (Merge PR #55 — sgp/v1-release), `82c514f` (#54), `5c821a2` (#56), `bb0f13d` (#57), `da6bfc8` (#58 — mypy-strict), `ac92032`
  - `skill-governance-pipeline/` (project tree, 75/75 unit tests)
- **Task type:** Major workflow ship (Python governance pipeline)
- **Outcome:** success
- **Workflows used:** in-session implementation; phases 1–5 tracked as `tasks/2026-06-13-sgp/`, `2026-06-13-sgp-p2/`, ... `2026-06-13-sgp-p5/`
- **Agents used:** main session (no sub-agents)
- **Skills used:** None explicitly; followed `skill-maturation` rules implicitly per memory
- **Files changed:** Created `skill-governance-pipeline/` with 17 modules, 75 tests, 8 CLI commands; mypy strict mode added in `a965c13`
- **Validation performed:** 75/75 unit tests; real-catalog E2E (126 artifacts); CI gating; mutation testing on `a965c13` → `efd083d` (261 survived 99.6% → progressively tightened)
- **User corrections:** None recorded; the 11 decisions (`D1`–`D11`) were recorded as the work proceeded
- **Git commits / diffs:**
  - `01d1c34` Merge pull request #55 from johrenberger/sgp/v1-release
  - `a965c13` chore(sgp): flip mypy to strict=true + add full type annotations
  - `efd083d` test(sgp): lock in mypy permissive state
  - `b5960b9` fix(sgp): dependency_analyzer filters 'unknown' artifacts
- **Summary:** A 39-minute, 5-phase implementation of a Click-based Python pipeline reached v1.0.0 across PRs #54–#58. The pipeline ships with 17 modules, 75 tests, 8 CLI commands, and runs end-to-end against a 126-artifact catalog with 133 blocking findings (expected — the catalog lacks metadata). After release, the team tightened mypy to strict (`a965c13`) and progressively eliminated the permissive allowances.
- **Linked lessons:** L-001, L-002
- **Linked regression scenarios:** RS-001, RS-002
- **Linked proposed improvements:** PI-001

---

## EV-002 — Task-state-management A2 exercise + Finding 1 fix

- **Run identifier:** tsm-a2-exercise-2026-06-12
- **Date:** 2026-06-12
- **Source files reviewed:**
  - `memory/2026-06-12.md` (full file, 1100 lines, sections 1–7)
  - Git commit: `300877f` on branch `fix/task-state-management-skip-to-closed`
  - `tasks/2026-06-12-task-state-management-exercise/` (3 sub-tasks: `tsm-s1-routine`, `tsm-s2-blocked`, `tsm-s3-false-blocker`)
- **Task type:** Skill validation exercise + bug-fix PR
- **Outcome:** partial success → success (after Finding 1 fix)
- **Workflows used:** in-session implementation; A2 validation exercise pattern
- **Agents used:** main session
- **Skills used:** `task-state-management` (the skill being validated), `handoff-packet`
- **Files changed:** `skills/task-state-management/SKILL.md` (table restructured, new "Skip-state rule"), `skills/task-state-management/scripts/transition.py` (new, 230 lines), `skills/task-state-management/scripts/lint-task-state.py` (new, 215 lines)
- **Validation performed:** 3 scenarios (routine, hard blocker, false blocker) under `tests/`; PR #17 open against `test-repo`
- **User corrections:** None recorded; 5 findings were self-identified during the exercise
- **Git commits / diffs:**
  - `300877f` (PR #17 open) `fix/task-state-management-skip-to-closed`
  - `291e8f9` (PR #16 merged) — `handoff-packet` promoted to `usable`
- **Summary:** An A2 validation exercise on `task-state-management` revealed a state-machine gap: no path from any post-`in_progress` state to `closed`. Fixed via a skip-state rule requiring `decisions/<id>.md`. A second DOTALL-regex bug was caught during this same exercise. A third finding (timestamp monotonicity) was partially fixed. Finding 4 (false-blocker decision record) was documented but not fixed in this PR. PR #17 carries the fix.
- **Linked lessons:** L-003, L-004
- **Linked regression scenarios:** RS-003, RS-004
- **Linked proposed improvements:** PI-002, PI-003

---

## EV-003 — BusinessOperationsDashboard slices 1 → 3.1

- **Run identifier:** bod-slices-1-to-3.1
- **Date:** 2026-06-20
- **Source files reviewed:**
  - `memory/2026-06-20.md` (full file, 168 lines)
  - Git commits: `44628bf` (slice 1), `0a4947f` (slice 2), `959ecb3` (slice 1+2 review fixes), `db4f15f` (slice 3), `dae7f51` (slice 3.1 review fixes), `eace226` (slice 4.1)
  - `BusinessOperationsDashboard/` subproject (74/74 BDD scenarios, 438/438 steps)
- **Task type:** Multi-slice feature implementation + repeated code-review sub-agent pattern
- **Outcome:** success (after 2 review-fix cycles)
- **Workflows used:** Sub-agent code-review loop (`sessions_spawn` with `mode=run`, `timeout=900s`); BDD-driven development with cucumber.cjs + per-scenario fresh SQLite
- **Agents used:** `code-review-bod-slice-2` (`session agent:main:subagent:735f98ae-8b39-48b2-a29a-c81da4717058`)
- **Skills used:** `code-review-slice-N` pattern (sub-agent workflow)
- **Files changed:** `BusinessOperationsDashboard/` — monorepo (pnpm, Fastify, Vite, Prisma), apps/api, apps/web, packages/shared, 9 new endpoints, 11 widgets, 4 new sync endpoints, schema additions
- **Validation performed:**
  - BDD: 15/15 (slice 1) → 34/34 (slice 2) → 43/43 (slice 3) → 74/74 (slice 4.1)
  - tsc clean on API and web builds
  - Live smoke test of `/connectors/:provider/sync` end-to-end (login → POST → poll → 202 → 200)
- **User corrections:** None recorded directly; reviewer-marked "Optional" items were explicitly skipped
- **Git commits / diffs:**
  - `44628bf` slice 1: monorepo scaffold + auth + RBAC + sales summary
  - `0a4947f` slice 2: 7 modules end-to-end
  - `959ecb3` code review: fix CRITICAL + HIGH findings from slice 1+2 review
  - `db4f15f` slice 3: background sync worker + operator-triggered syncs
  - `dae7f51` slice 3.1: address code review findings
  - `eace226` slice 4.1 (post-window, included for context)
- **Summary:** Five slices built a multi-tenant dashboard with auth, RBAC, 11 widgets, 9 endpoints, a background sync worker, and operator-triggered syncs. Two critical race conditions in slice 3 (wrong-SyncRun-update, hardcoded `dataType: 'unknown'`) and one HIGH multi-tenant info leak in `/health` were caught **only by the sub-agent code reviewer** — the BDD scenarios did not catch them. The slice 4.1 commit added two new BDD scenarios (dead-letter 409, double-click idempotency) specifically to prevent regression of these reviewer-only findings.
- **Linked lessons:** L-005, L-006
- **Linked regression scenarios:** RS-005, RS-006, RS-007
- **Linked proposed improvements:** PI-004, PI-005

---

## EV-004 — OpenClaw log evidence gap

- **Run identifier:** dreaming-cycle-1
- **Date:** 2026-06-29
- **Source files reviewed:** `find` across `/data/.openclaw/workspace` for OpenClaw run logs; `find` for handoff-packet files
- **Task type:** Evidence inventory for first dreaming cycle
- **Outcome:** finding (gap)
- **Summary:** No structured OpenClaw run logs and no saved handoff-packet files were discoverable in the workspace as of 2026-06-29. Dreaming Stage 1 could therefore only use Git history and `memory/*.md` notes as evidence. This gap is itself a candidate inefficiency pattern.
- **Linked lessons:** L-007
- **Linked regression scenarios:** RS-008
- **Linked proposed improvements:** PI-006

---

## EV-005 — Cron scheduling limitation (memory-tracked, not yet implemented)

- **Run identifier:** bod-slice-3-followup
- **Date:** 2026-06-20
- **Source files reviewed:** `memory/2026-06-20.md` ("Open items for slice 4+" section)
- **Task type:** Known limitation tracking
- **Outcome:** open
- **Summary:** Memory records "Cron schedules (currently interval-only)" and "`WORKER_MAX_ATTEMPTS` config (skipped from slice 3.1)" as known open items, not regression-tested.
- **Linked lessons:** L-008
- **Linked regression scenarios:** RS-009
- **Linked proposed improvements:** PI-007
