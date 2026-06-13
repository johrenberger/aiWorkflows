# ADR 0001: v2 coverage generation default-on

* **Status:** Accepted (2026-06-10)
* **Context:** Story 020 of v2 (test-factory) work, PR #34
* **Deciders:** software-engineer, test-automation, code-review-agent
* **Tags:** v2, defaults, coverage, mutation

## Context and Problem Statement

In every mutation run since story 019 (which wired v2's
`risk_scores.json` into mutation as a first-class coverage
source), v2 has been invoked **without** `--generate-coverage`.
Result: `line_coverage` was 0.0 across the board in the
`risk_scores.json` consumed by mutation's selector. This made
v2's `coverage_gap` signal degenerate (always "100% gap") and
forced mutation's selector to fall back to its readiness-40
heuristic uniformly — effectively losing the coverage-based
targeting that the v2 work was designed to enable.

The cost of running `--generate-coverage` by default is real:
~5-30 min per `test-factory run` for a typical repo, plus v2
mutates the target repo (writes `coverage.json` / `coverage.xml`).
Both are real, and both are why `--generate-coverage` is
currently opt-in (PR #23, 2026-06-10).

How do we make the right thing the default while still giving
the user a way to opt out?

## Considered Options

1. **Default-flip** (chosen): `--generate-coverage` becomes the
   default. Add `--no-generate-coverage` in a mutually exclusive
   group. The choice to skip coverage generation becomes a
   deliberate one, not a forgotten flag.
2. **Add a third flag `--coverage-on-by-default`**: Same effect
   as default-flip, but adds API surface. A `default` is a
   `default` — pretending otherwise is a leak.
3. **Don't change the default; document better**: The status quo.
   Users keep forgetting the flag; mutation's selector keeps
   falling back to readiness-40.
4. **Make coverage generation read-only**: Refactor v2 to never
   mutate the target repo. Out of scope — would require
   re-architecting the JaCoCo/pytest/lcov integrations to write
   to a sandbox.

## Decision Outcome

**Chosen option: 1 (default-flip).**

The right thing is the default thing. If the cost of running
coverage is so high that you want to opt out, you SHOULD be
required to type `--no-generate-coverage` — that's a deliberate
choice, not an accident. The cost of the forgotten flag is
silent (selector falls back to readiness-40 and mutation targets
a non-prioritized list), so the system can't "ask the user" the
way an interactive system could.

The mutually-exclusive-group design (`--generate-coverage` and
`--no-generate-coverage` in the same group) means argparse will
catch the case where the user passes both flags and fail loudly
(rather than silently pick one).

## Consequences

### Positive
- The common case (running `test-factory run --repo PATH`) just
  works — `risk_scores.json` has real coverage values, mutation's
  selector prioritizes based on coverage gap.
- The opt-out is explicit. Users who want to skip coverage know
  they're skipping it.
- mutation's selector no longer falls back to readiness-40
  uniformly; the v2 prioritization is effective end-to-end.

### Negative
- Users who were relying on the silent "skip coverage" behavior
  will see a 5-30 min slowdown. The error message at the end
  of `test-factory run` ("coverage generation skipped because
  --no-generate-coverage was passed") makes the cause visible.
- The `--no-generate-coverage` flag is part of the public API
  now. Removing it later would be a breaking change.

### Neutral
- The coverage generation itself is unchanged. The same JaCoCo
  / pytest / lcov commands run; the same outputs are written.
  Only the default flag changes.

## Follow-up

- (PR #34) `test-factory run` defaults to coverage generation on.
  `--no-generate-coverage` is the explicit opt-out.
- (future) If coverage generation cost becomes a real complaint
  (e.g. 30 min for a small repo), consider caching coverage
  artifacts and reusing them across `test-factory run` invocations.

## More Information

- Story markdown: `workflows/application-mutation-testing/stories/020_v2_always_generate_coverage.md`
- PR: https://github.com/johrenberger/aiWorkflows/pull/34
- Merge commit: `83fa4ae`
- Calibration: this ADR was identified by `code-change-review`
  reproducer as finding "design decision about defaults" on the
  PR #34 diff (calibration pass #2 of 5+).
