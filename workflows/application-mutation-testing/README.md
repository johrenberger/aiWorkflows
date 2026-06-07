# Application Mutation Testing Workflow

## Purpose

This workflow accepts a GitHub repository URL and uses mutation testing to strengthen test effectiveness. It is intended to run after `application-test-coverage`, but it can run independently.

## Primary Output

```text
TODO_mutation-testing.md
```

## Role

Coverage answers: "Was the code executed?"

Mutation answers: "Would the tests catch meaningful behavioral changes?"

## See also

- [Project notes](../PROJECT.md) — smoke-test history, layout convention
- [Reusable test patterns](../_docs/) — wrapped-commit, etc.
  - [Wrapped-commit pattern](../_docs/test-pattern-wrapped-commit.md) — for testing DB exception handlers
