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

### Stage 0a: Capture collect-only baseline at forecast-time (PI-020, cycle 12)

When writing the cycle row in `pr-change-log.md` (Stage -2 forward-looking schema), the cycle author must also capture the precise baseline. This is the symmetry partner of Stage 11's verification step (PI-018 / PI-020).

#### Required step

1. Run the collect-only baseline capture:

   ```
   python3 -m pytest tests/dreaming/ --collect-only -q 2>&1 | grep "tests collected"
   ```

2. Quote the captured count in the cycle row as a `Collected-test baseline (forecast): <N> tests collected` line (or a heading + bullet equivalent matching the `test_pr_change_log_includes_collect_only_forecast_baseline` regex). The captured count is the **precise forecast**, not a reasoned estimate.
3. Optionally include the parametrized-test-expansion delta explicitly (e.g., "cycle 12 adds 1 new file to `.openclaw/dreaming/` which adds 3 parametrized tests, so the collect-only baseline of 132 should match the post-merge count of 135").

#### Constraints

- The baseline must be captured via `python3 -m pytest tests/dreaming/ --collect-only -q` (or equivalent). Reasoned estimates from `def test_` count are NOT acceptable; they are exactly what PI-020 was filed to prevent.
- The line must include a numeric count in `<digit> tests collected` shape. Placeholders (`TBD`, `XXX`, `to be determined`) and narrative mentions without a number are NOT acceptable.
- Stage 0a is forward-looking: it requires the **most recent cycle's** row in `pr-change-log.md` to have the captured baseline. Past cycles' rows are preserved as historical record and are not retroactively restructured.

#### Validation required

Enforced by `tests/dreaming/test_pr_readiness.py::test_pr_change_log_includes_collect_only_forecast_baseline` (cycle 12 NEW). The test scans the most recent cycle section in `pr-change-log.md` and asserts a `Collected-test baseline (forecast): <digit> tests collected` line is present in one of three forms (heading + body, bullet, or plain line). Placeholder baselines (`TBD`, `to be determined`) and narrative mentions do NOT satisfy the test. See the test docstring for the regex shape and three failure modes.

#### Forecast format: explicit `collected → passed` arithmetic (PI-021 amendment, cycle 13)

The cycle row's `Main post-merge (forecast)` line must use one of three explicit formats:

- **Format A (preferred):** `Main post-merge (forecast): N collected → (N-2) passed + 1 skipped + 1 expected-fail-on-main`. The explicit `collected → passed` arithmetic is shown inline. Example: `Main post-merge (forecast): 136 collected → 134 passed + 1 skipped + 1 expected-fail-on-main`.
- **Format B (legacy-compatible):** `Main post-merge (forecast): N passed + 1 skipped + 1 expected-fail-on-main` paired with a separate `Collected-test baseline (forecast): N tests collected` line in the same cycle row. The arithmetic `N collected → (N-2) passed + 1 + 1` must be derivable from the separate baseline line.
- **Format C (collected-only):** `Main post-merge (forecast): N collected` with no `passed` count in the forecast. The post-merge verification (Stage 11) computes the actual `passed` count from the actual collect-only baseline.

The forecast's numeric value must be unambiguously labeled as either `collected` or `passed`. Mixing the two without explicit arithmetic (e.g., `136 passed` where `136` is actually a collected count) is a forecast-format labeling bug — the cycle-12 row had this bug and produced a −2 delta against the actual post-PR-#72 count (see EV-023 and `memory/2026-07-07-cycle-12-final-closeout.md`). PI-021 (cycle 13 NEW) enforces the label convention via `test_pr_change_log_forecast_uses_explicit_collected_or_passed_label`.

#### Forecast merge-state clarification (PI-022 amendment, cycle 13)

The cycle row's `Main post-merge (forecast)` line must also explicitly state the **assumed merge state** — i.e., which reviewer-driven additions are assumed to be in the merge. Acceptable values:

- `substantive-commit-only`: PR is merged at the cycle's substantive commit (no reviewer-driven additions in merge). Forecast arithmetic: `branch-local collect-only baseline − 1 (skipped) − 1 (expected-fail-on-main) = passed`.
- `with-reviewer-driven-additions`: PR is merged with all reviewer-driven additions (5 rounds per Stage 12). Forecast arithmetic: `branch-local collect-only baseline + (3 × reviewer-added-files) − 1 (skipped) − 1 (expected-fail-on-main) = passed`.
- `mixed`: PR is merged at a specific round (e.g., "merged at Round 3 fix-up state, no Rounds 4-5 additions"). Forecast arithmetic: explicit count of which reviewer rounds are in-merge, parametrized-expansion delta computed accordingly.

The cycle-12 row implicitly assumed `with-reviewer-driven-additions` but the actual PR #71 merge was `mixed` (Round 3 fix-up state only, no Rounds 4-5), producing a −4 delta against the actual count (see cycle-12 closeout memo). PI-022 enforces the merge-state-clarification convention going forward; this is documentation-only and is not enforced by a dedicated test (cycle 13 carry-forward; may be promoted to a tested PI in a future cycle if the merge-state assumption becomes a recurring source of forecast failures).

#### Why this stage exists (PI-020 amendment, cycle 12; PI-021 + PI-022 amendments, cycle 13)

Cycle 11's forecast missed by +3 because the forecast reasoned from `def test_` count but did not account for `@pytest.mark.parametrize` driven by `_all_dreaming_files()` in `tests/dreaming/test_no_hidden_reasoning_capture.py`. The post-merge verification step (PI-018 / Stage 11) caught the +3 correctly, but the forecast itself was a reasoned estimate. Stage 0a makes the forecast a captured number. PI-020 is the symmetry partner of PI-018: pre-merge baseline-capture (Stage 0a) + post-merge verification (Stage 11).

Cycle 12's forecast was numerically correct as a **collected** count but was labeled as **passed** in the cycle row (Format B without an explicit `collected → passed` arithmetic), producing a −2 delta against the actual post-PR-#72 count (EV-023). Cycle 12's forecast also implicitly assumed `with-reviewer-driven-additions` merge state but the actual PR #71 merge was `mixed` (Round 3 only), producing a −4 delta against the actual PR #71 count. PI-021 + PI-022 strengthen the forecast-discipline (PI-016 / PI-018 / PI-020) by requiring explicit `collected → passed` arithmetic (PI-021) and explicit merge-state assumption (PI-022) in the cycle row's `Main post-merge (forecast)` line.

## Stage -3: Post-amend verify (PI-017, cycle 10)

Before switching branches to start a new cycle (Stage -2) or to perform a merge closeout (`git checkout main`), the cycle author must verify the working tree is clean relative to the most recent commit. This applies after any commit, but is especially important after `git commit --amend`, which can leave the working tree's tracked files in a state that disagrees with HEAD.

Required step:

1. Run `git status --short` (scoped to the cycle working area; the enforcing test scopes to `.openclaw/dreaming/`):
   ```bash
   git status --short -- .openclaw/dreaming/
   ```
2. If any tracked file shows as `M ` (modified, staged) or ` M` (modified, unstaged), the amend (or recent commit) produced a state mismatch between the working tree and the commit. This is a footgun: a subsequent `git checkout` will fail with "Please commit your changes or stash them before you switch branches." Either `git add <file>` (if the working-tree content should be the new HEAD) or `git checkout -- <file>` (if the working tree should match HEAD).

Constraints:

- The check is scoped to `.openclaw/dreaming/` because that is the cycle's working area. Other directories (e.g., `workflows/`) may have intentionally-uncommitted local edits that are out of cycle scope and are not in scope for this stage.
- For cycles without an amend, Stage -3 is a no-op: `git status --short` returns empty or only `??` (untracked) lines, and the discipline is satisfied by virtue of having committed cleanly.

Why this stage exists (cycle 10 retrofitted justification): cycles 8 and 9 closeouts both hit this pattern. The cycle-8 closeout memo (`memory/2026-07-01-cycle-8-closeout.md`) disclosed it as "a real workflow-disclosure, not a process failure." The cycle-9 closeout memo (`memory/2026-07-01-cycle-9-closeout.md`) flagged it as "two-cycle-stale, not a one-off." Stage -3 codifies the discipline so cycle 11+ doesn't reproduce the pattern. Stage numbering is integers (the dream workflow does not use fractional stages); Stage -3 sits before Stage -2 because "amend hygiene" applies to the cycle author's own workflow between cycles, before any new cycle's pre-declaration begins.

Validation: enforced by `tests/dreaming/test_pr_readiness.py::test_no_post_amend_working_tree_drift` (cycle 10). The test runs `git status --short -- .openclaw/dreaming/` and asserts no lines indicate a modified, added, deleted, or renamed tracked file (untracked `??` lines are excluded). When `git status` reports any such drift, the test fails with an actionable message naming the offending file(s).

## Stage -2: Surface-Scope Pre-Declaration (PI-015, cycle 8)

Before Stage -1 (workspace pre-check), the cycle author declares the cycle's surface scope. This is a 4-line declaration at the top of the cycle's `nightly-summary.md` Trigger section.

Required fields (all four must appear, case-insensitive, in the Trigger section of the cycle author writes):

- **Workflow target** — which workflow is being evolved. Default: `dream` (the current cycle's own workflow).
- **Surface area** — `in-repo` | `out-of-repo` | `cross-repo`. `cross-repo` requires a `cross-repo-handoff-index.md` entry (cycle-6 pattern, H-001).
- **Dreaming-ledger scope** — `in-ledger` | `non-dreaming`. `non-dreaming` requires an explicit rationale (cycle-7 pattern, PI-014).
- **Cycle-size budget** — `1` | `2` | `3` commits (planned; reconciled at close).

Constraints:

- Out-of-repo work requires a handoff-index entry before the cycle ships.
- Non-dreaming-ledger work requires the rationale to cite either the surfacing-cycle (e.g., "surfaced by dream-workflow because cron is gateway-local") or a precedent (e.g., "follows PI-014 pattern").
- Cycle-size budget `>= 3` requires a substantive-work justification (e.g., "3 commits because one each for spec, code, and tests").

Why this stage exists (cycle 8 retrofitted justification): cycles 5, 6, and 7 each added a self-meta paragraph at close-out explaining what the cycle's scope had been. Cycle 5 was "biggest since cycle 1." Cycle 6 was "substantive-by-handoff." Cycle 7 was "first cycle with out-of-scope work." Pre-declaration forces the author to confront "is this in-scope?" at human time, not at audit time. The honest constraint "I cannot do that from this repo" becomes a structural artifact (handoff-index entry) rather than a self-meta justification.

Validation: enforced by `tests/dreaming/test_pr_readiness.py::test_declares_surface_scope_in_trigger` (cycle 8). The test reads the cycle author's Trigger section and asserts all four field labels appear. The test is forward-looking: it requires the **most recent cycle's** Trigger section to have the new format. Past cycles' Trigger sections are not retroactively restructured; their format is preserved as historical record.

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

## Stage 11: Closeout memo convention (PI-016, cycle 9; PI-018 amendment, cycle 11)

After the PR merges, the cycle author writes a closeout memo to `memory/YYYY-MM-DD-cycle-N-closeout.md` (or `memory/YYYY-MM-DD-cycle-N-final.md` for the cycle-closeout variant). The closeout memo must quote validator output **twice with explicit branch context**:

1. **Branch-local count** — `make dreaming-validate` on the cycle's branch (the commit that was merged). Quoted as "Branch-local — `make dreaming-validate` on `<branch-name>` (commit `<sha>`):" followed by the actual `make` output.
2. **`main` post-merge count** — `make dreaming-validate` on `main` after the merge. Quoted as "`main` post-merge — `make dreaming-validate` on `main` after PR #N merge (`<sha>`):" followed by the actual `make` output.

### Required step

1. After PR #N merges, `git checkout main && git pull origin main`.
2. Run `make dreaming-validate` on `main`. Capture the actual output.
3. Write the closeout memo with both counts (branch-local and `main` post-merge) and the actual output for each, **with explicit branch context in the header for each count** (e.g., "Branch-local — on `dreaming/...cycle-N` (commit `<sha>`):").
4. Compare the actual `main` post-merge count to the forecast the cycle author wrote in `pr-change-log.md` (the cycle row contains a "main post-merge forecast" line per PI-016).
5. If the forecast matched: leave the closeout memo as-is, document the match in a "Forecast check" section ("matched the forecast").
6. If the forecast did NOT match: correct the closeout memo with the actual measured count, document the delta in a "Forecast check" section explaining the off-by-N, and add an EV to `evidence-index.md` documenting the discipline failure.

### Constraints

- Both counts must be the actual `make` output, not a derived estimate. The convention is "quote validator output twice," not "compute validator output twice."
- The branch-local count must come from the cycle's branch (HEAD before merge), not from `main` post-merge.
- The `main` post-merge count must come from `main` post-merge, not from the cycle's branch.
- The cycle author's forecast (in `pr-change-log.md`) must be a forecast written BEFORE the merge, based on the cycle's diff. It is verified AFTER the merge by comparing to the actual `main` post-merge count.
- If the forecast did not match, the closeout memo must explicitly document the delta and the reason. "Silent" corrections are not allowed.

### Validation required

- `make dreaming-validate` includes `test_pr_change_log_forecasts_main_post_merge_count` (cycle 11 NEW), which asserts that the most recent committed cycle row in `pr-change-log.md` contains a `main post-merge (forecast)` line that includes a numeric count of tests in `<digit> passed` shape (e.g., `127 passed + 1 skipped + 1 expected-fail-on-main`). The test catches three failure modes: (a) missing forecast line entirely, (b) forecast present as a placeholder (`TBD`, `XXX`, `to be determined`), (c) narrative mention only (`PI-016 established the convention of forecasting main post-merge counts`) without an explicit forecast line. Placeholder forecasts and narrative mentions are NOT sufficient; the test requires an actual count.
- The cycle author must manually verify the forecast matched the actual `main` post-merge count. This verification step is NOT automated; it is a discipline enforced by the cycle author's own diligence. The test enforces forecast PRESENCE AND SHAPE; the forecast's CORRECTNESS is verified separately per Stage 11 step 6.

### Why this stage exists (PI-018 amendment, cycle 11)

PI-016 (cycle 9) was adopted as a procedural convention. Cycle 10's merge closeout initially reported that PI-016's forecast-discipline had failed for every cycle since adoption (cycles 6-10). **Cycle 11's PI-018 retroactive correction re-measured each prior cycle's actual count properly (by `git checkout <sha>` to clean working tree before running `make dreaming-validate`) and found the situation is more nuanced:** PI-016's forecast-discipline had **partial failures**. Cycles 6 and 10 miscounted (cycle 6 over-claimed by 2 in passed-count and missed the 1 skipped + 1 expected-fail-on-main; cycle 10 under-counted by 1). Cycles 7-9 happened to reason correctly and matched the actual `main` post-merge counts. The root cause for the failures: forecasters (cycle authors) reasoned from the branch-local count but did not account for on-`main` differences (e.g., the empty-range commits-prefix test skip rule fires on `main` but not on a fresh branch; the expected-fail-on-main `test_current_branch_uses_dreaming_prefix` only fires on `main`). PI-018 (cycle 11 NEW) amends PI-016 with this explicit verification step (run `make dreaming-validate` on the actual post-merge `main`, compare to the forecast, correct the closeout memo if they don't match) to make the convention a real verification method, not just a documentation discipline. See EV-020 for the cross-cycle actual-vs-claimed measurements.

## Stage 12: Code-reviewer sub-agent convention (PI-019, cycle 11)

The dreaming-workflow spawns a code-reviewer sub-agent for each substantive cycle. The sub-agent runs **5 rounds of review**, with **per-round summaries** dropped back to the parent session after each round (Telegram msg #11644 directive). The 5-round budget was chosen arbitrarily (msg #11770) and is not load-bearing as a count; what matters is the round PURPOSES.

### Required step

For each substantive cycle (one that adds a new test, stage, PI, RS, or EV — not a bookkeeping-only cycle), spawn a code-reviewer sub-agent after the substantive commit is on the branch and before opening the PR. The sub-agent reviews the diff between the cycle branch and `main`, applies fix-up commits to the branch as findings warrant, and pushes after each fix-up. Per-round summary via `sessions_send` after each round.

### Inline-review deviation criteria (PI-023 amendment, cycle 14)

The Stage 12 reviewer-sub-agent convention is the default for substantive cycles. Cycles **may** skip the reviewer-sub-agent and do inline review instead IF AND ONLY IF **all** of the following criteria are satisfied:

- **(a) No new stages.** The cycle amends existing stages only (e.g., adding sub-sections to Stage 0a) and does not introduce new top-level `## Stage N:` headings.
- **(b) ≤1 new test (mechanical).** The cycle adds at most one new test, and the test follows an established convention (e.g., a new test that asserts the same kind of property as an existing test in the same module). Cycles that add ≥2 new tests OR any test that introduces a new convention (e.g., a new drift-check pattern, a new bullet-regex widening, a new parametrized-expansion formula) MUST run the reviewer-sub-agent.
- **(c) Mechanical substantive change.** The cycle's substantive change is workflow-doc amendment + ledger entries (PI / RS / EV additions) + cycle-row backfill, with no new methodology, no new code paths, and no modification to existing tests that other cycles depend on (e.g., `test_pr_change_log_includes_collect_only_forecast_baseline` is shared infrastructure).
- **(d) Inline round-4 + round-5 verification demonstrated in PR body.** The cycle author's PR body includes an explicit "Inline review deviation justification" section that demonstrates:
  - **Round 4 (retroactive-correction accuracy):** any retroactive corrections to prior cycles' artifacts (closeout memos, PI bodies, EV entries, cycle rows) are verified numerically and textually consistent with the underlying data. If no retroactive corrections, the section notes this.
  - **Round 5 (real-world fitness / false-positive simulation):** the author has empirically simulated failure modes — e.g., temporarily broke the cycle's forecast / test input and verified the new test correctly FAILED, then restored. The simulation steps and results are documented in the PR body.

If any of (a)–(d) are not satisfied, the cycle MUST run the reviewer-sub-agent per the standard Stage 12 protocol.

### Reviewer-sub-agent is REQUIRED if any of:

- The cycle adds a new stage to `workflow-nightly-dreaming.md`.
- The cycle adds ≥2 new tests OR any test that introduces a new convention (drift-check pattern, bullet-regex widening, parametrized-expansion formula).
- The cycle modifies an existing test that other cycles depend on (e.g., `test_pr_change_log_includes_collect_only_forecast_baseline`, `test_pr_change_log_forecasts_main_post_merge_count`, `test_pr_change_log_forecast_uses_explicit_collected_or_passed_label`).
- The cycle introduces a new PI that affects forward-looking forecasts (e.g., PI-016, PI-018, PI-020, PI-021, PI-022).
- The cycle touches ≥3 cycles' retroactive corrections.
- The cycle introduces a new Stage that affects Stage 0a / Stage 11 / Stage 12 conventions (e.g., Stage -3 in cycle 10, the cycle-11 Stage 11 PI-018 amendment).

The key invariant: **inline review is acceptable for mechanical / single-cycle-scope changes; the reviewer-sub-agent is required for methodological / multi-cycle-scope / new-convention changes.**

### Round purposes (locked in by msg #11772)

- **Round 1 (flex).** Default: schema/format compliance of any new stage or test added by the cycle. Override for cycles that don't add schema-level changes.
- **Round 2 (flex).** Default: test quality / tightness if a test was added; PI body quality if a PI was added; docstring clarity if doc-heavy change.
- **Round 3 (flex).** Default: cross-artifact consistency check. Does the change reconcile with adjacent artifacts, or does it introduce contradictions with prior cycle's claims?
- **Round 4 (fixed).** **Retroactive-correction accuracy / cross-cycle bookkeeping verification.** If the cycle made retroactive corrections to prior cycles' artifacts (e.g., closeout memos, PI bodies, EV entries), verify the corrections are numerically and textually consistent with the underlying data. Cross-check by `git checkout <sha>` (clean working tree) and `make dreaming-validate` where the corrections touch validator counts. If no retroactive corrections, fall back to: verify the cycle's own claims are internally consistent.
- **Round 5 (fixed).** **Real-world fitness / false-positive simulation.** Empirically simulate failure modes: would the new test catch a placeholder / TBD / narrative-only input? Would the new stage's instructions work for a future cycle author who hasn't read this cycle's memory files? Run the simulations, not just read the code.

### Constraints

- The reviewer sub-agent runs in a clean context (no memory of why the cycle author wrote the code). This distance is the point.
- The reviewer MUST NOT modify scope. Only quality fixes.
- The reviewer MUST NOT rebase or rewrite the cycle's substantive commit. Append fix-up commits on top.
- All reviewer commits must pass `make dreaming-validate` before push.
- Per-round summaries are mandatory, not optional. They give the user real-time visibility mid-flight.
- **Second-pass discipline (load-bearing, msg #11772).** If any round claims a code change was applied (regex updated, test tightened, etc.), a subsequent round or a second pass MUST verify by reading the actual code on disk, not just the commit message. The cycle-11 reviewer caught a round-5 false-positive this way (commit `6c4f8ef`).

### Validation required

- The reviewer log lives at `.openclaw/dreaming/cycle-N-review-log.md` and is committed to the cycle's PR.
- The log must enumerate the rounds completed, fix-up commits applied, no-issue rounds, and the final recommendation (merge as-is or wait).
- The user merges when satisfied with the reviewer's recommendation. The reviewer does NOT auto-merge.

### Why this stage exists (PI-019 amendment, cycle 11; PI-023 amendment, cycle 14)

Cycles 10 and 11 both used a code-reviewer sub-agent. Cycle 10 caught 4 latent issues across 5 rounds (1 substantive + 4 reviewer-driven = 5 commits; cycle-size budget was 2 but reviewer-driven commits doubled it). Cycle 11 caught 6 latent issues across 5 rounds + a second-pass catch (1 substantive + 7 reviewer-driven = 8 commits; cycle-size budget was 2 but reviewer-driven commits quadrupled it). The most important findings (cycle 10: Stage -3 schema alignment; cycle 11: regex false-positive on placeholder inputs) were issues the cycle author would not have caught without a clean-context second pair of eyes. Locking in the convention as a workflow stage (Stage 12) makes it discoverable for future cycles and codifies which rounds are fixed-purposes vs flex-purposes (msg #11772).

**PI-023 (cycle 14 NEW, APPLIED) amendment:** Cycle 13 deliberately deviated from the Stage 12 reviewer-sub-agent convention by skipping the sub-agent and doing inline review instead. The deviation worked (cycle-13 had Δ = 0 perfect forecast match), but it was a one-off judgment call, not a codified rule. PI-023 codifies when inline-review is acceptable (criteria (a)–(d) above) vs when the reviewer-sub-agent is required (the bulleted list above). The convention is enforced by `tests/dreaming/test_pr_readiness.py::test_pr_change_log_includes_inline_review_deviation_justification_or_reviewer_subagent_run` (NEW, cycle 14), which scans the most recent cycle row's "Code-reviewer" section for one of the two phrases: `Inline review deviation justification` (if the sub-agent was skipped) or `Reviewer-sub-agent run` (if the sub-agent was run). Cycles that satisfy all of (a)–(d) skip the sub-agent and document inline review; cycles that don't satisfy one or more criteria run the sub-agent. The deviation is now reproducible rather than judgment-call.

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
