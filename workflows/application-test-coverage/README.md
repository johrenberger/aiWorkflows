# Application Test Coverage Workflow

## Purpose

This workflow accepts a GitHub repository URL, analyzes its current test coverage, implements tests to close gaps, and targets **90% coverage per eligible source file**.

## Primary Output

```text
TODO_test-coverage.md
```

The ledger documents analysis, implementation, validation, coverage results, and remaining gaps.

The ledger lives at the **root of the project being analyzed**, not at
the root of the input repository. For a single-project repository,
that is the repository root. For a repository that contains the target
project as a subdirectory (e.g. `aiWorkflows` → `skill-governance-pipeline/`),
that is the project subpath. See
[`workflows/shared/output-rules.md`](../shared/output-rules.md#project-root)
for the project-root rule and `TC-VAL-25` in `validation.md` for the
gate that enforces it.

## Default Mode

```text
MODE=implementation
```

## Success Criteria

The workflow succeeds when:

1. The repository is cloned or opened from the provided GitHub URL.
2. The stack and test framework are detected from evidence.
3. Baseline tests are run or blockers are documented.
4. Baseline coverage is run or blockers are documented.
5. Eligible files are classified.
6. Each eligible source file has a per-file coverage status.
7. Tests are implemented for selected coverage gaps.
8. Focused tests pass.
9. Coverage improves toward or reaches 90% per file.
10. Final validation results are recorded.
11. `TODO_test-coverage.md` is complete and recoverable.

## See also

- [Project notes](../PROJECT.md) — smoke-test history, layout convention
- [Reusable test patterns](../_docs/) — wrapped-commit, etc.
  - [Wrapped-commit pattern](../_docs/test-pattern-wrapped-commit.md) — for testing DB exception handlers
