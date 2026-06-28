# Validation Checklist

Cycle: 2026-06-29
Branch: `dreaming/nightly-execution-quality-2026-06-29`

Run before finalizing the PR-ready branch. Each item must pass.

## Artifact existence

- [ ] `DREAMING.md` exists at repo root.
- [ ] `.openclaw/dreaming/README.md` exists.
- [ ] `.openclaw/dreaming/workflow-nightly-dreaming.md` exists.
- [ ] `.openclaw/dreaming/evidence-index.md` exists and is non-empty.
- [ ] `.openclaw/dreaming/nightly-summary.md` exists.
- [ ] `.openclaw/dreaming/lessons-learned.md` exists.
- [ ] `.openclaw/dreaming/failure-patterns.md` exists.
- [ ] `.openclaw/dreaming/success-patterns.md` exists.
- [ ] `.openclaw/dreaming/inefficiency-patterns.md` exists.
- [ ] `.openclaw/dreaming/skill-usage-scorecard.md` exists.
- [ ] `.openclaw/dreaming/workflow-scorecard.md` exists.
- [ ] `.openclaw/dreaming/regression-scenarios.md` exists.
- [ ] `.openclaw/dreaming/minimax-consumption-brief.md` exists.
- [ ] `.openclaw/dreaming/proposed-improvements.md` exists.
- [ ] `.openclaw/dreaming/pr-change-log.md` exists.

## Evidence traceability

- [ ] Every recommendation in `proposed-improvements.md` references an `EV-####` ID.
- [ ] Every lesson in `lessons-learned.md` references an `EV-####` ID.
- [ ] Every pattern in `failure-patterns.md`, `success-patterns.md`, `inefficiency-patterns.md` references an `EV-####` ID.
- [ ] Every regression scenario in `regression-scenarios.md` references an `EV-####` ID.
- [ ] Every score below 3 in scorecards includes: evidence reference, observed impact, proposed remediation, validation needed.

## No hidden reasoning capture

- [ ] No file under `.openclaw/dreaming/` contains a section titled `## Reasoning`, `## Internal Analysis`, `## Hidden Thoughts`, `## Chain of Thought`, or `## Private Reasoning`.
- [ ] No fenced code block has `reasoning` as its first line content.
- [ ] No file contains `<<<REASONING>>>` or similar envelopes.

## Scorecard schema

- [ ] `skill-usage-scorecard.md` covers all 8 dimensions per skill: activation_precision, contribution_quality, overlap_risk, validation_compatibility, handoff_quality, recovery_contribution, deterministic_replacement_opportunity, minimax_usability.
- [ ] `workflow-scorecard.md` covers all 8 dimensions per workflow.
- [ ] Each scorecard entry has a Recommendation value from the allowed set.
- [ ] Deprecation is never recommended from a single bad run.

## Regression scenario quality

- [ ] Every scenario has Given/When/Then structure.
- [ ] Every scenario has a severity from {blocker, warning, informational}.
- [ ] Every scenario has pass/fail criteria.
- [ ] Every scenario has an owner from {MiniMax, deterministic_tool, human}.

## PR readiness

- [ ] One branch named `dreaming/nightly-execution-quality-YYYY-MM-DD`.
- [ ] All commits on the branch use the `chore(dreaming):` prefix.
- [ ] `pr-change-log.md` exists and maps every change to evidence.
- [ ] Auto-safe and review-required changes are clearly separated in the change log.
- [ ] No blocked-class changes are applied.

## MiniMax brief non-injection

- [ ] `DREAMING.md` references the brief by name but does not auto-load it.
- [ ] No file under `.openclaw/dreaming/` or at the repo root configures the brief for automatic injection.
- [ ] No GitHub Actions workflow on this branch auto-loads the brief.

## Single-PR check

- [ ] Only one PR branch exists for this cycle.
- [ ] No second `dreaming/nightly-execution-quality-*` branch exists.
