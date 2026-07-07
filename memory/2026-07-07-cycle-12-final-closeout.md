# Cycle 12 — Final closeout (post-PR-#72 verification per PI-018 + Stage 11)

**Cycle:** 12 (final wrap)
**Date:** 2026-07-07
**Branch:** `dreaming/nightly-execution-quality-2026-07-02-cycle-12` (merged and deleted via PR #72 cleanup)
**PR:** #72 (merged; merge SHA `57ef0f0`)
**Post-merge reconciliation commit (local main):** `5fbc1f9`

## Context

PR #71 merged cycle-12 at Round 3 fix-up state (`34f3793`), leaving Rounds 4 and 5 work (the retroactive wording correction + drift check / regex widening) on the cycle-12 branch but not in the merge. PR #72 was opened 2026-07-07 to bring those 4 commits onto `main`:

- `0f9f38d` Round 4: cycle-11 cross-reference wording fix in `pr-change-log.md`
- `ebbb3b9` Round 4: cycle-12 review-log entry
- `6301032` Round 5: drift check (±25) + bullet-regex widening for `test_pr_change_log_includes_collect_only_forecast_baseline`
- `088bfd7` Round 5: cycle-12 review-log entry + final summary

PR #72 CI: both `validate` checks PASS (`run/28877506405`, `run/28877580910`). Merged via merge commit (`57ef0f0`). Local `main` had an unpushed post-merge correction (`2085fdb`) — reconciled via local merge commit (`5fbc1f9`), giving final local `main` at `5fbc1f9`.

## Post-merge verification (Stage 11 + PI-018) — final, on `main`

After PR #72 merged to `origin/main` (merge SHA `57ef0f0`) and the local post-merge correction reconciliation (commit `5fbc1f9`), ran `make dreaming-validate` on actual `main` (clean working tree, on `main` branch):

```
134 passed, 1 skipped, 1 expected-fail-on-main (test_current_branch_uses_dreaming_prefix)
```

**Test count breakdown:**
- `pytest tests/dreaming/ --collect-only -q | grep "tests collected"` → **136 tests collected**
- 136 collected − 1 skipped (`test_commits_use_chore_dreaming_prefix`, skipped in detached-HEAD mode) − 1 failed (`test_current_branch_uses_dreaming_prefix`, expected to fail on `main`) = **134 passed**

## Forecast-accuracy (PI-018 + PI-020) — final, on `main`

**Forecast (from cycle-12 `pr-change-log.md` row, `main` post-merge):** 136 passed + 1 skipped + 1 expected-fail-on-main.

**Actual on `main` post-merge (re-measured at `5fbc1f9`, clean working tree, on `main` branch):** **134 passed + 1 skipped + 1 expected-fail-on-main**.

**Delta:** **−2 passed** on `main` post-merge vs forecast. The forecast did NOT match the actual (a partial-failure forecast, but closer than the −4 delta measured at PR #71's `34f3793`).

## Why the forecast missed by −2 (different from the −4 at PR #71)

The cycle-12 forecast format was **`136 passed + 1 skipped + 1 expected-fail-on-main`**. The arithmetic of "136 passed + 1 skipped + 1 expected-fail-on-main" implies **138 collected tests**. But the cycle-12 row's reasoning (line 645) computed `136` as the *post-merge collect-only baseline*: branch-local 133 + 3 parametrized expansion (reviewer log) = 136 tests collected. So the cycle-12 forecast had a **formatting inconsistency**: it labeled the `136` as "passed" when it was actually the **collected** count.

**Real forecast-arithmetic check:**
- If 136 = collected → passed = 136 − 1 (skipped) − 1 (expected-fail-on-main) = **134 passed + 1 skipped + 1 expected-fail-on-main** ← matches actual
- If 136 = passed → collected = 136 + 1 + 1 = 138 ← would require 138 tests collected, but actual collect-only shows 136

The forecast's *number* (`136`) was correct as a *collected* count. The forecast's *label* (`passed`) was wrong. The cycle-12 forecast-format convention needs to label the post-merge count as either "collected" or "passed" and apply the −1/−1 correctly. This is a **PI-020 forecast-format refinement**, distinct from the cycle-11 +3 off-by-N (which was a methodology failure) and the cycle-12 PR-#71 −4 (which was a merge-state-assumption failure).

**Forecast-accuracy verdict (final):** the cycle-12 forecast was **numerically correct as a collected count** (136 matches `pytest --collect-only`) but was **labeled incorrectly as a passed count** in the pr-change-log row. The actual `main` count of 134 passed is fully consistent with the cycle-12 forecast's underlying reasoning; the −2 delta is purely a forecast-format labeling bug.

## Comparison: forecast accuracy across cycle-11, cycle-12 PR #71, cycle-12 PR #72

| Cycle | Forecast | Actual | Delta | Cause |
| --- | --- | --- | --- | --- |
| Cycle-11 (PR #70) | `127 + 1 + 1` | `130 + 1 + 1` | +3 passed | methodology: parametrized-test expansion not accounted for |
| Cycle-12 PR #71 (`34f3793`) | `136 + 1 + 1` | `132 + 1 + 1` | −4 passed | merge-state assumption wrong (reviewer log not in merge) |
| Cycle-12 PR #72 (`5fbc1f9`) | `136 + 1 + 1` | `134 + 1 + 1` | −2 passed | forecast-format labeling bug (136 = collected, not passed) |

PI-018 / Stage 11 caught all three. The cycle-12 final state (`134 + 1 + 1`) is **internally consistent with the cycle-12 forecast's underlying reasoning** — the only error was the forecast's label of "136 passed" vs "136 collected".

## Cycle-12 carry-forward (final)

The previous closeout memo (`memory/2026-07-01-cycle-12-closeout.md`) carry-forwards stand. Adding:

5. **PI-020 forecast-format labeling (cycle-13+ candidate).** The cycle-12 row's `136 + 1 + 1` should have been labeled `136 collected → 134 passed + 1 skipped + 1 expected-fail-on-main`. Possible cycle-13 PI: **PI-021 (forecast-format clarification)** — the cycle row's `Main post-merge (forecast)` heading should always include the explicit `collected → passed` arithmetic, and `make dreaming-validate` should verify the labels are consistent with the actual collect-only count.

6. **The two-merge cycle pattern.** Cycle 12 took two PRs to land all 5 reviewer-driven fix-ups (PR #71 = substantive + rounds 1-3; PR #72 = rounds 4-5). This is the first cycle to need a follow-up PR to complete reviewer work. Future cycles should aim for a single PR merge after all reviewer rounds complete (per carry-forward item 3 in the previous closeout).

## Refs

- `memory/2026-07-01-cycle-12-closeout.md` (PR-#71 closeout)
- `.openclaw/dreaming/pr-change-log.md` (cycle-12 row, line 645 forecast, line 646 PR-#71 actual)
- `.openclaw/dreaming/cycle-12-review-log.md` (Rounds 4 and 5 entries, now in `main` via PR #72)
- `tests/dreaming/test_pr_readiness.py` (drift check + regex widening, now in `main` via PR #72)
- PR #71 (cycle 12 first-merge; merge SHA `34f3793`)
- PR #72 (cycle 12 follow-up merge; merge SHA `57ef0f0`)
- Post-merge correction: commit `2085fdb` on `main` (PR-#71 actual-count correction)
- Local main reconciliation merge: `5fbc1f9` (PR #72 + post-merge correction reconciled)