# MiniMax Consumption Brief

Cycle: 2026-06-29 cycle-5

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
- When a validation gate is about to flip from permissive to strict (mypy, lint, coverage, mutation budget), first write the "current permissive state" test, then add a progression script, then flip the gate. **(NEW in cycle 2)** This pattern was applied three times in the SGP arc (mypy strict, branch coverage gate, mutation testing gate); treat it as canonical.
- **(NEW in cycle 2)** When introducing a new CI gate to an existing workflow, ship the gate as a **separate commit on a separate PR**, ordered by feedback cost (cheap → moderate → expensive). Each gate is additive and independent.
- When validating any skill with a state machine, require a complete transition table in SKILL.md before trusting the validator script.
- When touching `finalize*`, `findFirst`, `findUnique`, or externalized state, route the work through the sub-agent code review path.

## Preferred Skills by Task Type

- **Multi-slice feature implementation with BDD:** `task-state-management` for task tracking, `handoff-packet` for decision records, `code-review-slice-N` (sub-agent) for review.
- **Skill or workflow validation exercise (A2-style):** `task-state-management` for the exercise harness; explicit linter script for the artifact under review.
- **Governance / decision code (routing, scoring, classification):** SGP (`skill-governance full`) for static review; mutation testing as a gate; a **gate-stack** (cycle 2 widens this from "mutation alone") including unit + branch coverage + mutation + mypy strict + ruff + ≥1 property-based test for invariants.
- **Execution-quality review (this workflow):** dreaming itself.
- **(NEW in cycle 2) Pre-push local validation:** `make <workflow>-validate` — runs the same pytest suite as CI, locally, before push. Use this prior to every push that touches any artifact set under CI validation.

## Skills to Avoid Unless Triggered

- `task-state-management` — only for tasks with a state-machine lifecycle.
- `handoff-packet` — only when handing off a decision between sessions.
- Dreaming's `minimax-consumption-brief.md` — only when explicitly relevant, never by default.

## Current Failure Patterns

- **P-F-001**: concurrency races in finalize/finalizeFailure (BDD does not catch).
- **P-F-002**: undocumented state-machine transitions in skill specs.
- **P-F-003**: DOTALL regexes that match across section boundaries.
- **P-F-004**: multi-tenant info leaks in `/health` and `/ready`.
- **(NEW in cycle 2) P-F-005**: CI-environment mismatch causing false-positive test failures (detached HEAD without `main` ref; marker-scan greps matching rule-documenting files; "ensure X is not configured" greps matching docs that say "do not configure X").

## Required Preflight Checks

Before declaring a slice done:

1. BDD green.
2. Sub-agent code review returns zero CRITICAL or HIGH.
3. No `re.DOTALL` introduced in any validator under `skills/**/scripts/*.py`.
4. Any state-machine skill under review has a complete transition table in SKILL.md.
5. **(NEW in cycle 2)** `make <workflow>-validate` (or equivalent local pre-push validation) returns green.

## Required Validation Gates

For any governance / decision code:

- Unit tests with branch coverage ≥ the project baseline.
- Mutation testing with survivor rate ≤ the configured budget (default: 50%).
- mypy strict (after the permissive-to-strict progression pattern is applied).
- **(NEW in cycle 2)** At least one property-based test (Hypothesis or equivalent) for invariant properties.

For any feature slice:

- BDD scenarios green.
- Sub-agent code review.
- `tsc` clean on API and web builds (for TS projects).

## Regression Scenarios to Respect

See `regression-scenarios.md`. Highlights:

- RS-002 — SGP gate-stack requirement (cycle 2 widens from "mutation alone").
- RS-005 — wrong-SyncRun update on finalizeFailure.
- RS-006 — `/health` multi-tenant info leak.
- RS-007 — double-click idempotency.
- **(NEW in cycle 2)** RS-010 — Makefile local-validation prereq degradation.
- **(NEW in cycle 2)** RS-011 — branch-name regex accepts cycle suffix.
- **(NEW in cycle 2)** RS-012 — commit-prefix test skips on empty range.

## Pending Review Changes

- PI-002: state-machine transition-table check.
- PI-004: sub-agent review as slice ship gate.
- PI-005: register `code-review-slice-N` as a skill.
- PI-006: add structured OpenClaw run log (cycle 2: still proposed, still the largest unfilled gap).
- **(NEW in cycle 2)** PI-009: generalize the Makefile pre-push validation pattern (PI-008) to other workflow artifact sets.

## Open Risks

- **(Carried)** Dreaming Stage 1 evidence is currently Git + memory + PRs only; no structured OpenClaw run log exists. First-cycle findings are coarse; subsequent cycles should consume a JSONL run log (PI-006).
- **(Carried)** `memory_search` embedding provider quota was exhausted during cycle 1. Working with `read` + `grep` is brittle vs. semantic search. **Cycle 2 status:** no change to provider state; cycle 2 also ran on `read` + `grep`.
- **(NEW in cycle 2)** The cycle-2 evidence base was extended with PR-review activity, which surfaced that cycle-1's EV-001 was a coarse snapshot of a 16-PR arc. Future cycles should expect that *every* cycle-1 entry is a candidate for arc expansion.
