# Application Test Coverage Workflow

## Objective

Close application test coverage gaps by implementing deterministic, maintainable tests until each eligible source file reaches at least 90% coverage, or until an evidence-backed blocker prevents completion.

## Inputs

```text
INPUT_GITHUB_REPO=<github-url>
INPUT_BRANCH=<optional branch>
MODE=implementation
COVERAGE_TARGET_PER_FILE=90
ALLOW_PRODUCTION_FIXES=false
ALLOW_COMMIT=false
MAX_FILES_PER_BATCH=5
```

## Phases

### Phase 0 — Input Validation

- Validate `INPUT_GITHUB_REPO` exists.
- Validate URL format.
- Capture optional branch.
- Capture workflow config values.

### Phase 1 — Clone / Open Repository

- Clone the repo if not present.
- Checkout branch if provided.
- Capture commit hash and working tree status.

### Phase 2 — Runtime Contract

- Create/update `TODO_test-coverage.md`.
- Record repo metadata.
- Record workflow settings.
- Add checkpoints.

### Phase 3 — Stack and Test Framework Detection

Detect from config and files:

- Language stack.
- Package manager.
- Test framework.
- Coverage tooling.
- CI workflows.

### Phase 4 — Baseline Test Execution

Run existing tests when feasible.

If baseline tests fail:

- Classify the failure.
- Record evidence.
- Do not hide or weaken failures.
- Continue only if safe.

### Phase 5 — Baseline Coverage Execution

Run coverage command from project config or framework convention.

Do not invent coverage values.

### Phase 6 — Eligible File Classification

Classify source files as:

- Eligible.
- Excluded.
- Blocked.

Every exclusion requires rationale.

### Phase 7 — Per-File Coverage Gap Mapping

Create a table:

```markdown
| File | Baseline | Target | Final | Status | Notes |
|---|---:|---:|---:|---|---|
```

Target for every eligible file:

```text
>=90% line coverage
```

Where branch coverage is supported, critical files should also target:

```text
>=90% branch coverage
```

### Phase 8 — Work Batch Selection

Prioritize:

1. High-risk files below 50%.
2. Files with 0% coverage.
3. Critical path files.
4. Branch-heavy logic.
5. Files near 90% needing small additions.

Default batch limit:

```text
MAX_FILES_PER_BATCH=5
```

### Phase 9 — Test Design

For each selected file, define:

- Behaviors.
- Happy paths.
- Edge cases.
- Error paths.
- Boundary values.
- Fixtures/factories/builders.
- Mocking strategy.
- Determinism strategy.

### Phase 10 — Test Implementation

Implement tests and supporting test utilities.

Allowed by default:

- Test files.
- Fixtures.
- Factories/builders.
- Test utilities.
- Test config.
- Coverage config.
- CI test/coverage commands.

Production code changes are prohibited unless `ALLOW_PRODUCTION_FIXES=true`.

### Phase 11 — Focused Validation

Run tests for changed modules first.

### Phase 12 — Per-File Coverage Recheck

Re-run coverage.

Update per-file coverage table.

### Phase 13 — Repair Loop

Repair failures up to:

```text
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
```

Then document blocker.

### Phase 14 — Full Validation

Run broader validation when feasible:

- Full test suite.
- Coverage command.
- Lint/typecheck if configured.
- CI-equivalent command if known.

### Phase 15 — Ledger Finalization

Finalize `TODO_test-coverage.md` with:

- Commands run.
- Files changed.
- Coverage before/after.
- Remaining gaps.
- Blockers.
- Commit-ready summary.

### Phase 16 — Optional Commit

If `ALLOW_COMMIT=true` and validation passes:

```bash
git add <changed files>
git commit -m "test: improve per-file coverage"
```
