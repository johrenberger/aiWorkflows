# DREAMING.md

## Purpose

Define the standalone nightly dreaming workflow for OpenClaw / MiniMax execution-quality improvement.

This workflow reviews prior OpenClaw / MiniMax activity, extracts evidence-backed lessons, creates regression scenarios, updates scorecards, and produces one combined PR-ready change set.

It does not train the model.

It does not expose hidden chain-of-thought.

It does not automatically inject context into future MiniMax runs.

## When to Run

Run this workflow as an offline review cycle after meaningful OpenClaw / MiniMax activity, typically nightly.

It may also be run manually after:

- large workflow changes
- major skill additions
- repeated execution failures
- repeated user corrections
- significant Git churn in agent, skill, workflow, or validation files

## Inputs

Use all available observable sources:

- raw OpenClaw logs
- saved handoff packets
- Git history

Do not use hidden reasoning or private chain-of-thought as evidence.

For the first execution cycle (2026-06-29), the available evidence sources were:

- `memory/2026-06-12.md`, `memory/2026-06-13.md`, `memory/2026-06-14.md`, `memory/2026-06-20.md`
- Git history (188+ commits) filtered for workflow, skill, and CI changes
- `skill-governance-pipeline/` subproject artifacts and PRs
- `BusinessOperationsDashboard/` slice commit history

Structured OpenClaw run logs and saved handoff packets as discrete files were not available in the workspace at first run; this gap is tracked in `.openclaw/dreaming/inefficiency-patterns.md` (P-IP-001).

## Outputs

Generate or update under `.openclaw/dreaming/`:

- `README.md`
- `workflow-nightly-dreaming.md`
- `evidence-index.md`
- `nightly-summary.md`
- `lessons-learned.md`
- `failure-patterns.md`
- `success-patterns.md`
- `inefficiency-patterns.md`
- `skill-usage-scorecard.md`
- `workflow-scorecard.md`
- `regression-scenarios.md`
- `minimax-consumption-brief.md`
- `proposed-improvements.md`
- `validation-checklist.md`
- `pr-change-log.md`

## PR Behavior

Create one combined PR-ready branch:

`dreaming/nightly-execution-quality-YYYY-MM-DD`

The branch may contain multiple logical commits separating scaffolding, first-cycle artifacts, tests, and CI wiring, but they ship as one PR.

Each commit on the branch uses a `chore(dreaming):` prefix.

Do not split the nightly dreaming output into multiple PRs in this version.

## Change Safety Rules

Classify every change as one of the following.

### Auto-safe

May be applied directly:

- dreaming documentation
- evidence index updates
- scorecard updates
- regression scenario additions
- validation checklist additions
- report template updates
- non-runtime guidance clarifications

### Review-required

May be proposed but must not be silently applied:

- skill instruction changes
- workflow routing changes
- validation gate changes
- agent behavior changes
- skill merge/split proposals
- MiniMax consumption guidance that materially changes execution behavior

### Blocked

Must not be applied:

- deleting skills
- weakening validation
- weakening evidence requirements
- changing default model/tool behavior
- automatically injecting the MiniMax brief into future runs
- changing production execution behavior without validation

## MiniMax Consumption

MiniMax should treat `.openclaw/dreaming/minimax-consumption-brief.md` as an optional manual context pack.

Do not automatically inject this file into unrelated future runs.

The brief is **referenced by name** from this section. When the user asks about recurring execution patterns, repeated failures, skill routing, or workflow selection, MiniMax should read the brief **only after** being told it is relevant to the current request.

When explicitly provided as context, MiniMax should use the brief to improve:

- skill routing
- preflight checks
- validation discipline
- handoff quality
- regression awareness
- workflow selection

The brief is not auto-loaded, not present in default prompt context, and not included in agent spawn payloads.

## Relationship to Skill Governance Pipeline

This is a standalone workflow.

It is not a required stage of the Skill Governance Pipeline.

However, it may produce artifacts that the Skill Governance Pipeline can consume later, including:

- skill scorecards
- overlap findings
- deprecation watch items
- regression scenarios
- proposed skill improvements
- validation gaps

The Skill Governance Pipeline remains responsible for formal skill lifecycle decisions.

Nightly dreaming is responsible for evidence-backed execution review and PR-ready improvement proposals.

Both workflows write their own scorecards by design. SGP scorecards live in `skill-governance-pipeline/output/`; dreaming scorecards live in `.openclaw/dreaming/`. The dreaming scorecards intentionally use a different dimension set (see `workflow-nightly-dreaming.md` §Stage 5) so they remain additive rather than redundant.

## Validation Requirements

Before finalizing the PR-ready branch, validate that:

- all required artifacts exist
- every recommendation maps to evidence
- no hidden chain-of-thought is captured
- review-required changes are clearly separated
- blocked changes are not applied
- MiniMax brief exists but is not auto-injected
- regression scenarios include pass/fail criteria
- one combined PR branch is produced

Validation is enforced by `tests/dreaming/` and the `.github/workflows/nightly-dreaming-validation.yml` workflow.

## Final Output

Return only:

1. PR branch name
2. PR summary
3. Files changed
4. Evidence sources analyzed
5. Key findings
6. Scorecard highlights
7. Regression scenarios added
8. MiniMax brief location
9. Validation results
10. Review-required changes
11. Blocked changes
12. Recommended next MiniMax behavior
