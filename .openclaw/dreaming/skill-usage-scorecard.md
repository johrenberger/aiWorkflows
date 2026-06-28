# Skill Usage Scorecard

Cycle: 2026-06-29

Scored 1–5 across:

- activation_precision — does the skill activate when it should and only then?
- contribution_quality — does the skill's output materially help the run?
- overlap_risk — does the skill's territory overlap another skill's?
- validation_compatibility — does the skill compose with BDD/mutation/mypy validation gates?
- handoff_quality — does the skill produce clean handoff artifacts (decisions/, evidence/)?
- recovery_contribution — does the skill help the run recover from failure?
- deterministic_replacement_opportunity — could a script replace most of this skill's value?
- minimax_usability — would a fresh MiniMax session benefit from this skill being loaded?

Recommendation values: `keep | revise | add_guardrail | merge | split | deprecation_watch | deprecation_review`

Deprecation rule: `deprecation_watch` after one materially poor pattern; `deprecation_review` only after repeated evidence across runs or Git history.

---

## task-state-management

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-002 — activated for the right task type (A2 validation exercise) |
| contribution_quality | 4 | EV-002 — caught 4 findings (state-machine gap, DOTALL bug, partial timestamp fix, false-blocker) |
| overlap_risk | 2 | EV-002 — overlaps with `handoff-packet` (both produce decision records) |
| validation_compatibility | 4 | EV-002 — 3 scenarios run; PR #17 carries the fix |
| handoff_quality | 3 | EV-002 — produced PR + commits; less good at capturing "why" in `decisions/` |
| recovery_contribution | 3 | EV-002 — recovery path is the skip-state rule; works but is a workaround |
| deterministic_replacement_opportunity | 3 | EV-002 — validator could be a script; spec still requires human-readable prose |
| minimax_usability | 4 | EV-002 — MiniMax can read SKILL.md and apply the transitions |

- **Recommendation:** `revise`
- **Evidence below 3:** overlap_risk (2) — see EV-002 §6; overlap with `handoff-packet` needs explicit boundary.
- **Observed impact:** Without a clear boundary, both skills risk producing duplicate decision records.
- **Proposed remediation:** Add a "Boundary with `handoff-packet`" subsection to `task-state-management/SKILL.md` clarifying which artifact owns what.
- **Validation needed:** A test that creates both artifacts for a single decision and asserts each contains distinct content.

---

## handoff-packet

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-002 — promoted to `usable` after PR #16 merge (`291e8f9`) |
| contribution_quality | 4 | EV-002 — used as decision-record carrier |
| overlap_risk | 2 | EV-002 — overlaps with `task-state-management` (see above) |
| validation_compatibility | 4 | EV-002 — cold-consumption test on `csv-stats-app` satisfies "Skill has been reviewed by a second agent or run on multiple repos" |
| handoff_quality | 5 | EV-002 — clean handoff artifact by design |
| recovery_contribution | 3 | EV-002 — not a recovery skill per se |
| deterministic_replacement_opportunity | 2 | EV-002 — template is structured but generation is human/LLM |
| minimax_usability | 5 | EV-002 — explicit "what to read next" path |

- **Recommendation:** `revise`
- **Evidence below 3:** overlap_risk (2), deterministic_replacement_opportunity (2)
- **Observed impact:** see `task-state-management` above.
- **Proposed remediation:** see `task-state-management`. Also: consider a deterministic validator for handoff-packet structure.
- **Validation needed:** A test that asserts the boundary.

---

## code-review-slice-N (emergent; not yet registered)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-003 — activated at the right moment (post-BDD-green) for slices 1+2, 3, 4 |
| contribution_quality | 5 | EV-003 — caught 2 CRITICAL + 4 HIGH + 5 MEDIUM + 3 LOW in slice 3 alone |
| overlap_risk | 4 | EV-003 — distinct from `code-review-slice-N` per slice |
| validation_compatibility | 5 | EV-003 — sub-agent is itself a validator; composed with BDD |
| handoff_quality | 4 | EV-003 — produces a structured finding list; sometimes writes `.reviews/slice-N-review.md` |
| recovery_contribution | 5 | EV-003 — explicitly the recovery path for slice N.1 |
| deterministic_replacement_opportunity | 1 | EV-003 — this is the kind of thing only a sub-agent can do well |
| deterministic_replacement_opportunity (corrected) | 5 | EV-003 — low opportunity (high score means "not replaceable by script") — see score clarification below |

**Score clarification:** `deterministic_replacement_opportunity` per `workflow-nightly-dreaming.md` §Stage 5: high score = low opportunity. Score 5 here means "this skill should not be replaced by a script."

| Dimension | Score | Evidence |
| --- | --- | --- |
| minimax_usability | 4 | EV-003 — MiniMax can spawn the same sub-agent pattern |

- **Recommendation:** `revise` (registered as skill; current state is emergent pattern in `memory/` only)
- **Evidence below 3:** none
- **Observed impact:** n/a (no score below 3)
- **Proposed remediation:** Promote to a registered skill with explicit frontmatter, triggers, and outputs. See PI-005.
- **Validation needed:** A smoke test that spawns the sub-agent against a known slice and asserts the response shape.

---

## dreaming (this workflow)

| Dimension | Score | Evidence |
| --- | --- | --- |
| activation_precision | 4 | EV-004 — activated correctly for first cycle; ran on intended window |
| contribution_quality | 4 | EV-004 — produced 8 regression scenarios + 9 lessons + 4 patterns from 3 runs |
| overlap_risk | 5 | EV-004 — intentionally separate from SGP scorecards |
| validation_compatibility | 4 | EV-004 — 6 tests under `tests/dreaming/` enforce schema |
| handoff_quality | 4 | EV-004 — produces structured artifacts + PR change log |
| recovery_contribution | 3 | EV-004 — not a recovery workflow; surfaces gaps for follow-up |
| deterministic_replacement_opportunity | 2 | EV-004 — most of the workflow is structured and could be partially scripted |
| minimax_usability | 4 | EV-004 — MiniMax brief is referenced by name from DREAMING.md |

- **Recommendation:** `revise` (after first cycle)
- **Evidence below 3:** deterministic_replacement_opportunity (2)
- **Observed impact:** Without a deterministic Stage-1 evidence collector, the cycle depends on human curation of Git/memory inputs.
- **Proposed remediation:** Build a JSONL parser for the future OpenClaw run log (see PI-006).
- **Validation needed:** A test that feeds a fixture run log and asserts the parsed evidence index matches expectations.
