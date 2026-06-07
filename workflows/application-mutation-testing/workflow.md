# Application Mutation Testing Workflow

## Objective

Use mutation testing to identify weak assertions, missing edge cases, equivalent mutants, and false confidence in covered code.

## Inputs

```text
INPUT_GITHUB_REPO=<github-url>
INPUT_BRANCH=<optional branch>
MODE=implementation
ALLOW_PRODUCTION_FIXES=false
ALLOW_COMMIT=false
MAX_MUTATION_TARGET_FILES=5
MUTATION_TARGET_INITIAL=60
MUTATION_TARGET_MATURE=75
```

Optional inputs:

```text
TODO_test-coverage.md
coverage report
```

## Phases

### Phase 0 — Input Validation

Validate repository URL and optional branch.

### Phase 1 — Clone / Open Repository

Clone or open the repo, checkout branch if provided, and capture baseline metadata.

### Phase 2 — Consume Coverage Context

If available, read:

- `TODO_test-coverage.md`
- coverage reports
- CI test commands

Use this to select mutation targets.

### Phase 3 — Mutation Tool Detection

Detect available mutation tooling:

- Python: mutmut, cosmic-ray, mutatest.
- JavaScript/TypeScript: Stryker.
- Java: PIT.
- .NET: Stryker.NET.
- Go: go-mutesting or equivalent if present.

Do not install new mutation tooling unless explicitly allowed.

### Phase 4 — Target Selection

Select bounded target files:

1. Critical files already near or above coverage target.
2. Files with complex branching.
3. Files with many assertions but suspiciously weak checks.
4. Files recently improved by coverage workflow.
5. Files where mutation runtime is manageable.

Default limit:

```text
MAX_MUTATION_TARGET_FILES=5
```

### Phase 5 — Baseline Mutation Run

Run mutation testing only for selected targets.

Record:

- mutation command
- runtime
- killed mutants
- survived mutants
- timeout mutants
- equivalent candidates
- mutation score

### Phase 6 — Surviving Mutant Classification

Classify survived mutants as:

- Missing assertion.
- Missing edge case.
- Missing error-path test.
- Over-mocked behavior.
- Untested branch.
- Equivalent mutant.
- Production ambiguity.

### Phase 7 — Test Hardening Implementation

Implement targeted tests or assertion improvements.

Do not weaken tests.

### Phase 8 — Validation

Run:

1. Focused tests.
2. Mutation recheck for target files.
3. Broader test suite where feasible.

### Phase 9 — Ledger Finalization

Finalize `TODO_mutation-testing.md`.

### Phase 10 — Optional Commit

If `ALLOW_COMMIT=true` and validation passes:

```bash
git add <changed files>
git commit -m "test: strengthen assertions with mutation testing"
```
