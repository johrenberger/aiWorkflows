# Proposed Improvements

Cycle: 2026-06-29

Each improvement has an ID, evidence reference, observed problem, affected artifact, recommended change, expected benefit, risk level, safety classification, validation required, rollback notes, and status.

Safety classifications: `auto_safe | review_required | blocked`

---

## PI-001 — Add "permissive-state" pre-check to SGP CI

- **Improvement ID:** PI-001
- **Evidence reference:** EV-001, L-001
- **Observed problem:** SGP flipped mypy to strict after locking in permissive state, but the permissive-state test is project-specific. A future project repeating the same pattern may forget the lock-in step.
- **Affected workflow / skill / artifact:** SGP CI; generic validation-discipline documentation
- **Recommended change:** Add a CI check (or a documentation page in `DREAMING.md`) that asserts: any commit flipping a validation gate from permissive to strict must be preceded by a "lock in permissive state" commit on the same gate.
- **Expected benefit:** Prevents silent "we forgot to type module X" surprises on future gate flips.
- **Risk level:** low
- **Safety classification:** auto_safe
- **Validation required:** Manual review of `git log` for the next strict-flip attempt.
- **Rollback notes:** N/A (documentation / CI check only).
- **Status:** proposed

---

## PI-002 — Add state-machine transition-table requirement to `task-state-management` validator

- **Improvement ID:** PI-002
- **Evidence reference:** EV-002, L-003
- **Observed problem:** `task-state-management` SKILL.md had an incomplete transition table; the validator implemented what the table said; the gap was real.
- **Affected workflow / skill / artifact:** `task-state-management` validator (`lint-task-state.py`)
- **Recommended change:** Add a check that SKILL.md contains a complete transition table covering every `(from, to)` pair, or an explicit "no path" assertion.
- **Expected benefit:** Future state-machine gaps are caught at lint time, not in an exercise.
- **Risk level:** low
- **Safety classification:** review_required (touches a skill validator — material change)
- **Validation required:** A test that feeds an incomplete transition table and asserts the lint fails.
- **Rollback notes:** Disable the check in `transition.py` if false positives emerge.
- **Status:** proposed

---

## PI-003 — Add `re.DOTALL` denylist to skill validator CI

- **Improvement ID:** PI-003
- **Evidence reference:** EV-002, L-004
- **Observed problem:** `lint-task-state.py` used `re.DOTALL` to match across section boundaries, allowing placeholder text to satisfy the validator.
- **Affected workflow / skill / artifact:** Skill-validator CI under `skills/**/scripts/*.py`
- **Recommended change:** Add a CI check: `grep -rn "re.DOTALL" skills/**/scripts/ || true` must return empty. Fail CI if not empty.
- **Expected benefit:** Prevents reintroduction of the DOTALL anti-pattern.
- **Risk level:** low
- **Safety classification:** auto_safe
- **Validation required:** A test that introduces a `re.DOTALL` use in a fixture validator and asserts CI fails.
- **Rollback notes:** Remove the CI check if a legitimate `re.DOTALL` use is needed.
- **Status:** proposed

---

## PI-004 — Require sub-agent code review before slice ship

- **Improvement ID:** PI-004
- **Evidence reference:** EV-003, L-005
- **Observed problem:** Slice 3 shipped BDD-green; sub-agent review caught 2 CRITICAL race conditions. Without sub-agent review, the slice would have shipped with the races.
- **Affected workflow / skill / artifact:** `BusinessOperationsDashboard` slice workflow; `code-review-slice-N` sub-agent (emergent)
- **Recommended change:** Add a routing rule: "Slice N is not shippable until `code-review-slice-N` returns zero CRITICAL or HIGH findings." Document in a workflow doc (not enforced as CI initially; see PI-005 for full skill promotion).
- **Expected benefit:** Concurrency bugs caught before merge, not in `slice N.1`.
- **Risk level:** medium
- **Safety classification:** review_required (changes ship-gate behavior)
- **Validation required:** Run on the next 3 slices and compare findings to historical `slice N.1` commits.
- **Rollback notes:** Revert to BDD-only ship gate if sub-agent review becomes a bottleneck.
- **Status:** proposed

---

## PI-005 — Promote `code-review-slice-N` sub-agent pattern to a registered skill

- **Improvement ID:** PI-005
- **Evidence reference:** EV-003, L-005, P-S-001
- **Observed problem:** The sub-agent code-review pattern is documented in `memory/` and repeated across slices but is not a registered skill. MiniMax has no canonical trigger, output, or spawn payload for it.
- **Affected workflow / skill / artifact:** New skill registration; potential `code-review-slice-N/SKILL.md`
- **Recommended change:** Create `code-review-slice-N/SKILL.md` with explicit frontmatter, triggers ("after a feature slice ships BDD-green"), inputs (slice diff + commit range), outputs (categorized finding list with severity and evidence), and stop conditions ("BDD still green after fixes"). Standardize the `sessions_spawn` payload.
- **Expected benefit:** Future slices inherit the pattern without rediscovery.
- **Risk level:** medium
- **Safety classification:** review_required (skill registration changes routing behavior)
- **Validation required:** A smoke test that spawns the sub-agent against a known slice and asserts the response shape.
- **Rollback notes:** Delete the skill if it produces low-quality reviews.
- **Status:** proposed

---

## PI-006 — Add structured OpenClaw run log

- **Improvement ID:** PI-006
- **Evidence reference:** EV-004, L-007, P-IP-001
- **Observed problem:** Dreaming Stage 1 ran without structured run logs; coarse-grained findings.
- **Affected workflow / skill / artifact:** OpenClaw runtime logging; dreaming Stage 1 evidence collector
- **Recommended change:** Add a JSONL run log that records per-turn: start timestamp, completion timestamp, selected skills, tool errors, retries, and outcome. Add a deterministic parser to dreaming Stage 1 that consumes the log.
- **Expected benefit:** Subsequent dreaming cycles produce finer-grained patterns (per-tool-call retries, timeouts, blocked states).
- **Risk level:** medium
- **Safety classification:** review_required (touches OpenClaw runtime behavior)
- **Validation required:** Feed a fixture log to the parser and assert the parsed evidence index matches expectations.
- **Rollback notes:** Disable logging if it materially slows turns.
- **Status:** proposed

---

## PI-007 — Add regression test for cron tick path

- **Improvement ID:** PI-007
- **Evidence reference:** EV-005, L-008, RS-009
- **Observed problem:** "Cron schedules (currently interval-only)" and "`WORKER_MAX_ATTEMPTS` config" are tracked as open items but have no regression tests.
- **Affected workflow / skill / artifact:** `BusinessOperationsDashboard` scheduler; BDD test suite
- **Recommended change:** Add `tests/features/scheduler/cron-tick.feature` that asserts a deterministic side-effect on tick (e.g., `lastTickAt` updates, audit row written).
- **Expected benefit:** Future cron-related changes have a test scaffold to extend; the open item becomes a tracked test instead of a tracked limitation.
- **Risk level:** low
- **Safety classification:** auto_safe (test addition only)
- **Validation required:** Run the new BDD scenario; it should pass against current behavior.
- **Rollback notes:** Delete the test if scheduler refactor invalidates it.
- **Status:** proposed
