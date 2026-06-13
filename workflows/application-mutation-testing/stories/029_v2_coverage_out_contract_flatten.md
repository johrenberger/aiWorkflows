# Story 029 — Flatten `coverage_out_dir` result contract

## Why

Story 025 (`--coverage-out`, PR #39) shipped with a result-dict contract
that's hard to consume cleanly:

- `coverage_out_dir` is set on the result ONLY in the mkdir-else branch
- `coverage_out_copied` is set only when there are new reports
- `coverage_out_error` is set only on failure
- A consumer of the result has to check all 3 fields, AND has to know
  that "field absent" can mean "not requested" or "mkdir failed" or
  "no new reports" depending on which field is missing

This is **code-review H1 + M2** from `tasks/2026-06-13-skill-progress-review/reports/code-review-report.md`.

## What's in this PR

Flatten the contract: **all three fields are always set, with consistent semantics**:

| field | when requested | when not requested |
|---|---|---|
| `coverage_out_dir` | `str` (the **resolved** path) | `None` |
| `coverage_out_copied` | `list[str]` of copied paths (empty if no new reports or copy failed) | `[]` |
| `coverage_out_error` | `str` (warning) on mkdir-fail or copy-fail; `None` on success | `None` |

Also fixes the **M2 inconsistency**: `run()` previously set its
top-level `coverage_out_dir` to the **input** path (could be
relative), while `coverage_generate` set its `coverage_out_dir` to
the **resolved** path. Now both are the resolved path (or `None`).
The top-level field in `run()` reads from
`coverage_generation["coverage_out_dir"]` so they can't disagree.

## End-to-end evidence

After the fix, every result that involves `coverage_out_dir` will
have **all three keys present, always**, with `None` / `[]` for
"not requested" cases. Consumers can do:

```python
result = orchestrator.coverage_generate(coverage_out_dir="/some/path")
assert result["coverage_out_dir"] == "/some/path"  # always present
assert isinstance(result["coverage_out_copied"], list)  # always a list
assert result["coverage_out_error"] is None  # or str on failure
```

…without needing to know whether the user requested it.

## Tests

Existing tests in `tests/test_025_v2_coverage_out_dir.py` need
updating:

- `test_coverage_generate_no_coverage_out_does_nothing` (line 75):
  currently asserts `"coverage_out_dir" not in result["generation"]`.
  Change to assert `result["generation"]["coverage_out_dir"] is None`
  and `result["generation"]["coverage_out_copied"] == []`.

Add 2 new tests:
- `test_coverage_generate_always_sets_all_three_fields`:
  regardless of `coverage_out_dir`, the result has all 3 keys.
- `test_run_top_level_coverage_out_dir_matches_generation`:
  when running with `--coverage-out`, the top-level
  `coverage_out_dir` in the `run()` result equals the one in
  `coverage_generation.coverage_out_dir` (both resolved).

## Out of scope

- The `result` dict typing (story 032).
- The unrelated M3 (CLI flag appears in non-run subcommand help).
- Pre-existing result-typing issues (story 032).
