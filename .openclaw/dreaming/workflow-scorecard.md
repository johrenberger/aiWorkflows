# Workflow Scorecard

Cycle: 2026-06-29

Same 1–5 dimensions and recommendation values as `skill-usage-scorecard.md`.

---

## Skill Governance Pipeline (SGP)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 5 | EV-001 — only activated when SGP commands are invoked |
| contribution_quality | 5 | EV-001 — 17 modules, 75/75 tests, real-catalog E2E (126 artifacts) |
| overlap_risk | 5 | EV-001 — no overlap with dreaming; boundary documented in `DREAMING.md` |
| validation_compatibility | 5 | EV-001 — CI mode; mutation testing added in `efd083d` |
| handoff_quality | 4 | EV-001 — produces `remediation_backlog.md`, executive/technical reports |
| recovery_contribution | 4 | EV-001 — rewrite proposals are human-reviewed, not auto-applied |
| deterministic_replacement_opportunity | 1 | EV-001 — the workflow IS the deterministic replacement for ad-hoc skill governance |
| minimax_usability | 5 | EV-001 — CLI is well-documented; MiniMax can invoke `skill-governance full` |

**Score clarification for `deterministic_replacement_opportunity`:** per `workflow-nightly-dreaming.md` §Stage 5, high score = low opportunity. Score 1 here means "this workflow is itself the deterministic replacement for the broader category of work."

- **Recommendation:** `keep`
- **Evidence below 3:** none
- **Observed impact:** n/a
- **Proposed remediation:** Continue tightening (mypy strict already applied; mutation progression in progress).

---

## A2 validation exercise (task-state-management)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-002 — activated for `tsm-a2-exercise-2026-06-12` |
| contribution_quality | 4 | EV-002 — caught 4 findings across 3 scenarios |
| overlap_risk | 4 | EV-002 — distinct from handoff-packet validation |
| validation_compatibility | 4 | EV-002 — 3 scenarios run; PR #17 carries the fix |
| handoff_quality | 4 | EV-002 — produces PR + commits + decisions/ |
| recovery_contribution | 4 | EV-002 — skip-state rule is a clean recovery path |
| deterministic_replacement_opportunity | 3 | EV-002 — partially scriptable (lint-task-state.py); spec is human/LLM |
| minimax_usability | 4 | EV-002 — MiniMax can run the exercise |

- **Recommendation:** `keep`
- **Evidence below 3:** none
- **Observed impact:** n/a
- **Proposed remediation:** none material.

---

## BDD-driven slice workflow (BusinessOperationsDashboard)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 5 | EV-003 — BDD runs on every slice commit |
| contribution_quality | 5 | EV-003 — 74/74 scenarios, ~4:35 runtime |
| overlap_risk | 5 | EV-003 — no overlap |
| validation_compatibility | 5 | EV-003 — composes with sub-agent review and tsc |
| handoff_quality | 4 | EV-003 — produces slice commits + slice.N.1 review commits |
| recovery_contribution | 4 | EV-003 — slice.N.1 cycle is the recovery path |
| deterministic_replacement_opportunity | 2 | EV-003 — BDD itself is a deterministic replacement; sub-agent review is not |
| minimax_usability | 4 | EV-003 — MiniMax can run `pnpm test:bdd` |

- **Recommendation:** `add_guardrail`
- **Evidence below 3:** deterministic_replacement_opportunity (2) — see clarification.
- **Observed impact:** The sub-agent review step is currently optional. Without it, concurrency bugs slip through.
- **Proposed remediation:** Add a guardrail: "Slice N is not shippable until sub-agent code review returns zero CRITICAL or HIGH findings." See PI-004.
- **Validation needed:** A test that asserts a slice with a known CRITICAL concurrency bug fails the ship gate.

---

## Dreaming workflow (this workflow)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-004 — first cycle activated correctly |
| contribution_quality | 4 | EV-004 — surfaced 4 patterns, 8 scenarios, 9 lessons |
| overlap_risk | 5 | EV-004 — boundary with SGP documented |
| validation_compatibility | 4 | EV-004 — 6 tests enforce schema |
| handoff_quality | 4 | EV-004 — structured artifacts + PR change log |
| recovery_contribution | 3 | EV-004 — surfaces gaps; does not close them |
| deterministic_replacement_opportunity | 2 | EV-004 — Stage-1 evidence collection could be scripted |
| minimax_usability | 4 | EV-004 — brief is referenced by name |

- **Recommendation:** `revise`
- **Evidence below 3:** deterministic_replacement_opportunity (2)
- **Observed impact:** First cycle is human-curated; subsequent cycles should run from a JSONL run log.
- **Proposed remediation:** see PI-006.
- **Validation needed:** see `skill-usage-scorecard.md` "dreaming" entry.
