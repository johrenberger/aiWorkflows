# Implementation Guardrails

## Allowed Changes by Default

- Test files.
- Test fixtures.
- Test factories/builders.
- Test utilities.
- Test configuration.
- Coverage configuration.
- CI test/coverage commands.
- Workflow ledger files:
  - `TODO_test-coverage.md`
  - `TODO_mutation-testing.md`

## Restricted Changes by Default

Do not modify production code unless explicitly enabled.

Restricted by default:

- Application source behavior.
- Public interfaces.
- Business logic.
- Validation rules.
- Auth/security logic.
- Database schema or migrations.
- Dependency upgrades.
- Broad refactors.

## Production Bug Handling

If a new test exposes a production bug:

1. Keep the failing test if it correctly captures expected behavior.
2. Document the bug in the ledger.
3. Stop modifying production code unless `ALLOW_PRODUCTION_FIXES=true`.
4. Provide a recommended fix as a patch proposal if production changes are not allowed.

## Repair Loop Limit

For any single failure class:

```text
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
```

After two failed repair attempts:

- Stop repairing that failure.
- Record the blocker.
- Continue with independent work if safe.

## Test Quality Rules

All implemented tests must:

- Follow AAA: Arrange, Act, Assert.
- Use descriptive behavior-based names.
- Cover happy paths, edge cases, error paths, and boundaries.
- Avoid arbitrary sleeps.
- Avoid over-mocking internals.
- Mock external dependencies at boundaries.
- Use fixtures/factories/builders where appropriate.
- Be deterministic and isolated.
- Preserve original test intent.
- Never weaken assertions just to make tests pass.
