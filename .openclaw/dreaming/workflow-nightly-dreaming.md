# workflow-nightly-dreaming

Standalone offline workflow that reviews prior OpenClaw / MiniMax activity, extracts evidence-backed execution lessons, creates regression scenarios, updates scorecards, and produces one combined PR-ready change set.

## Inputs

Observable evidence only:

- Raw OpenClaw logs (PI-006)
- Saved handoff packets
- Git history
- **(Cycle 2)** PR-review activity (`gh pr list --state all --json ...`, `gh pr view <N>`) — single-event evidence can hide arc-scale patterns; PR traces un-collapse them

Hidden chain-of-thought is **never** evidence.

## Outputs

All outputs under `.openclaw/dreaming/` plus the root-level `DREAMING.md` entry point.

## Stage 0: Local pre-push validation (PI-008, cycle 2)

Before opening or pushing the PR-ready branch, run `make dreaming-validate` from the repo root. The target mirrors the CI workflow's `pytest tests/dreaming/` step and the marker-scan / merge-base steps, locally. PRs that fail locally should not be pushed.

This step is the durable fix for the cycle-1 fix-up loop (5 of 9 commits were CI-only corrections).

## Stage -1: Workspace state pre-check (PI-012, cycle 4)

Before starting a dreaming cycle, verify the local workspace is in a known clean shape relative to this workflow:

- **Prior-cycle dreaming branches:** deleted locally and remotely.
  - `git branch --list 'dreaming/nightly-execution-quality-*'` should show only the new cycle's branch.
  - Delete with `git push origin --delete dreaming/nightly-execution-quality-<prior-date>[-<suffix>]` and `git branch -D <local>`.
  - **Why:** `test_only_one_dreaming_branch_exists` is a PR-readiness invariant; lingering branches have caused local-validation noise in cycle 3 (RS-014).
- **Local main fast-forwarded:** `git fetch origin main && git merge --ff-only origin/main` so that merge-base refs resolve cleanly. Cycle 1's fragile local merge-base was a recurring fix-up source.
- **`git status` on main is clean** (or only contains the deliberately-untracked paths documented in `README.md` / `DREAMING.md`).
- **`DREAMING.md` and `MEMORY.md` policies reviewed** for any new constraints since the prior cycle.

This step is a checklist, not automation. Its purpose is to make CI failures from state, not from policy, visible at human time, not at push time.

## CI Trigger Model

The dreaming validation suite is a **PR-readiness suite**. Its CI configuration must reflect this:

- `on: pull_request:` with appropriate `paths:` filter — primary trigger (PR-side context is where the suite's invariants apply).
- `on: push: branches:` — restricted to the branches that own the PRs (`dreaming/nightly-execution-quality-*`), so pre-PR pushes get an early-warning run. **Do not include `main`**; the base branch is the union of every prior cycle's diffs, not the natural site for PR-readiness checks.
- The suite tests themselves should skip gracefully when their precondition does not hold (current branch == main, HEAD == merge-base, etc.). Defense in depth: the workflow trigger is the primary guard; the test skips are a backstop against ad-hoc triggers.

This model was learned in cycle 3 (L-014), after the prior cycle's merge to `main` triggered a CI run that failed on PR-readiness assertions. The bundle of `main` into the `push:` block was the latent bug for two cycles before it was caught.

### Stage 1: Collect Evidence

For each candidate run, gather observable artifacts:

- task start / completion events
- selected workflows, agents, skills
- tool usage and validation commands
- errors, retries, blocked states, completion status
- Git commits, diffs, branch names, reverted changes
- handoff packet contents if present

### Stage 2: Build Evidence Index

Write `.openclaw/dreaming/evidence-index.md`. Each entry:

- `EV-####` ID
- run identifier / timestamp
- source files reviewed
- task type
- outcome
- workflows / agents / skills used
- files changed
- validation performed
- user corrections if any
- associated Git commits
- summary
- linked lessons, regression scenarios, proposed improvements

### Stage 3: Classify Each Run

Per-run classification across:

- outcome: success | partial | failed | blocked | abandoned
- efficiency: efficient | acceptable | inefficient | excessive
- skill routing: correct | partially correct | unnecessary | missing | overlapping
- validation: strong | acceptable | weak | missing
- recovery: not_needed | successful | partial | failed
- deterministic tooling: none | script | ci | static | structured_parse
- governance impact: none | lesson_only | regression_needed | prompt_change | skill_change | workflow_change | validation_change

### Stage 4: Cross-Run Patterns

Look for repeated failures, repeated successes worth preserving, inefficient successes, missing/unnecessary/overlapping skills, weak handoffs, validation gaps, unclear workflow boundaries, repeated user corrections, high-churn files, repeated prompt edits with unclear benefit, PRs without enough validation, deterministic-tool opportunities.

Classify each pattern: `one_off | repeated | systemic | candidate_regression | candidate_workflow | candidate_skill_governance`.

### Stage 5: Update Scorecards

Score skills and workflows 1–5 across:

- activation precision
- contribution quality
- overlap risk
- validation compatibility
- handoff quality
- recovery contribution
- deterministic replacement opportunity
- MiniMax usability

Recommendation values: `keep | revise | add_guardrail | merge | split | deprecation_watch | deprecation_review`.

Scores below 3 require evidence reference, observed impact, proposed remediation, validation needed.

Deprecation rule: one bad run → `deprecation_watch`. Repeated evidence across runs or Git history → `deprecation_review`. Never recommend deprecation from a single bad run.

### Stage 6: MiniMax Consumption Brief

Compact, structured, operational. No narrative, no hidden reasoning, no vague lessons.

Required sections:

- Active routing rules
- Preferred skills by task type
- Skills to avoid unless triggered
- Current failure patterns
- Required preflight checks
- Required validation gates
- Regression scenarios to respect
- Pending review changes
- Open risks

Manual-injection only. Not loaded by default, not present in agent spawn payloads.

### Stage 7: Regression Scenarios

BDD-style Given/When/Then. Each scenario:

- title
- evidence reference
- affected workflow or skill
- severity: blocker | warning | informational
- acceptance criteria
- expected behavior
- pass / fail criteria
- validation method
- owner: MiniMax | deterministic_tool | human

### Stage 8: One Combined PR-Ready Change Set

Branch: `dreaming/nightly-execution-quality-YYYY-MM-DD`.

Logical commits allowed on the branch, one PR.

Commit message prefix: `chore(dreaming):`.

### Stage 9: Classify Change Safety

Per change: `auto_safe | review_required | blocked`.

### Stage 10: Add Validation

Add `.github/workflows/nightly-dreaming-validation.yml` and `tests/dreaming/` test files enforcing:

- artifact existence
- evidence traceability
- no hidden reasoning capture
- scorecard schema
- regression scenario quality
- PR readiness
- blocked-change detection
- review-required separation
- MiniMax brief non-injection
- single-PR check

## Hard Constraints

- No hidden chain-of-thought capture.
- No automatic MiniMax brief injection.
- No skill deletion.
- No weakening of validation or evidence requirements.
- No default model/tool behavior changes.
- No high-risk production behavior changes without explicit validation.
- No splitting nightly dreaming into multiple PRs.
- No deprecation recommendations from a single bad run.
- Every recommendation traces to evidence.
