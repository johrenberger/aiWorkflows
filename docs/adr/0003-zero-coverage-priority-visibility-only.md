# ADR 0003: Zero-coverage priority is visibility-only, not a formula change

* **Status:** Accepted (2026-06-12)
* **Context:** Story 024 of v2 (test-factory) work, PR #38
* **Deciders:** software-engineer, test-automation, code-review-agent
* **Tags:** v2, zero-coverage, priority, mutation-targeting

## Context and Problem Statement

v2's mutation-targeting ranks files by `priority = risk_score *
coverage_gap`. With `risk_score` based on cyclomatic complexity
and `coverage_gap` based on `100 - line_coverage`, the formula
works — but zero-coverage files (line_coverage=0) all tie at
`coverage_gap=100`. So a complex untested file and a trivial
untested file get the same priority.

The question: should we change the priority formula to break
the tie (e.g. add a `zero_coverage` bonus term), or should we
just make zero-coverage items MORE VISIBLE in the output
without changing the formula?

## Considered Options

1. **Visibility-only improvement (chosen)**: Don't change the
   formula. Instead, add a `zero_coverage_queue.json` artifact
   that surfaces zero-coverage items separately, sort by
   `risk_score` (not `priority`), and add a `--zero-coverage-only`
   flag for the `queue` subcommand.
2. **Add a `zero_coverage` bonus to the priority formula**:
   E.g. `priority = risk_score * coverage_gap * (1.5 if
   line_coverage==0 else 1.0)`. This makes zero-coverage items
   float to the top, but adds a magic constant to the formula.
3. **Use `coverage_gap=180` for zero-coverage items** (already
   true with the current formula, since `100 - 0 = 100`; but
   we could push it higher with an explicit `min(180,
   coverage_gap)` adjustment).
4. **Add a separate `risk_score` for zero-coverage items**:
   Out of scope — would require a new scoring algorithm.

## Decision Outcome

**Chosen option: 1 (visibility-only).**

The current priority formula already works for the common case:
a complex file with low coverage is the right target. The
zero-coverage case is special because every zero-coverage file
ties at the same priority. The fix is to surface them
separately, NOT to change the formula.

Why not change the formula? Three reasons:

1. **The formula is simple and understandable.** Adding a bonus
   term is a magic constant that future readers have to figure
   out. The current formula `risk_score * coverage_gap` is
   self-explanatory.
2. **The bonus term would be a tiebreaker, not a real change.**
   Zero-coverage items would float to the top because of the
   bonus, not because of their actual risk. The visibility
   approach lets the user sort by `risk_score` (the meaningful
   axis) without the formula being load-bearing.
3. **The visibility approach is reversible.** If we change our
   mind about zero-coverage handling, we just stop writing the
   artifact. If we change the formula, we have a behavior change
   that affects everyone.

## Consequences

### Positive
- The priority formula is unchanged. Existing prioritization
  behavior is preserved.
- Zero-coverage items are visible (separate artifact, separate
  flag). The user can target them deliberately.
- The `zero_coverage_queue.json` artifact is **additive** —
  not a replacement for the regular queue. Users can use both.
- Sort by `risk_score` in `zero_coverage_queue.json` is the
  meaningful axis (priority collapses to `risk_score * 180`
  for all zero-coverage items, so it's degenerate).

### Negative
- The `--zero-coverage-only` flag is part of the public API.
  Removing it later would be a breaking change.
- The artifact name (`zero_coverage_queue.json`) is a bit
  long. Future refactoring might rename to `untested_queue.json`
  or `gap_queue.json`.

### Neutral
- The `is_zero_coverage` annotation is `True` for both
  measured-zero and unmeasurable (story 031 splits these
  into two artifacts).

## Follow-up

- (PR #38) `zero_coverage_queue.json` artifact + `--zero-coverage-only`
  flag + "Zero-Coverage Files" section in the markdown report.
- (PR #41, story 031) `coverage_status()` 3-state helper splits
  measured-zero from unmeasurable.
- (future) If the priority formula is ever changed, the change
  should be a separate story with a separate ADR.

## More Information

- Story markdown: `workflows/application-mutation-testing/stories/024_v2_zero_coverage_priority.md`
- PR: https://github.com/johrenberger/aiWorkflows/pull/38
- Merge commit: `1b5e0fb`
- Calibration: this ADR was identified by `code-change-review`
  reproducer as finding "design decision about visibility vs
  formula change" on the PR #38 diff (calibration pass #4 of 5+).
