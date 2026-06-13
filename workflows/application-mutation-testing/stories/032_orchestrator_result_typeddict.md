# Story 032 — TypedDict for `orchestrator.coverage_generate` and `run` results

## Why

Code-review P1 from `tasks/2026-06-13-skill-progress-review/reports/code-review-report.md`:

> `orchestrator.py` `result` is untyped — the `coverage_generate` function
> returns `dict[str, Any]`. A TypedDict or dataclass would be much better.
> Pre-existing, not introduced by story 025; story 025 inherits the problem.

The 4 follow-up stories (025, 029, 031, 033) have all added fields to
the `coverage_generate` result. Each one had to discover the field
shapes by reading the implementation. A TypedDict would:

1. Document the contract in code (the linter / IDE can flag
   `result["foo"]` when `foo` isn't in the TypedDict).
2. Catch typos at type-check time (e.g. `coverage_out_di`).
3. Make the field set visible to consumers without reading the source.
4. Provide a single place to find "what's in the result."

## Scope (this PR)

This story is a **focused** typing effort, not a full migration:

1. **`CoverageGenerateResult` TypedDict** for the inner `generation`
   block of `coverage_generate()`. Includes:
   - `status: str`  ("completed" | "timeout" | "missing_binary" | "skipped" | "no_report_written")
   - `command: str | None`  (rendered command line)
   - `exit_code: int | None`  (subprocess return code)
   - `stdout: str`
   - `stderr: str`
   - `timeout_seconds: int`
   - `preflight_findings: list[dict[str, str]]`
   - `new_reports: list[str]`  (post-run mtime-detected reports)
   - `warning: str | None`  (set when status="no_report_written")
   - `coverage_out_dir: str | None`  (story 029: always present)
   - `coverage_out_copied: list[str]`  (story 029: always present)
   - `coverage_out_error: str | None`  (story 029: always present)
   - `reason: str | None`  (set when status="skipped")

2. **`RunResult` TypedDict** for the top-level `run()` return:
   - `status: str`
   - `module_scope: str`
   - `coverage_generation: CoverageGenerateResult | None`
   - `coverage_out_dir: str | None`  (story 029: matches nested)

3. **Update `coverage_generate()` and `run()` return type
   annotations** to use the TypedDicts. The runtime values
   don't change (TypedDicts are dicts at runtime).

4. **Add a runtime assertion in tests** that the result is
   `isinstance(result, dict)` (it's a TypedDict so isinstance
   still returns True) and that the key set is a superset of
   the TypedDict. This catches accidental field deletions.

5. **Add a type-check test** that uses `mypy --strict` on
   the orchestrator (or a focused subset) to verify the
   TypedDicts match actual usage. If mypy is not available
   in the test environment, skip with a clear message.

## Out of scope

- **Other methods** (`scan`, `validate`, `mutate`, `branch`,
  `commit`, `report`) return untyped dicts. Each could get a
  TypedDict in a follow-up story. This story is focused on
  the two methods touched by stories 020-031.
- **No** migration of internal helpers (e.g. `_collect_coverage_records`
  returns `list[CoverageRecord]`, which IS typed — keep it).
- **No** `dataclass` migration (TypedDicts preserve the
  existing `dict` return type so consumers don't break).
- The pre-existing `_decode_json_maybe` and other internals.

## Tests

- 3 new tests in `test_032_orchestrator_result_typeddict.py`:
  - `test_coverage_generate_result_has_all_typed_fields`
  - `test_run_result_has_all_typed_fields`
  - `test_typeddict_runtime_isinstance_dict` (TypedDicts are dicts
    at runtime, so `isinstance(result, dict)` is True).

## Why a TypedDict, not a dataclass

- TypedDicts don't change the runtime type — consumers reading
  `result["coverage_out_dir"]` still work.
- Dataclasses would require a migration of every consumer
  (downstream test code, CLI output, etc.) from `result["x"]`
  to `result.x`. The risk-reward isn't worth it for a
  pre-existing untyped return.
- The Python ecosystem is comfortable with TypedDict for
  "shape-of-dict" documentation. This is a typing-only change.
