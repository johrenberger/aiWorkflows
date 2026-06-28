# MiniMax Consumption Brief

Cycle: 2026-06-29

This file is **not** loaded by default. It is referenced by name from `DREAMING.md`. MiniMax should read this file only when explicitly told it is relevant to the current request.

When read, use it to improve:

- skill routing
- preflight checks
- validation discipline
- handoff quality
- regression awareness
- workflow selection

---

## Active Routing Rules

- When a feature slice is "BDD green" and ready to ship, spawn `code-review-slice-N` as a sub-agent with `mode=run`, `timeout=900s`. Do not declare the slice done until the sub-agent review returns zero CRITICAL or HIGH findings.
- When a validation gate is about to flip from permissive to strict (mypy, lint, coverage, mutation budget), first write the "current permissive state" test, then add a progression script, then flip the gate.
- When validating any skill with a state machine, require a complete transition table in SKILL.md before trusting the validator script.
- When touching `finalize*`, `findFirst`, `findUnique`, or externalized state, route the work through the sub-agent code review path.

## Preferred Skills by Task Type

- **Multi-slice feature implementation with BDD:** `task-state-management` for task tracking, `handoff-packet` for decision records, `code-review-slice-N` (sub-agent) for review.
- **Skill or workflow validation exercise (A2-style):** `task-state-management` for the exercise harness; explicit linter script for the artifact under review.
- **Governance / decision code (routing, scoring, classification):** SGP (`skill-governance full`) for static review; mutation testing as a gate.
- **Execution-quality review (this workflow):** dreaming itself.

## Skills to Avoid Unless Triggered

- `task-state-management` — only for tasks that genuinely have a state-machine lifecycle. Do not activate for plain task lists.
- `handoff-packet` — only when a decision is being handed off between sessions. Do not activate for in-session notes.
- Dreaming's `minimax-consumption-brief.md` — only when explicitly relevant to the current request, never by default.

## Current Failure Patterns

- P-F-001: concurrency races in finalize/finalizeFailure (CRITICAL class, BDD does not catch).
- P-F-002: undocumented state-machine transitions in skill specs.
- P-F-003: DOTALL regexes that match across section boundaries.
- P-F-004: multi-tenant info leaks in `/health` and `/ready` endpoints.

## Required Preflight Checks

Before declaring a slice done:

1. BDD green.
2. Sub-agent code review returns zero CRITICAL or HIGH.
3. No `re.DOTALL` introduced in any validator under `skills/**/scripts/*.py`.
4. Any state-machine skill under review has a complete transition table in SKILL.md.

## Required Validation Gates

For any governance / decision code:

- Unit tests with branch coverage ≥ the project baseline.
- Mutation testing with survivor rate ≤ the configured budget (default: 50%).
- mypy strict (after the permissive-to-strict progression pattern is applied).

For any feature slice:

- BDD scenarios green.
- Sub-agent code review (see `code-review-slice-N`).
- `tsc` clean on API and web builds (for TS projects).

## Regression Scenarios to Respect

See `regression-scenarios.md`. Highlights:

- RS-005 — wrong-SyncRun update on finalizeFailure.
- RS-006 — `/health` multi-tenant info leak.
- RS-007 — double-click idempotency on `POST /connectors/:provider/sync`.

## Pending Review Changes

- PI-005: Promote `code-review-slice-N` sub-agent pattern to a registered skill.
- PI-007: Add regression test for cron tick path before closing `WORKER_MAX_ATTEMPTS` gap.

## Open Risks

- Dreaming Stage 1 evidence is currently Git + memory only; no structured OpenClaw run log exists. First-cycle patterns are real but coarse-grained. Subsequent cycles should consume a JSONL run log (PI-006).
- `memory_search` embedding provider quota is currently exhausted (as of 2026-06-29), so evidence retrieval relied on `grep` and `read`. Dreaming is not blocked but is more brittle than designed.
