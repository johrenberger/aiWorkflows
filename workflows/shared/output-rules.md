# Output Rules

## Ledger Rules

Each workflow must maintain exactly one primary ledger:

- `application-test-coverage` -> `TODO_test-coverage.md`
- `application-mutation-testing` -> `TODO_mutation-testing.md`

The ledger must include:

- Context.
- Execution log.
- Commands run.
- Commands skipped.
- Evidence-backed findings.
- Checkpoints.
- Files changed.
- Test cases added.
- Validation results.
- Remaining gaps.
- Blockers.
- Commit-ready summary.

## Task ID Rules

Every actionable item must use a stable task ID.

Recommended prefixes:

```text
TC-* = test coverage workflow task
MT-* = mutation testing workflow task
OBS-* = observability/logging item
VAL-* = validation item
BLK-* = blocker item
```

## Status Values

Use only these status values for per-file and task reporting:

```text
PASS
PARTIAL
BLOCKED
EXCLUDED
DEFERRED
FAIL
NOT_RUN
```

## Coverage Exclusion Rules

A file may be excluded only with explicit rationale.

Allowed exclusion examples:

- Generated file.
- Type declaration only.
- Static asset.
- Vendor/build artifact.
- Pure constants with no runtime behavior.
- Framework boilerplate with no application-owned logic.

Hard-to-test is not a valid exclusion by itself.
