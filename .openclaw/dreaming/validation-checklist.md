# Validation Checklist

Cycle: 2026-06-29 cycle-3
Branch: `dreaming/nightly-execution-quality-2026-06-29-cycle-2`

Run before finalizing the PR-ready branch. Each item must pass.

Cycle-2 deltas:
- "Makefile local validation" added (PI-008 applied)
- "CI-environment mismatch" added (P-F-005, RS-010, RS-011, RS-012)
- "Cycle-2 evidence expansion" — PR-review activity is now an evidence source

## Artifact existence

- [ ] `DREAMING.md` exists at repo root.
- [ ] `.openclaw/dreaming/README.md` exists.
- [ ] `.openclaw/dreaming/workflow-nightly-dreaming.md` exists.
- [ ] `.openclaw/dreaming/evidence-index.md` exists and is non-empty; includes EV-006+ for cycle 2 (cycle 1's EV-001..EV-005 may stay or be reframed).
- [ ] `.openclaw/dreaming/nightly-summary.md` exists.
- [ ] `.openclaw/dreaming/lessons-learned.md` exists; L-009+ for cycle 2.
- [ ] `.openclaw/dreaming/failure-patterns.md` exists; P-F-005 for cycle 2.
- [ ] `.openclaw/dreaming/success-patterns.md` exists; P-S-004 for cycle 2.
- [ ] `.openclaw/dreaming/inefficiency-patterns.md` exists; P-IP-003 for cycle 2.
- [ ] `.openclaw/dreaming/skill-usage-scorecard.md` exists.
- [ ] `.openclaw/dreaming/workflow-scorecard.md` exists.
- [ ] `.openclaw/dreaming/regression-scenarios.md` exists; RS-010, RS-011, RS-012 for cycle 2.
- [ ] `.openclaw/dreaming/minimax-consumption-brief.md` exists.
- [ ] `.openclaw/dreaming/proposed-improvements.md` exists; PI-008 status MUST be `applied` (or `proposed` if intentionally deferred) and not silently flipped.
- [ ] `.openclaw/dreaming/pr-change-log.md` exists.
- [ ] `Makefile` exists at repo root; `make dreaming-validate` returns green.
- [ ] `.openclaw/dreaming/validation-checklist.md` exists (this file).

## Evidence traceability

- [ ] Every recommendation in `proposed-improvements.md` references an `EV-####` ID.
- [ ] Every lesson in `lessons-learned.md` references an `EV-####` ID.
- [ ] Every pattern in `failure-patterns.md`, `success-patterns.md`, `inefficiency-patterns.md` references an `EV-####` ID.
- [ ] Every regression scenario in `regression-scenarios.md` references an `EV-####` ID.
- [ ] Every score below 3 in scorecards includes: evidence reference, observed impact, proposed remediation, validation needed.
- [ ] **(NEW in cycle 2)** Every EV entry should be reviewed against PI-010's invariant: "Is this a single event or an arc-tip?" If the latter, expand before publishing.

## No hidden reasoning capture

- [ ] No file under `.openclaw/dreaming/` (or in the Makefile) contains a section titled `## Reasoning`, `## Internal Analysis`, `## Hidden Thoughts`, `## Chain of Thought`, `## Private Reasoning`.
- [ ] No fenced code block has `reasoning` as its first line content.
- [ ] No file contains `<<<REASONING>>>` or similar envelopes.

## Scorecard schema

- [ ] `skill-usage-scorecard.md` covers all 8 dimensions per skill.
- [ ] `workflow-scorecard.md` covers all 8 dimensions per workflow.
- [ ] Each scorecard entry has a Recommendation value from the allowed set.
- [ ] Deprecation is never recommended from a single bad run.

## Regression scenario quality

- [ ] Every scenario has Given/When/Then structure.
- [ ] Every scenario has a severity from {blocker, warning, informational}.
- [ ] Every scenario has pass/fail criteria.
- [ ] Every scenario has an owner from {MiniMax, deterministic_tool, human}.

## PR readiness

- [ ] Branch named `dreaming/nightly-execution-quality-YYYY-MM-DD` with optional `-N` suffix.
- [ ] All commits on the branch use the `chore(dreaming):` prefix.
- [ ] `pr-change-log.md` exists and maps every change to evidence.
- [ ] Auto-safe and review-required changes are clearly separated in the change log.
- [ ] No blocked-class changes are applied.
- [ ] **(NEW in cycle 2)** Branch name suffix matches the cycle number being run.

## MiniMax brief non-injection

- [ ] `DREAMING.md` references the brief by name but does not auto-load it.
- [ ] No file under `.openclaw/dreaming/` or at the repo root configures the brief for automatic injection.
- [ ] No GitHub Actions workflow on this branch auto-loads the brief.
- [ ] `Makefile` does not configure the brief for automatic injection.

## **(NEW in cycle 2)** Local pre-push validation

- [ ] `make dreaming-validate` runs the same pytest suite as CI.
- [ ] `make dreaming-validate` exits 0 on a freshly-checked-out branch with no commits (L-013, RS-012).
- [ ] `make dreaming-validate` reports skipped, not failed, when the merge-base cannot be resolved and DREAMING_MERGE_BASE is unset.
- [ ] `make dreaming-resolve-base` falls through to `git merge-base` when `gh` is unavailable (RS-010).

## Single-PR check

- [ ] Only one PR branch exists for this cycle.
- [ ] No second `dreaming/nightly-execution-quality-*` branch exists for the same cycle.
