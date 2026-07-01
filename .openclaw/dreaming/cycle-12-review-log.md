# Cycle 12 review log (PR #71, commit 956c2ce)

Reviewer: code-reviewer sub-agent (cycle 12)
Branch: dreaming/nightly-execution-quality-2026-07-02-cycle-12

## Final summary

(Filled in at the end after all 5 rounds.)

## Per-round entries

### Round 1 (flex): Stage 0a schema/format compliance

**Default purpose:** Schema/format compliance of the new Stage 0a. Compare against Stage 0 (which it extends) and Stage -2/Stage -3/Stage 11/Stage 12 (the existing convention). Does Stage 0a follow the same structure (Required step, Constraints, Validation required, Why this stage exists)?

**Finding:** Stage 0a used inline `**Why this step exists**` (bolded) and lacked the formal `### Required step` / `### Constraints` / `### Validation required` / `### Why this stage exists` headings used by Stages -2, -3, 11, and 12. Stage 0 (its parent) also lacks these headings — but Stage 0 is a one-paragraph reference to `make dreaming-validate` rather than a substantive stage. Stage 0a is substantive (it introduces a new workflow step that is the symmetry partner of Stage 11 / PI-018) and should follow the same convention as other substantive stages.

**Fix-up commit:** `9e247f6` — upgrade Stage 0a to use the four-heading schema.

**Validation:** `make dreaming-validate` returns 136 passed, 0 failed after the commit.

### Round 2 (flex): test quality of `test_pr_change_log_includes_collect_only_forecast_baseline`

**Default purpose:** Test quality / tightness. Does the test actually catch the cycle-11 failure mode (a cycle row without a collect-only baseline)? Does it have false-positive risks? Could a placeholder baseline (`TBD`, `to be determined`) pass? Could narrative mentions pass?

**Finding (Round 2):** The test's single regex only matched the plain-bullet form (without markdown bold) and the heading-with-number-on-same-line form. The test's OWN error message suggested a bullet-bold form (`- **Collected-test baseline (forecast):** 132 tests collected`) that the regex actually REJECTED. This was a self-contradiction: a future cycle author following the error message's example would still fail the test. Empirical verification: substituting the cycle-12 row's `Collected-test baseline (forecast)` line with the error message's suggested form returned no match.

All five Round-5 failure-mode simulations behaved correctly with the original regex (missing line → fail, TBD → fail, to be determined → fail, narrative only → fail, valid count → pass). The Round-2 issue was specifically about the THREE FORMS the test accepts, not the placeholder/narrative catching.

**Fix-up commit:** `e3c480a` — replace single regex with three regexes (heading + body, bullet with optional `**` bold, plain line). Mirrors cycle-11's `test_pr_change_log_forecasts_main_post_merge_count` three-form approach (commit `a280189`).

**Verification (post-fix, all 10 cases):**
- Heading + body line (with blank line between): pass
- Heading + body line (no blank line): pass
- Plain line: pass
- Bullet (no bold): pass
- Bullet with `**` bold (the error message's form): pass ← was failing before
- Heading with number on heading line: pass
- Singular "1 test collected": pass
- `TBD`: fail (good)
- "to be determined": fail (good)
- Narrative only: fail (good)
- Empty/missing: fail (good)

**Validation:** `make dreaming-validate` returns 136 passed, 0 failed after the commit.

### Round 3 (flex): cross-artifact consistency check

**Default purpose:** Does the cycle-12 row in `pr-change-log.md` use the partial-failures framing (cycle 11 was off by +3, not "fully matches" or "fully off")? Does PI-020's body accurately describe the cycle-11 finding? Do RS-022 / EV-022 / PI-020 cross-reference correctly?

**Findings (Round 3):**

1. ✅ Cycle-12 row uses partial-failures framing: "Cycle 11's forecast missed by +3 because the forecast reasoned from `def test_` count but did not account for `@pytest.mark.parametrize`..." (line 597 of pr-change-log.md).
2. ❌ PI-020's status was `proposed (cycle 12, NEW)` but the cycle-12 row labels it `applies-this-cycle`. Should be `APPLIED (cycle 12, NEW)`.
3. ❌ PI-020's "Affected package" said `Stage 0 amended with collect-only forecast step` but the actual change was `Stage 0a added (NEW section under Stage 0)`.
4. ❌ PI-020's "Validation required" said `amend Stage 0` instead of `add Stage 0a`. Same wording issue.
5. ❌ cycle-10 PI status table in `proposed-improvements.md` did not include PI-020 (cycle 11 added PI-018/PI-019 to this table when those were applied; cycle 12 should mirror).
6. ❌ `nightly-summary.md` cycle-12 Surface area line said `Stage 0 amendment for collect-only forecast step` but the change was `Stage 0a added`.
7. ✅ RS-022 cross-references EV-022 + cycle-11 closeout memo correctly.
8. ✅ EV-022 cross-references RS-022 correctly.
9. ⚠️ Cross-references for "Cycle 11 added 3 new files" wording — this is the Round-4 retroactive-correction finding (the cycle-11 row in pr-change-log.md and the cycle-11 closeout memo both say "Cycle 11 added 3 new files" but only 1 was actually new; 2 were modifications). Saved for Round 4.

**Fix-up commit:** `a1920b3` — PI-020 status (proposed → APPLIED), Affected package wording, Validation required wording, cycle-10 PI status table (added PI-020 row), nightly-summary.md Surface area wording.

**Validation:** `make dreaming-validate` returns 136 passed, 0 failed after the commit.

### Round 4 (flex): retroactive wording correction for "Cycle 11 added 3 new files"

**Default purpose:** Retroactive-correction accuracy (per the cycle-11 review log's round 4 default purpose). The Round 3 review flagged that 5 places in the dreaming artifacts incorrectly stated "Cycle 11 added 3 new files to `.openclaw/dreaming/`" when only 1 of the 3 files was actually new; the other 2 were modifications of existing files.

**Verification of the finding (Round 4):** `git show --stat fd822b0` (the cycle-11 merge SHA) confirms:
- `.openclaw/dreaming/cycle-11-review-log.md` | 257 ++++ → NEW file (no prior history)
- `.openclaw/dreaming/workflow-nightly-dreaming.md` | 68 ++++ → MODIFIED (prior history, modified by 9fe37e4)
- `.openclaw/dreaming/proposed-improvements.md` | 41 ++-- → MODIFIED (prior history, modified by 9bc894a)

So 1 NEW + 2 modifications, not 3 new files.

**Mechanism (corrected):** `_all_dreaming_files()` in `tests/dreaming/test_no_hidden_reasoning_capture.py` enumerates EVERY file in `.openclaw/dreaming/` and feeds 3 parametrized tests (`test_no_forbidden_heading`, `test_no_forbidden_marker`, `test_no_fenced_reasoning_block`). The +3 parametrized test invocations on `main` post-cycle-11-merge came from the 1 NEW file (cycle-11-review-log.md) being newly enumerated by these 3 parametrized tests (3 tests × 1 new file = +3). The 2 modified files were already present pre-cycle-11 and were already being enumerated by `_all_dreaming_files()`, so they did not add new parametrized test invocations.

The Round 3 note added to `nightly-summary.md` had it right: "The 1 new file contributes +3 parametrized test invocations because `_all_dreaming_files()` is enumerated by 3 test functions in `test_no_hidden_reasoning_capture.py`." This was the corrected mechanism; the main prose in 4 other files still had the incorrect "added 3 new files" wording and needed to be brought in line.

**Fix-up commit:** `0f9f38d` — corrects the wording in:
- `.openclaw/dreaming/pr-change-log.md` (cycle-12 row's Actual section)
- `.openclaw/dreaming/evidence-index.md` (EV-022 evidence statement + quantitative summary reference)
- `.openclaw/dreaming/nightly-summary.md` (cycle-12 PI-018 line; replaces the Round 3 parenthetical note with an explicit retroactive-correction note)
- `.openclaw/dreaming/proposed-improvements.md` (PI-020 Observed problem)
- `memory/2026-07-01-cycle-11-closeout.md` (closeout memo's "Why the forecast missed by +3" section)

Also backfills `memory/2026-07-01-cycle-11-closeout.md` as a new tracked file. The closeout memo was referenced from tracked files (pr-change-log.md, evidence-index.md) but had never been committed to git in any branch. Backfilling it as part of this commit makes the cross-references resolvable and preserves the cycle-11 record properly. The closeout memo's substantive content (forecast-accuracy section, post-merge verification, carry-forward notes, code-reviewer sub-agent section, cycle-11 carry-forward) is unchanged from its pre-existing working-tree form; only the wording about "3 new files" → "1 NEW + 2 modifications" was corrected.

**Validation:** `make dreaming-validate` returns 136 passed, 0 failed after the commit.