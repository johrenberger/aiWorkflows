# Nightly Summary

- **Cycle:** 2026-07-02 cycle-12
- **Branch:** `dreaming/nightly-execution-quality-2026-07-02-cycle-12`
- **Date:** 2026-07-02

## Trigger

### Surface-Scope Pre-Declaration (Stage -2, PI-015, cycle 8)

- **Workflow target:** dream (in-repo dreaming-workflow, .openclaw/dreaming/ + tests/dreaming/).
- **Surface area:** `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage 0a added as a new section under Stage 0 for the collect-only forecast step), `tests/dreaming/test_pr_readiness.py` (new test enforcing the collect-only baseline in pr-change-log.md), `.openclaw/dreaming/proposed-improvements.md` (PI-020 added), `.openclaw/dreaming/regression-scenarios.md` (RS-022 added), `.openclaw/dreaming/evidence-index.md` (EV-022 added), `.openclaw/dreaming/pr-change-log.md` (cycle-12 row with collect-only baseline).
- **Dreaming-ledger scope:** PI-020 NEW (forecast methodology refinement — collect-only baseline + symmetry with PI-018 verification step). RS-022 NEW (forecast must include a collect-only baseline that the post-merge verification can compare against). EV-022 NEW (cross-cycle forecast-vs-actual delta history, including cycle-11's +3 finding).
- **Cycle-size budget:** 2 commits (1 substantive + 1 reviewer-driven if needed). The collect-only step is a small workflow-doc amendment + one new test; no retroactive corrections are required because the parametrized-test-expansion finding is forward-looking only.

### Cycle-12 reason for change (PI-020 / cycle-12 trigger)

PI-018 (cycle 11 NEW, APPLIED) established the post-merge verification step: after the cycle's PR merges, run `make dreaming-validate` on actual `main` and compare to the cycle author's forecast. Cycle 11's forecast missed by +3 because the forecast reasoned from `def test_` count but did not account for `@pytest.mark.parametrize` driven by `_all_dreaming_files()` in `tests/dreaming/test_no_hidden_reasoning_capture.py`. Cycle 11 added 1 NEW file to `.openclaw/dreaming/` (`cycle-11-review-log.md`, committed by reviewer) and modified 2 existing files (`workflow-nightly-dreaming.md` adding Stage 11 + Stage 12, `proposed-improvements.md` adding PI-018 + PI-019). Only the 1 NEW file was newly enumerated by `_all_dreaming_files()` and contributed +3 parametrized test invocations (3 parametrized tests × 1 newly-enumerated file); the 2 modified files were already present pre-cycle-11 and did not add new parametrized test invocations.

PI-020 strengthens the forecast-discipline by adding a **pre-merge verification step** that captures the precise baseline at forecast-time. Specifically: when the cycle author writes the cycle row in `pr-change-log.md`, they must also run `python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"` and quote the collected-test count as the forecast baseline. This gives a precise forecast (rather than a reasoned estimate), making the post-merge verification step (PI-018) more deterministic. PI-020 is the symmetry partner of PI-018: pre-merge baseline + post-merge verification.

_(Retroactive correction, cycle 12 review round 4: earlier wording in this file and in `pr-change-log.md`, `evidence-index.md`, `proposed-improvements.md`, and the cycle-11 closeout memo incorrectly stated "Cycle 11 added 3 new files to `.openclaw/dreaming/`". The cycle-11 merge stat shows 1 NEW file (`cycle-11-review-log.md`) and 2 modifications (`workflow-nightly-dreaming.md`, `proposed-improvements.md`). Only the 1 NEW file was newly enumerated by `_all_dreaming_files()` and contributed to the +3 parametrized test invocations. The 2 modified files were already present pre-cycle-11 and did not add new parametrized test invocations.)_

### Cycle-12 expected impact

- The forecast-baseline becomes a captured number, not a reasoned estimate. Future cycles' forecasts will reflect parametrized-test expansions.
- The post-merge verification step (PI-018) compares the actual collected count to the captured baseline, surfacing drift caused by out-of-band test additions (e.g., reviewer-driven parametrization changes).
- The cycle-12 forecast-discipline test asserts the cycle row's `Collected-test baseline (forecast)` line is present with a numeric count.

### Cycle-12 validation performed (planned)

- `python3 -m pytest tests/dreaming/ --collect-only -q | grep "tests collected"` to capture the precise baseline before opening PR.
- `make dreaming-validate` on the cycle-12 branch — expected to match the collect-only baseline.
- The new test `test_pr_change_log_includes_collect_only_forecast_baseline` enforces the discipline going forward.

### Cycle-12 artifacts changed (planned)

- `.openclaw/dreaming/workflow-nightly-dreaming.md` — Stage 0 amended with collect-only forecast step (~10 lines).
- `tests/dreaming/test_pr_readiness.py` — `test_pr_change_log_includes_collect_only_forecast_baseline` added (NEW, ~30 lines).
- `.openclaw/dreaming/regression-scenarios.md` — RS-022 added (NEW).
- `.openclaw/dreaming/evidence-index.md` — EV-022 added (NEW).
- `.openclaw/dreaming/proposed-improvements.md` — PI-020 added (NEW, auto_safe).
- `.openclaw/dreaming/pr-change-log.md` — cycle-12 row appended with `Collected-test baseline (forecast)` line.
- `.openclaw/dreaming/nightly-summary.md` — cycle-12 body prepended (this section); cycle-11 body preserved below.

### What's still open on `main` after cycle 11 (cycle-12 carry-forward)

- **PI-006a** — runtime JSONL emitter; out-of-repo; principal outstanding PI per the user's original framing in #11557. Still blocked on runtime side.
- **PI-014** — `cyber-signal-fetch-feeds.sh` missing; fix is on the same gateway, outside the workflow's surface area.
- **PI-009** — held since cycle 2 per "A then B"; PI-008 APPLIED for many cycles now; hold may be obsolete. Cycle 13 candidate if not addressed in cycle 12.
- **PI-018** — applied; verification step working correctly (caught cycle-11 forecast miss).
- **PI-019** — applied; code-reviewer sub-agent convention codified as Stage 12.
- **PI-020** — NEW this cycle, applied-this-cycle.

## Cycle-11 body (carried forward, unchanged)

## Trigger

### Surface-Scope Pre-Declaration (Stage -2, PI-015, cycle 8)

- **Workflow target:** dream (`.openclaw/dreaming/`)
- **Surface area:** in-repo
- **Dreaming-ledger scope:** in-ledger
- **Cycle-size budget:** 2 (planned; PI-018 application is the substantive commit; reviewer-driven fixes may add 1 commit)

### Trigger narrative

Cycle 11 was triggered by user request "Candidate 1" (Telegram msg #11687, 2026-07-01 01:54 GMT+2). The "1" refers to the cycle-11 candidate list presented in the cycle-10 merge closeout (`memory/2026-07-01-cycle-10-closeout.md`); candidate 1 was PI-018 application (strengthen PI-016 forecast-discipline with post-merge verification; retroactively correct cycles 6-10 closeout memos).

Cycle 11 is the **first cycle where the substantive work is fixing a procedural-discipline failure**. PI-016 was adopted in cycle 9 as a forecast convention; cycle 10's merge closeout initially reported that PI-016's forecast-discipline had failed for every cycle since adoption. **Cycle 11's PI-018 retroactive correction re-measured each prior cycle's actual count properly (by `git checkout <sha>` to clean working tree before running `make dreaming-validate`) and found the situation is more nuanced:** PI-016's forecast-discipline had partial failures (cycles 6 and 10 miscounted; cycles 7-9 matched). PI-018 addresses this by amending PI-016 with a post-merge verification step and retroactively correcting the wrong counts in cycles 6 and 10's closeout memos (cycles 7-9's closeouts were verified as correctly-quoted and required no edits).

Cycle 11 is also the **second cycle with a code-reviewer sub-agent** (per msg #11647 "use this code review cycle on changes going forward" + msg #11644 "drop a summary after each round. Don't wait for me to respond"). The reviewer evaluates the cycle-11 PR through 5 rounds, with per-round summaries.

Rationale: cycle 11's substantive work is small (~50 lines of Stage-11 workflow-doc + ~70 lines of forecast-presence test) and addresses the partial PI-016 failures for cycles 6 and 10 specifically. PI-018's specific deliverable is the verification step + retroactive correction of cycles 6 and 10 closeout memos; cycles 7-9 were verified correct and required no retroactive edits.

### Trigger narrative

Cycle 10 was triggered by user request "Kick off cycle 10. After you create a new PR with changes spin up a code reviewer to evaluate solution through 5 rounds of code evaluation and fixes to the PR" (Telegram msg #11623, 2026-07-01 01:13 GMT+2). The user-requested scope is two-part: ship a substantive cycle (Stage -3 candidate from cycle-9 closeout) AND spin up a code-reviewer sub-agent for 5 rounds of evaluation + fixes.

Cycle 9's merge closeout (`memory/2026-07-01-cycle-9-closeout.md`) proposed Stage -3 as the cheapest non-trivial cycle-10 candidate, addressing the two-cycle-stale post-amend working-tree-rescue pattern. With PI-006a, PI-014, PI-009, and the AI-overload review date (2026-07-15) all in their prior-cycle states and no new external evidence, Stage -3 is the natural opening.

## Auto-safe changes applied in cycle 10

All cycle-10 changes are `auto_safe`:

- `.openclaw/dreaming/workflow-nightly-dreaming.md` — Stage -3 added before Stage -2 (NEW, PI-017).
- `tests/dreaming/test_pr_readiness.py` — `test_no_post_amend_working_tree_drift` added (NEW).
- `.openclaw/dreaming/regression-scenarios.md` — RS-019 added (NEW).
- `.openclaw/dreaming/evidence-index.md` — EV-019 added (NEW).
- `.openclaw/dreaming/proposed-improvements.md` — PI-017 added (NEW, cycle 10, auto_safe, APPLIED this cycle); cycle-10 status table appended.
- `.openclaw/dreaming/nightly-summary.md` — cycle-10 body prepended (this section); cycle-9 body preserved below.
- `.openclaw/dreaming/pr-change-log.md` — cycle-10 row appended.

No code changes. No parser changes. No spec changes. No schema migrations. No production-runtime changes.

## Validation findings (cycle-10 delta)

- **124 collected tests** on `main` post-cycle-9-merge (`d1cbc08`).
- **+1 test** added in cycle 10: `test_no_post_amend_working_tree_drift`. Total now 125.
- The new test fails on the cycle-10 branch during authoring (because the workflow-doc edit is in the working tree but not yet committed) and passes once the cycle-10 commit lands. This is the natural cycle-authoring workflow; the test enforces "your commit must match your working tree at validation time."
- **0 CI fix-ups.** The PI-008 diminishing-returns curve continues to hold.

## Deterministic tooling opportunities (cycle-10 delta)

- **PI-017** NEW (cycle 10, auto_safe, APPLIED this cycle) — Stage -3 Post-amend verify.
- **PI-006a** still waiting on the OpenClaw runtime side; nothing new on this cycle.
- **PI-014** — proposed; fix is on the same gateway, outside the workflow's surface area.
- **PI-009** still held per "A then B".
- **PI-016** — convention adopted going forward; cycle 10's closeout memos (cycle-closeout and merge-closeout) will be the second application.

## Regression scenarios added (cycle-10 delta)

- **RS-019** — working tree in `.openclaw/dreaming/` must be clean relative to HEAD after commits (NEW; status: `failing` baseline; expected to flip to `passing` after cycle-10 merge).

## Commits (cycle 10)

1. cycle-10 substantive commit — workflow-doc change (Stage -3) + test + RS-019 + EV-019 + PI-017 + cycle-10 Trigger + pr-change-log row. 7 files changed, +300 / −1. Hash captured at PR-creation time in the PR body and merge closeout memo.

## Cycle-10 self-meta observation

Cycle 10 is the **second cycle in a row where the substantive work is a procedural discipline** (PI-017 → Stage -3). Cycles 8 (Stage -2), 9 (PI-016), and 10 (Stage -3) are all procedural-discipline cycles. The cycle-size table goes `4→3→2→2→2→2→2→1→1→1→2` (logical feature commits = 2 — the substantive commit plus any reviewer-driven fix-up commit).

Cycle 10 is also the **first cycle where a code-reviewer sub-agent is involved**. The user's request was "spin up a code reviewer to evaluate solution through 5 rounds of code evaluation and fixes to the PR." This introduces a new shape: the cycle's substantive change is reviewed by an external (to the cycle's own context) reviewer before the cycle is considered complete. The five rounds of evaluation and fixes are the reviewer's iteration loop.

Whether the cycle-size table's logical-feature-commits cell of 2 holds depends on the reviewer finding issues that need fixing. If the reviewer approves without changes, cycle 10 ships at 1 commit and the cycle-size cell is corrected in cycle 11 (same pattern as cycle 7's bookkeeping nit, which cycle 8 reconciled).

## Sub-agent workflow

The cycle-10 code-reviewer sub-agent will be spawned after PR #69 opens. The reviewer evaluates the cycle-10 PR through 5 rounds. Reviewer-driven fixes (if any) are committed as separate commits on the cycle-10 branch. The sub-agent's lifecycle ends when the 5 rounds complete or the reviewer approves.

## Cycle-10 carry-forward

- **PI-006a** still waiting on the OpenClaw runtime side; the principal outstanding PI per the user's original framing in #11557.
- **PI-014** — proposed; fix is on the same gateway but outside the workflow's surface area.
- **PI-009** still held per "A then B".
- **PI-016** — convention adopted going forward.
- **PI-017** (cycle 10) — APPLIED this cycle.
- **Adjacent follow-up (not in PI ledger):** AI-overload retry pattern on `cyber-signal-daily` — review date 2026-07-15.
- **Cycle-10-surfaced question (not yet a PI):** whether the code-reviewer sub-agent workflow itself deserves a workflow-doc stage (e.g., "Stage 0.5: Code reviewer" between pre-push validation and PR creation). The 5-round loop is novel; whether it becomes a recurring cycle pattern is a cycle-11 question.

## Auto-safe changes applied in cycle 11

All cycle-11 changes are `auto_safe`:

- `.openclaw/dreaming/workflow-nightly-dreaming.md` — Stage 11 added before Hard Constraints (NEW, PI-016/PI-018). Documents the closeout-memo convention with the verification step.
- `tests/dreaming/test_pr_readiness.py` — `test_pr_change_log_forecasts_main_post_merge_count` added (NEW). Asserts the most recent cycle row in `pr-change-log.md` contains a `main post-merge (forecast)` line.
- `.openclaw/dreaming/regression-scenarios.md` — RS-020 added (NEW).
- `.openclaw/dreaming/evidence-index.md` — EV-020 added (NEW).
- `.openclaw/dreaming/proposed-improvements.md` — PI-018 status updated to APPLIED (cycle 11, NEW); cycle-11 status table appended.
- `.openclaw/dreaming/nightly-summary.md` — cycle-11 body prepended (uses Stage -2 schema, dogfooding); cycle-10 body preserved below.
- `.openclaw/dreaming/pr-change-log.md` — cycle-11 row appended (after this cycle's commit lands).

No code changes. No parser changes. No spec changes. No schema migrations. No production-runtime changes.

## Validation findings (cycle-11 delta)

- **126 collected tests** on `main` post-cycle-10-merge (`a91abff`).
- **+1 test** added in cycle 11: `test_pr_change_log_forecasts_main_post_merge_count`. Total now 127.
- The new test passes on `main` post-cycle-11-merge because the cycle-11 row in `pr-change-log.md` will contain a `main post-merge (forecast)` line.
- **0 CI fix-ups.** The PI-008 diminishing-returns curve continues to hold.

## Deterministic tooling opportunities (cycle-11 delta)

- **PI-018** NEW (cycle 11, auto_safe, APPLIED this cycle) — Stage 11 Closeout memo convention with post-merge verification step.
- **PI-006a** still waiting on the OpenClaw runtime side; nothing new on this cycle.
- **PI-014** — proposed; fix is on the same gateway, outside the workflow's surface area.
- **PI-009** still held per "A then B".
- **PI-016** — proposed; amended by PI-018 with the verification step.

## Regression scenarios added (cycle-11 delta)

- **RS-020** — Cycle closeout memos must quote validator output twice with explicit branch context and a forecast-accuracy section (NEW; status: `failing` baseline; expected to flip to `passing` after cycle-11 merge).

## Commits (cycle 11)

*(populated after commit lands)*

## Cycle-11 self-meta observation

Cycle 11 is the **first cycle where the substantive work is fixing a procedural-discipline failure**. PI-016 (cycle 9) was a forecast convention. Cycle 10's merge closeout initially reported that PI-016 had failed for every cycle since adoption; **cycle 11's PI-018 retroactive correction re-measured each prior cycle's actual count properly and found the situation is more nuanced:** PI-016's forecast-discipline had partial failures (cycles 6 and 10 miscounted; cycles 7-9 matched). PI-018 amends PI-016 to make it a real verification method. The cycle's substantive work is small (~50 lines of workflow doc + ~70 lines of test) but addresses a 2-cycle discipline failure (cycles 6 and 10 specifically).

Cycle 11 is also the **second cycle with a code-reviewer sub-agent**. Per msg #11647, the reviewer pattern is the user's adopted workflow going forward. Per msg #11644, the reviewer drops a summary after each round rather than waiting for the full 5-round report-back. Cycle 11's reviewer will follow this directive.

Cycle-size table: `4→3→2→2→2→2→2→1→1→1→2→2` (cycle 11 logical feature commits = 2 — the substantive commit plus 1 reviewer-driven fix-up).

## Cycle-11 carry-forward

- **PI-006a** still waiting on the OpenClaw runtime side; the principal outstanding PI per the user's original framing in #11557.
- **PI-014** — proposed; fix is on the same gateway but outside the workflow's surface area.
- **PI-009** still held per "A then B".
- **PI-016** — amended by PI-018; verification step added.
- **PI-017** (cycle 10) — APPLIED.
- **PI-018** (cycle 11) — APPLIED this cycle.
- **Adjacent follow-up (not in PI ledger):** AI-overload retry pattern on `cyber-signal-daily` — review date 2026-07-15.
- **Cycle-10 cycle-size bookkeeping nit:** cycle-10's self-meta pre-populated the cycle-size cell as "2 logical feature commits"; actual was 5 (1 substantive + 4 reviewer-driven fix-ups). Whether reviewer-driven commits count as "cycle feature commits" is a cycle-12 question.

## Sub-agent workflow

The cycle-11 code-reviewer sub-agent will be spawned after PR #70 opens. Per msg #11644, the reviewer drops a summary after each round (5 rounds total). Reviewer-driven fixes (if any) are committed as separate commits on the cycle-11 branch.

---

## Cycle-10 body (carried forward, unchanged)

- **Cycle:** 2026-07-01 cycle-10
- **Branch:** `dreaming/nightly-execution-quality-2026-07-01-cycle-10`
- **Date:** 2026-07-01

## Trigger (cycle 10)

*(cycle-10 trigger preserved; see commit history for the full text)*

---

## Cycle-9 body (carried forward, unchanged)

- **Cycle:** 2026-07-01 cycle-9
- **Branch:** `dreaming/nightly-execution-quality-2026-07-01-cycle-9`
- **Date:** 2026-07-01

## Trigger (cycle 9)

### Surface-Scope Pre-Declaration (Stage -2, PI-015, cycle 8)

- **Workflow target:** dream (`.openclaw/dreaming/`)
- **Surface area:** in-repo
- **Dreaming-ledger scope:** in-ledger
- **Cycle-size budget:** 1 (planned; reconciled at close)

Rationale: cycle 9's substantive work is a single procedural convention change to how cycle closeout memos quote validator output. All changes are inside `aiWorkflows`. PI-016 (the only PI filed this cycle) is `auto_safe`; it changes the prose discipline, not the code, schema, or workflow doc. One commit covers it; splitting PI-016 from artifact tracking would couple unrelated change classes.

### Trigger narrative

Cycle 9 was triggered by user request "Kick off cycle 9" (Telegram msg #11611, 2026-07-01 01:06 GMT+2). Cycle 8's merge closeout (`memory/2026-07-01-cycle-8-closeout.md`) surfaced PI-016 as a candidate for the next cycle. With PI-006a, PI-014, PI-009, and the AI-overload review date (2026-07-15) all in their prior-cycle states and no new external evidence, cycle 9's natural opening is the procedural-evolution candidate from the closeout memo's "Cycle 9 candidates" list.

Cycle 9 is the **first cycle whose substantive work is a procedural convention about how I write memos, not a code/doc/artifact change**. Cycles 5 (PI-006 partial), 6 (PI-006a cross-repo handoff), 7 (PI-014 non-dreaming surfaced), and 8 (PI-015 workflow-doc stage) all shipped substantive procedural changes; cycle 9 ships a meta-procedural change about how cycles are documented.

## Auto-safe changes applied in cycle 9

All cycle-9 changes are `auto_safe`:

- `.openclaw/dreaming/proposed-improvements.md` — PI-016 added (NEW, cycle 9, auto_safe, proposed); cycle-9 status table appended.
- `.openclaw/dreaming/nightly-summary.md` — cycle-9 body prepended (uses Stage -2 schema, dogfooding); cycle-8 body preserved below.
- `.openclaw/dreaming/pr-change-log.md` — cycle-9 row appended.

No code changes. No parser changes. No spec changes. No schema migrations. No production-runtime changes. No workflow-doc stage changes.

## Validation findings (cycle-9 delta)

- **124 collected tests** on `main` post-cycle-8-merge (`ec087fe`).
- **+0 tests** added in cycle 9 (PI-016 is a procedural convention; no automated test is appropriate).
- The Stage -2 test `test_declares_surface_scope_in_trigger` continues to pass on the cycle-9 branch (cycle-9's Trigger is written in the new format, dogfooding).
- **0 CI fix-ups.** The PI-008 diminishing-returns curve continues to hold.
- **0 pre-push catches** expected. Branch cleanup was done at the start of cycle 9 (no lingering dreaming branches from prior sessions).

## Deterministic tooling opportunities (cycle-9 delta)

- **PI-016** NEW (cycle 9, auto_safe, proposed) — cycle closeout memos must quote validator output with explicit branch context.
- **PI-006a** still waiting on the OpenClaw runtime side; nothing new on this cycle.
- **PI-014** — proposed; fix is on the same gateway, outside the workflow's surface area.
- **PI-009** still held per "A then B".

## Regression scenarios added (cycle-9 delta)

None. PI-016 is a procedural convention; no automated test is appropriate.

## Commits (cycle 9)

*(populated after commit lands)*

## Cycle-9 self-meta observation

Cycle 9 is the first cycle whose substantive work is a **procedural convention about how I write memos, not a code/doc/artifact change**. Cycles 6 (cross-repo handoff document), 7 (non-dreaming PI entry), and 8 (workflow-doc stage) all shipped substantive procedural changes; cycle 9 ships a meta-procedural change about how cycles are documented.

The cycle-size table goes `4→3→2→2→2→2→2→1→1→1` (logical feature commits = 1) — cycle 9 is a single-commit cycle, the same shape as cycles 3, 4, 5, 6, 7, and 8. The diminishing-returns P-S-005 curve is preserved at 0 CI fix-ups.

Three cycles in a row (7, 8, 9) have all been **PI-as-self-discipline cycles** — cycles where the substantive work is filing a PI rather than shipping a code/doc/artifact change. The pattern is worth naming: "PI-as-self-discipline" cycles are the cycle type where the cycle's value is in the ledger entry, not in a deliverable. Cycles 6, 7, 8, 9 are all in this category if you squint. Cycle 5 (PI-006 partial) was the last cycle with a true code deliverable (the parser + spec + fixture + 9 tests).

Whether this trend continues (cycle 10 also being PI-as-self-discipline, or PI-014 implementation, or stand-still) is a cycle-10 question.

## Sub-agent workflow

None — cycle 9 was done in the main session.

## Cycle-9 carry-forward

- **PI-006a** still waiting on the OpenClaw runtime side; the principal outstanding PI per the user's original framing in #11557.
- **PI-014** — proposed; fix is on the same gateway but outside the workflow's surface area.
- **PI-009** still held per "A then B".
- **PI-016** (cycle 9) — adopted-as-convention; cycle 10's closeout memo is the next application.
- **Adjacent follow-up (not in PI ledger):** AI-overload retry pattern on `cyber-signal-daily` — review date 2026-07-15.
- **Cycle-9-surfaced observation (not yet a PI):** the Stage -2 schema's "Workflow target" field assumes the workflow has a stable name. If cycle 10 wants to evolve a workflow whose name isn't `dream`, the cycle author must explicitly state it. Whether Stage -2 should also require a workflow-doc update check is a cycle-10 question.
- **Cycle-9-surfaced observation (not yet a PI):** the post-amend-verify footgun disclosed in cycle 8's closeout. Whether to add a Stage -3 ("post-amend verify") is a cycle-10 question.

---

## Cycle-8 body (carried forward, unchanged)

- **Cycle:** 2026-07-01 cycle-8
- **Branch:** `dreaming/nightly-execution-quality-2026-07-01-cycle-8`
- **Date:** 2026-07-01

## Trigger (cycle 8)

### Surface-Scope Pre-Declaration (Stage -2, PI-015, cycle 8)

- **Workflow target:** dream (`.openclaw/dreaming/workflow-nightly-dreaming.md`)
- **Surface area:** in-repo
- **Dreaming-ledger scope:** in-ledger
- **Cycle-size budget:** 1 (planned; reconciled at close)

Rationale: cycle 8 evolves the dream workflow itself (the procedure document, not a neighboring workflow). All changes are inside `aiWorkflows`. The substantive change is a single new stage (Stage -2 Surface-Scope Pre-Declaration); everything else in this cycle is artifact tracking (PI-015, RS-018, EV-017, pr-change-log row). One commit covers it; splitting artifacts vs. workflow-doc change would couple unrelated change classes.

### Trigger narrative

Cycle 8 was triggered by user request "let's define cycle 8 to evolve workflow" (Telegram msg #11587, 2026-07-01 00:51 GMT+2), with follow-up clarifications at #11589 ("Workflow dream is the target") and #11592 ("Q1: yes, Q2: substantive, Q3: no"). The "evolve workflow" framing was ambiguous until the user clarified it meant the dream workflow's own procedure document. Cycles 5, 6, and 7 each retrofitted scope justification in self-meta observations; cycle 8 formalizes pre-declaration as Stage -2.

## Auto-safe changes applied in cycle 8

All cycle-8 changes are `auto_safe`:

- `.openclaw/dreaming/workflow-nightly-dreaming.md` — Stage -2 added before Stage -1 (NEW, PI-015).
- `tests/dreaming/test_pr_readiness.py` — `test_declares_surface_scope_in_trigger` added (NEW).
- `.openclaw/dreaming/regression-scenarios.md` — RS-018 added (NEW).
- `.openclaw/dreaming/evidence-index.md` — EV-017 added (NEW).
- `.openclaw/dreaming/proposed-improvements.md` — PI-015 added (NEW, auto_safe, APPLIED this cycle); cycle-8 summary table appended.
- `.openclaw/dreaming/nightly-summary.md` — cycle-8 body prepended (this section); cycle-7 body preserved below.
- `.openclaw/dreaming/pr-change-log.md` — cycle-8 row appended.

No code changes. No parser changes. No spec changes. No schema migrations. No production-runtime changes.

## Validation findings (cycle-8 delta)

- **123 collected tests** on `main` post-cycle-7-merge (per `make dreaming-validate` run on `b42cdca` during cycle-7 closeout).
- **+1 test** added in cycle 8: `test_declares_surface_scope_in_trigger`. Total now 124.
- The new test fails on `main` (cycle 7's Trigger section does not have the new format) and passes on the cycle-8 branch (cycle 8's Trigger is written in the new format, dogfooding the schema). After cycle-8 merge, the test continues to pass on `main` because cycle 8's Trigger is the most recent in the file.
- **0 CI fix-ups.** The PI-008 diminishing-returns curve continues to hold.

## Deterministic tooling opportunities (cycle-8 delta)

- **PI-015** NEW (cycle 8, auto_safe, APPLIED this cycle) — Stage -2 Surface-Scope Pre-Declaration.
- **PI-006a** still waiting on the OpenClaw runtime side; nothing new on this cycle.
- **PI-014** — proposed; fix is on the same gateway, outside the workflow's surface area.
- **PI-009** still held per "A then B".

## Regression scenarios added (cycle-8 delta)

- **RS-018** — most recent cycle's Trigger section must declare surface scope (NEW; status: `failing` baseline; expected to flip to `passing` after cycle-8 merge).

## Commits (cycle 8)

*(populated after commit lands)*

## Cycle-8 self-meta observation

Cycle 8 is the **first cycle where the workflow-doc change is the deliverable, not just a side effect**. Cycles 2 and 4 added workflow stages (Stage 0, Stage -1) as part of broader PI rollouts; cycle 8 adds Stage -2 as the cycle's entire substantive work. This is a different shape from cycle 5 (substantive PI), cycle 6 (cross-repo handoff), and cycle 7 (non-dreaming ledger entry). The cycle-size table stays at `4→3→2→2→2→2→2→1` (logical feature commits = 1) — cycle 8 is a single-commit cycle, the same shape as cycles 3–7.

| Metric | Cycle 1 | Cycle 2 | Cycle 3 | Cycle 4 | Cycle 5 | Cycle 6 | Cycle 7 | Cycle 8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logical feature commits | 4 | 3 | 2 | 2 | 2 | 2 | 2 | 1 |
| CI fix-up commits | 5 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pre-push validation catches | n/a | 2 | 1 | 1 (negative) | 0 | 0 | 0 | 1 (lingering branches) |
| Total commits | 9 | 4 | 2 | 2 | 2 | 2 | 2 | 1 |

Cycle 7's bookkeeping nit (table said 2 commits, actual was 1) is reconciled in this row. Cycle 8 stays at 1 commit unless scope expands.

The cycle-7 self-meta observation ("first cycle with out-of-scope work") is now obsolete by definition: with Stage -2 in place, scope is declared at the top of every cycle. Cycle 8's Trigger section is the first Trigger section written in the new format; cycles 9 and beyond must follow.

## Sub-agent workflow

None — cycle 8 was done in the main session.

## Cycle-8 carry-forward

- **PI-006a** still waiting on the OpenClaw runtime side; the principal outstanding PI.
- **PI-014** — proposed; fix is on the same gateway but outside the workflow's surface area.
- **PI-009** still held per "A then B".
- **Adjacent follow-up (not in PI ledger):** AI-overload retry pattern on `cyber-signal-daily` — review date 2026-07-15.
- **Newly surfaced by cycle 8 (not yet a PI):** the Stage -2 schema's "Workflow target" field assumes the workflow has a stable name. If cycle 9 wants to evolve a workflow whose name isn't `dream` (e.g., sgp, fetch-pipeline), the cycle author must explicitly state it. Whether Stage -2 should also require a workflow-doc update check (e.g., "if you change `Workflow target`, update the dream-workflow's reference doc") is a cycle-9 question.

---

## Cycle-7 body (carried forward, unchanged)

- **Cycle:** 2026-06-30 cycle-7
- **Branch:** `dreaming/nightly-execution-quality-2026-06-30-cycle-7`
- **Date:** 2026-06-30

## Trigger (cycle 7)

Cycle 7 was triggered by user request "File new PI and start cycle 7", following the cycle-6 closeout memo (`memory/2026-06-30-cycle-6-final.md`). The cycle-6 closeout surfaced the cyber-signal-daily cron staleness as a "worth filing if you want" item — the user picked it up. With PI-006a (the principal outstanding PI from the user's framing) sitting out-of-repo and waiting on the OpenClaw runtime side, and PI-009 still held per "A then B", cycle 7's natural opening was the cross-domain issue.

## Honest re-framing — cycle 7 is mostly a non-dreaming concern filed in the dreaming ledger

PI-014 is about a cron on the gateway that feeds a Telegram-delivered intelligence brief. It is not about a dreaming-workflow artifact, a SGP component, a skill, or anything in `tests/dreaming/`. It is filed here because:

1. The dream-workflow's nightly review surfaced it. The cross-domain check ("what else has been degraded while I wasn't looking?") is part of dreaming's mandate.
2. RS-017 is a regression scenario that fits the existing RS-NNN schema.
3. The fix is auto_safe (script creation; no production-runtime change), which fits the cycle's typical safety profile.

The non-dreaming framing is explicit in the PI body so the eval reader can see "this was filed by dreaming but it's a cron issue." If a future cycle wants to relocate PI-014 to a more appropriate ledger, the cross-repo-handoff-index pattern from cycle 6 (H-001) provides the template.

## Evidence sources (cycle 7)

- **EV-016** (this cycle, NEW) — `cyber-signal-daily` cron feed pipeline is broken (missing fetch script + 19-day stale JSON; adjacent AI-overload retry pattern).
- **Cron runs history** — 97 total runs; consistent staleness notes from 2026-06-11 onward.

## Auto-safe changes applied in cycle 7

All cycle-7 changes are `auto_safe`:

- `.openclaw/dreaming/proposed-improvements.md` — PI-014 entry (NEW); cycle-7 status table.
- `.openclaw/dreaming/regression-scenarios.md` — RS-017 entry (NEW).
- `.openclaw/dreaming/evidence-index.md` — EV-016 entry (NEW; supersedes a prior same-numbered cycle-shape observation — see entry body).
- `.openclaw/dreaming/nightly-summary.md` — this file.
- `.openclaw/dreaming/pr-change-log.md` — cycle-7 row appended.

No code changes. No parser changes. No spec changes. No test-suite changes.

## Validation findings (cycle-7 delta)

- **123 collected tests** on `main` post-cycle-6-merge (per `make dreaming-validate` run on `c21b712` during cycle-6 closeout). No new tests added in cycle 7 — RS-017 is a manual-inspection regression scenario, not an automated test.
- **0 CI fix-ups.** The PI-008 diminishing-returns curve holds; cycle 7 is self-contained.

## Deterministic tooling opportunities (cycle-7 delta)

- **PI-014** NEW (cycle 7, auto_safe, proposed) — restore the `cyber-signal-fetch-feeds.sh` script; either as a separate cron or as a step 1 in the analyst cron.
- **PI-006a** still waiting on the OpenClaw runtime side; nothing new on this cycle.
- **PI-009** still held per "A then B".

## Regression scenarios added (cycle-7 delta)

- **RS-017** — `cyber-signal-daily` cron deliverable freshness (NEW; status: `failing` baseline; expected to flip `passing` when PI-014 lands).

## Commits (cycle 7)

1. `82c2063` — file PI-014, add RS-017, back-fill EV-016; update nightly-summary and pr-change-log. 5 files changed, +314 / −1.

## Cycle-7 self-meta observation

Cycle 7 is the first cycle whose **substantive work is outside the dreaming-workflow's own surface area**. PIs 1–14 inclusive have been filed inside the dreaming ledger, but PI-014's fix lives in `/data/.openclaw/workspace/scripts/` — a directory that doesn't currently exist on this gateway. This is a different shape from PI-006a's cycle-6 handoff (which was a *document* delivered to a different repo); cycle 7 is closer to "first cycle where the PI body says `not in this repo` AND the fix is on the same gateway." Whether that means cycle 7 should be a 2-commit cycle (artifacts only) or a 3-commit cycle (artifacts + the fetch script + cron adjustment) is a scope decision worth making explicit before commit.

| Metric | Cycle 1 | Cycle 2 | Cycle 3 | Cycle 4 | Cycle 5 | Cycle 6 | Cycle 7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Logical feature commits | 4 | 3 | 2 | 2 | 2 | 2 | 2 |
| CI fix-up commits | 5 | 1 | 0 | 0 | 0 | 0 | 0 |
| Pre-push validation catches | n/a | 2 | 1 | 1 (negative) | 0 | 0 | 0 |
| Total commits | 9 | 4 | 2 | 2 | 2 | 2 | 2 |

**Cycle sizes continue at `4→3→2→2→2→2→2`** — cycle 7 stays at 2 commits (artifacts + hygiene). The cycle-7 framing is "out-of-scope ledger addition", not "new in-repo surface area."

## Sub-agent workflow

None — cycle 7 was done in the main session.

## Cycle-7 carry-forward

- **PI-014** — owner: human (or future cycle); not blocking on anything.
- **PI-006a** — still the principal outstanding PI per the user's framing; waiting on OpenClaw runtime side.
- **PI-009** — still held per "A then B".
- **Adjacent follow-up (not in PI ledger):** AI-overload retry pattern on `cyber-signal-daily` — doubles model-call cost and adds latency. Worth tracking as a follow-up PI if the pattern persists past 2026-07-15.

---

## Cycle-5 (carried forward, unchanged)

- **Cycle:** 2026-06-29 cycle-5
- **Branch:** `dreaming/nightly-execution-quality-2026-06-29-cycle-5`
- **Date:** 2026-06-29

## Trigger

Cycle 5 was triggered by user choice "A" between options A/B/C. With PI-009 still held per the "A then B" directive, the natural opening was the substantive unfilled PI: PI-006 (OpenClaw run log). Cycle 5 was framed as the **biggest cycle since cycle 1** by file count (4 new files), but constrained to `tests/dreaming/` + `.openclaw/dreaming/` so the CI-fixup trajectory is preserved at 0.

## Honest re-framing — PI-006 is two pieces

The original PI-006 ("Add structured OpenClaw run log") bundled two parts:

- **Part A: OpenClaw runtime emits JSONL logs.** Lives in OpenClaw core. **Out of dreaming's scope**.
- **Part B: Downstream tooling parses those logs.** Lives in `tests/dreaming/` and `.openclaw/dreaming/`. **In scope.**

Cycle 5 applies Part B (parser + spec + fixture + 9 tests). PI-006's status moves from `proposed` (carried since cycle 1) → **`partial`**. Part A remains in PI-006's body as a clearly-distinct still-open item.

## Evidence sources (cycle 5)

- **EV-014** — PI-006 partial application (the trigger framing)
- **EV-015** — Parser + spec landed (4 new files, 9 new tests)
- **EV-016** — Cycle-5 shape observation: largest cycle since 1 by file count, but still 0 CI fix-ups; size ≠ complexity.

## Auto-safe changes applied in cycle 5

**None.** All cycle-5 changes are `review_required` (PI-006 specifically demands human review of evidence-collection rules per the safety-classification rule). Specifically:

- `.openclaw/dreaming/openclaw-run-log-spec.md` — JSONL format spec, v1 (NEW)
- `tests/dreaming/ev_parser.py` — Deterministic parser (NEW)
- `tests/dreaming/test_openclaw_run_log_parser.py` — 9 pytest cases (NEW)
- `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl` — Fixture exercising happy + error paths (NEW)
- `.openclaw/dreaming/{proposed-improvements,evidence-index,lessons-learned,regression-scenarios,inefficiency-patterns}.md` — Cycle-5 evidence + PI-006 status moves to `partial`; PI-013 added and applied.

## Validation findings (cycle-5 delta)

- **117 collected tests**, 116 passed, 1 skipped (empty-range commits-prefix on the fresh cycle branch — same skip rule from cycle 2).
- The 9 new parser tests cover: happy path, malformed-JSON tolerance, missing-required-field tolerance, unknown-spec-version tolerance, file-not-found, args_summary truncation, message truncation, invalid-tool-status tolerance, and spec_versions_seen recorded.
- **No CI fix-ups.** PI-008's diminishing-returns P-S-005 curve continues; cycle-5's work is what would have been 4 fix-up commits in cycle-1's CI but is now 0.

## Deterministic tooling opportunities (cycle-5 delta)

- **PI-006 partial** (downstream applied; runtime side remains open).
- **PI-013** NEW (cycle 5, applied) — the scope-split audit itself as a concrete change. (The audit's product is this cycle's body.)
- **PI-009** still held per "A then B".
- **PI-006 Part A** (the runtime side) is the open loop requiring an OpenClaw-core PR, not a dreaming PR. Could be linked from this side as a future hint.

## Regression scenarios added (cycle-5 delta)

- RS-016 — long-carried PIs must surface their scope splits (NEW).

## Commits (cycle 5)

1. `da531f0` — code: spec + parser + parser tests + fixture.
2. `271d64b` — artifacts: cycle-5 evidence + PI-006 status moves to `partial`; PI-013 added and applied.

## Cycle-5 self-meta observation

Cycle 5 breaks the monotonic-decreasing commit-count trend **on purpose** by applying the largest deferred PI. The cycle counter still advances, but the cycle size is rebound upward to fit the substantive work. Empirical:

| Metric | Cycle 1 | Cycle 2 | Cycle 3 | Cycle 4 | Cycle 5 |
| --- | --- | --- | --- | --- | --- |
| Logical feature commits | 4 | 3 | 2 | 2 | 2 |
| CI fix-up commits | 5 | 1 | 0 | 0 | 0 |
| Pre-push validation catches | n/a | 2 | 1 | 1 (negative) | 0 |
| Total commits | 9 | 4 | 2 | 2 | 2 |

**Cycle sizes swung from `4→3→2→2→2`** because cycle 5 chose the substantive PI rather than a maintenance cycle. The diminishing-returns curve is now reading a "longer cycle intentional" signal, not a "no new work" signal.

## Sub-agent workflow

None — cycle 5 was done in the main session.

## Cycle-5 carry-forward

- **PI-006 Part A** (runtime side, in OpenClaw core) remains a separate concern; cycle 5 cannot apply it. Cycle 6 split this out as **PI-006a** (per L-016) and shipped a spec-grounded handoff at `.openclaw/dreaming/openclaw-run-log-emitter-handoff.md` (cycle 6).
- **PI-009** still held.
- **PI-006 status is `partial`** — the eval reader can see at-a-glance that one piece is open.


---

## Cycle-5 body (restored after cycle-7 header prepend)

### Trigger (cycle 5)

Cycle 5 was triggered by user choice "A" between options A/B/C. With PI-009 still held per the "A then B" directive, the natural opening was the substantive unfilled PI: PI-006 (OpenClaw run log). Cycle 5 was framed as the **biggest cycle since cycle 1** by file count (4 new files), but constrained to `tests/dreaming/` + `.openclaw/dreaming/` so the CI-fixup trajectory is preserved at 0.

### Honest re-framing — PI-006 is two pieces

The original PI-006 ("Add structured OpenClaw run log") bundled two parts:

- **Part A: OpenClaw runtime emits JSONL logs.** Lives in OpenClaw core. **Out of dreaming's scope**.
- **Part B: Downstream tooling parses those logs.** Lives in `tests/dreaming/` and `.openclaw/dreaming/`. **In scope.**

Cycle 5 applies Part B (parser + spec + fixture + 9 tests). PI-006's status moves from `proposed` (carried since cycle 1) → **`partial`**. Part A remains in PI-006's body as a clearly-distinct still-open item.

### Evidence sources (cycle 5)

- **EV-014** — PI-006 partial application (the trigger framing)
- **EV-015** — Parser + spec landed (4 new files, 9 new tests)
- **EV-016** (cycle 5) — Cycle-5 shape observation: largest cycle since 1 by file count, but still 0 CI fix-ups; size ≠ complexity. (NB: cycle 7's EV-016 entry supersedes this as the canonical "EV-016" in the evidence index, but the cycle-5 observation is preserved here for accuracy.)

### Auto-safe changes applied in cycle 5

**None.** All cycle-5 changes are `review_required` (PI-006 specifically demands human review of evidence-collection rules per the safety-classification rule). Specifically:

- `.openclaw/dreaming/openclaw-run-log-spec.md` — JSONL format spec, v1 (NEW)
- `tests/dreaming/ev_parser.py` — Deterministic parser (NEW)
- `tests/dreaming/test_openclaw_run_log_parser.py` — 9 pytest cases (NEW)
- `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl` — Fixture exercising happy + error paths (NEW)
- `.openclaw/dreaming/{proposed-improvements,evidence-index,lessons-learned,regression-scenarios,inefficiency-patterns}.md` — Cycle-5 evidence + PI-006 status moves to `partial`; PI-013 added and applied.

### Validation findings (cycle-5 delta)

- **117 collected tests**, 116 passed, 1 skipped (empty-range commits-prefix on the fresh cycle branch — same skip rule from cycle 2).
- The 9 new parser tests cover: happy path, malformed-JSON tolerance, missing-required-field tolerance, unknown-spec-version tolerance, file-not-found, args_summary truncation, message truncation, invalid-tool-status tolerance, and spec_versions_seen recorded.
- **No CI fix-ups.** PI-008's diminishing-returns P-S-005 curve continues; cycle-5's work is what would have been 4 fix-up commits in cycle-1's CI but is now 0.

### Deterministic tooling opportunities (cycle-5 delta)

- **PI-006 partial** (downstream applied; runtime side remains open).
- **PI-013** NEW (cycle 5, applied) — the scope-split audit itself as a concrete change. (The audit's product is this cycle's body.)
- **PI-009** still held per "A then B".
- **PI-006 Part A** (the runtime side) is the open loop requiring an OpenClaw-core PR, not a dreaming PR. Could be linked from this side as a future hint.

### Regression scenarios added (cycle-5 delta)

- RS-016 — long-carried PIs must surface their scope splits (NEW).

### Commits (cycle 5)

1. `da531f0` — code: spec + parser + parser tests + fixture.
2. `271d64b` — artifacts: cycle-5 evidence + PI-006 status moves to `partial`; PI-013 added and applied.

### Cycle-5 self-meta observation

Cycle 5 breaks the monotonic-decreasing commit-count trend **on purpose** by applying the largest deferred PI. The cycle counter still advances, but the cycle size is rebound upward to fit the substantive work. Empirical:

| Metric | Cycle 1 | Cycle 2 | Cycle 3 | Cycle 4 | Cycle 5 |
| --- | --- | --- | --- | --- | --- |
| Logical feature commits | 4 | 3 | 2 | 2 | 2 |
| CI fix-up commits | 5 | 1 | 0 | 0 | 0 |
| Pre-push validation catches | n/a | 2 | 1 | 1 (negative) | 0 |
| Total commits | 9 | 4 | 2 | 2 | 2 |

**Cycle sizes swung from `4→3→2→2→2`** because cycle 5 chose the substantive PI rather than a maintenance cycle. The diminishing-returns curve is now reading a "longer cycle intentional" signal, not a "no new work" signal.

### Sub-agent workflow

None — cycle 5 was done in the main session.

### Cycle-5 carry-forward

- **PI-006 Part A** (runtime side, in OpenClaw core) remains a separate concern; cycle 5 cannot apply it. Cycle 6 split this out as **PI-006a** (per L-016) and shipped a spec-grounded handoff at `.openclaw/dreaming/openclaw-run-log-emitter-handoff.md` (cycle 6).
- **PI-009** still held.
- **PI-006 status is `partial`** — the eval reader can see at-a-glance that one piece is open.
