# Cycle 11 — Closeout memo (post-merge verification per PI-018 + Stage 11)

**Cycle:** 11
**Date:** 2026-07-01
**Branch:** `dreaming/nightly-execution-quality-2026-07-01-cycle-11` (now merged and deleted)
**PR:** #70 (merged; merge SHA `fd822b0`)

## Post-merge verification (Stage 11 + PI-018)

After PR #70 merged to `main`, ran `make dreaming-validate` on actual `main` at `fd822b0` (clean working tree, no dream-branch checked out):

```
130 passed, 1 skipped, 1 expected-fail-on-main (test_current_branch_uses_dreaming_prefix)
```

## Forecast-accuracy (PI-018)

**Forecast (from cycle-11 `pr-change-log.md` row, branch-local):** 132 passed, 0 failed, 0 skipped.
**Forecast (from cycle-11 `pr-change-log.md` row, `main` post-merge):** 127 passed + 1 skipped + 1 expected-fail-on-main.

**Actual on `main` post-merge (re-measured):** **130 passed + 1 skipped + 1 expected-fail-on-main**.

**Delta:** +3 passed on `main` post-merge vs forecast. The forecast did NOT match the actual.

## Why the forecast missed by +3

The cycle-11 forecast predicted `127 + 1 + 1` for `main` post-merge, reasoning:
- cycle-10's `main` was `126 + 1 + 1`
- cycle 11 adds 1 test (`test_pr_change_log_forecasts_main_post_merge_count`)
- expected: `127 + 1 + 1`

The actual delta was **+4 tests**, not +1:
- `test_pr_readiness.py`: 9 → 10 tests collected (+1 from the new `test_pr_change_log_forecasts_main_post_merge_count` function)
- `test_no_hidden_reasoning_capture.py`: 52 → 55 tests collected (+3, from `@pytest.mark.parametrize("path", _all_dreaming_files(), ...)` enumerating the new files in `.openclaw/dreaming/`)

**The +3 in `test_no_hidden_reasoning_capture.py` was not anticipated** because the forecast only counted net-new `def test_` functions, not parametrized test expansions. Cycle 11 touched 3 files in `.openclaw/dreaming/`:
- `.openclaw/dreaming/cycle-11-review-log.md` — **NEW** (committed by reviewer)
- `.openclaw/dreaming/workflow-nightly-dreaming.md` — modified (Stage 11 + Stage 12 added)
- `.openclaw/dreaming/proposed-improvements.md` — modified (PI-018 + PI-019 added)

Of these, only the 1 NEW file (cycle-11-review-log.md) was newly enumerated by `_all_dreaming_files()` and contributed to the +3 parametrized test expansion. The 2 modified files were already present in `.openclaw/dreaming/` before cycle 11, so they were already being enumerated by `_all_dreaming_files()` and did not add new parametrized test invocations.

The `_all_dreaming_files()` helper in `test_no_hidden_reasoning_capture.py` enumerates every file in `.openclaw/dreaming/` and runs three parametrized tests per file. So each NEW (not previously-present) file adds +3 new test invocations.

**This is a parametric test expansion driven by artifact count, not by test-function count.** Future cycles' forecasts must account for this when adding new artifact files.

## Updated forecast-discipline convention (carry-forward to cycle 12)

PI-016's forecast convention assumed `passed_count` is a function of `def test_` count. This is true for `test_pr_readiness.py` but not for `test_no_hidden_reasoning_capture.py` (and possibly others with `@pytest.mark.parametrize` over discovered files). Per PI-018's verification step, the forecast must be verified post-merge by `make dreaming-validate` on actual `main`. Cycle 11's forecast missed by +3, which the closeout memo now documents.

**Going forward (cycle 12+):** when a cycle adds new files to `.openclaw/dreaming/`, the forecast must include +3 per new file (one per parametrized test in `test_no_hidden_reasoning_capture.py`). Better yet: cycle 12 can add a `--collect-only` step to the forecast workflow that enumerates collected tests at the time the forecast is written, giving a more precise baseline. This is a candidate for a future cycle-12 PI (PI-020 candidate).

## What cycle 11 actually shipped

- Stage 11 + Stage 12 added to `workflow-nightly-dreaming.md` (PI-016/PI-018/PI-019)
- `test_pr_change_log_forecasts_main_post_merge_count` (PI-018, RS-020)
- RS-020 (closeout memo convention) + RS-021 (code-reviewer convention)
- EV-020 (cross-cycle actual-vs-claimed measurements) + EV-021 (code-reviewer catches)
- PI-018 + PI-019 added to `proposed-improvements.md` (APPLIED)
- Cycle-11 reviewer sub-agent ran 5 rounds + second-pass verification (PI-019 / Stage 12 codification)
- Retroactive corrections to cycles 6-10 closeout memos (PI-018 retroactive)
- Cross-cycle actual-vs-claimed verification (PI-018, on clean working tree)

## Code-reviewer sub-agent (cycle 11 = second-of-kind)

- 5 rounds completed with second-pass verification on rounds 4 and 5
- 6 fix-up commits applied (1 per round in first pass + 1 round-5 second-pass catch)
- Recommendation: merge as-is
- Most important catch: round 5 regex false-positive (would have passed on `TBD` placeholder); second-pass verified and fixed
- Reviewer log: `.openclaw/dreaming/cycle-11-review-log.md` (~8.2KB, 257 lines)

## Cycle-11 carry-forward

1. **Forecast methodology refinement (cycle-12 candidate).** Add a `--collect-only` step to the forecast workflow so cycles can compare collected-test counts at forecast-time vs post-merge. Could be PI-020.
2. **Cycle-size bookkeeping nit.** Cycle-11 forecast was 2 commits; actual was 9 (1 substantive + 7 reviewer-driven + 1 PI-019/Stage-12 amendment). Same pattern as cycle-10's 2→5. Cycle 12 should reconcile by reporting actual-vs-forecast as a matter of course, or by adjusting the cycle-size budget methodology.
3. **PI-018 / Stage 11 verified working.** The forecast-discipline had a partial failure on cycle 11 (forecast missed by +3), and the verification step caught it correctly. PI-018 is doing its job.

## Refs

- `.openclaw/dreaming/workflow-nightly-dreaming.md` (Stage 11 + Stage 12)
- `.openclaw/dreaming/proposed-improvements.md` (PI-018 + PI-019)
- `.openclaw/dreaming/regression-scenarios.md` (RS-020 + RS-021)
- `.openclaw/dreaming/evidence-index.md` (EV-020 + EV-021)
- `.openclaw/dreaming/cycle-11-review-log.md` (reviewer log)
- `.openclaw/dreaming/pr-change-log.md` (cycle-11 row)
- Telegram msg #11687 (cycle 11 trigger: "Candidate 1")
- Telegram msg #11772 (round purposes locked: 4 = retroactive-correction accuracy, 5 = real-world fitness)
- Telegram msg #11773 (Stage 12 / PI-019 codification)
- PR #70 (cycle 11, merged)
- Merge SHA `fd822b0`
- Cycles 6-10 closeout memos (retroactive corrections per PI-018)