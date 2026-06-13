# ADR 0002: JaCoCo path-matching — additive regression net, not a fix

* **Status:** Accepted (2026-06-11)
* **Context:** Story 022 of v2 (test-factory) work, PR #36
* **Deciders:** software-engineer, test-automation, code-review-agent
* **Tags:** v2, jacoco, path-matching, regression-testing

## Context and Problem Statement

When v2 ingests a JaCoCo `jacoco.xml`, it produces `CoverageRecord`
entries keyed on JaCoCo's `org/example/Foo.java`-style paths
(the parser joins `<package>` and `<sourcefile>` from the XML).
v2's `risk_scores.json` is keyed on v2's own inventory file
paths (e.g. `common/src/main/java/org/example/Foo.java`).

The join between these two path forms happens in two places:

1. **Coverage baseline** (`coverage_baseline.json`):
   `orchestrator._collect_coverage_records` calls
   `_merge_coverage_records(coverage, inventory_paths)`, which
   uses `_normalize_coverage_path` to map each JaCoCo path to
   an inventory path via suffix matching.
2. **Risk score step** (`risk_scores.json`):
   `orchestrator.score` joins on `coverage_rows.get(row["path"])`.

Reproduced on Broadleaf 2026-06-13: 5/765 risk_scores records had
non-zero `line_coverage`. The original hypothesis was that the
5/765 was a path-matching bug in `_normalize_coverage_path`.

Investigation showed the root cause was **not** the
`_normalize_coverage_path` algorithm — that one is fine. The
root cause was that the previous `test-factory run` was invoked
with `--module admin`, which scopes the inventory to `admin/`
files only. The coverage report was for the `common/` module,
so its files did not appear in v2's inventory at all, and the
join (correctly) had nothing to join them to.

The 5/765 was a **scoping artifact**, not a path-matching bug.
But the original premise of "5/765 looks like a path bug"
isn't a crazy premise — it COULD have been a path bug. How do
we prevent future regression while not breaking the working
join?

## Considered Options

1. **Ship `resolve_jacoco_paths` as a regression net (chosen)**:
   Add a new helper that does the JaCoCo→inventory path resolution
   for a wider set of cases than `_normalize_coverage_path` (the
   current helper). Ship it as a NEW function, leaving
   `_normalize_coverage_path` in place. Tests pin the contract.
2. **Replace `_normalize_coverage_path` with `resolve_jacoco_paths`**:
   Tempting, but the working join is in production. If the new
   helper has a subtle bug, we break a working join. The
   regression net is the additive path.
3. **Just add tests, no new helper**: The current algorithm
   works. Tests pin the contract; we move on.
4. **Switch to a different algorithm entirely** (e.g. hash-based
   join): Out of scope. The current suffix-matching works.

## Decision Outcome

**Chosen option: 1 (additive regression net).**

The reframing matters: the original premise ("fix 5/765
path-matching bug") was wrong. The 5/765 was a scoping
artifact. But the *premise* (path matching could be a bug) is
right — it's a class of bug that's easy to introduce and hard
to catch in code review. The fix is to add a wider-coverage
helper that catches the class, ship it as a regression net,
and have the test suite pin the contract.

The additive path (option 1) over the replacement path
(option 2) is a **risk-management decision**: the working
join is in production, breaking it would silently corrupt
risk scores across the board. The new helper is opt-in; if
it has a bug, we don't lose anything.

## Consequences

### Positive
- The working join is preserved. The 5/765 was a scoping
  artifact; it stops happening once users understand the
  `--module` scoping.
- A new helper (`resolve_jacoco_paths`) covers a wider set of
  path-matching cases (basename fallback, `.java`/`.kt`
  extension handling, Maven module roots via on-disk `pom.xml`).
- 5 BDD tests pin the contract for both the working join and
  the new helper's behavior. Future regressions are caught at
  test time.

### Negative
- Two helpers exist (`_normalize_coverage_path` and
  `resolve_jacoco_paths`). Documentation must explain which
  to use when.
- The new helper is currently unused in the production join
  path. If it has a bug, we won't catch it at runtime. The
  tests catch it at test time, but runtime is the ground truth.

### Neutral
- The original "5/765" bug (the scoping artifact) is not
  fixed by this story. It's a documentation fix in the
  `--module` help text. Story 023 (`--module auto` resolution)
  addresses it more substantively.

## Follow-up

- (PR #36) `resolve_jacoco_paths` shipped as additive helper
  with 5 BDD tests.
- (future) Once `resolve_jacoco_paths` is exercised in
  production, deprecate `_normalize_coverage_path`.
- (story 023) `--module auto` resolution makes the scoping
  artifact less likely to occur.

## More Information

- Story markdown: `workflows/application-mutation-testing/stories/022_v2_jacoco_path_matching.md`
- PR: https://github.com/johrenberger/aiWorkflows/pull/36
- Merge commit: `7b0b668`
- Calibration: this ADR was identified by `code-change-review`
  reproducer as finding "design decision about regression net
  vs replacement" on the PR #36 diff (calibration pass #3 of 5+).
- **Lesson logged in memory:** the original premise of a bug
  report can be wrong. Investigation (not just code reading)
  is required before shipping a "fix."
