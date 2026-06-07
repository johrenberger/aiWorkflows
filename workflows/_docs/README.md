# `_docs/` — Reusable Patterns

This directory contains **reusable patterns and lessons** that emerged from running the workflows. They are not workflow specs themselves — they are reference material for anyone writing or running the workflows.

The leading underscore on `_docs/` marks it as metadata, not a workflow (the workflow loader should ignore it).

## Contents

- **[test-pattern-wrapped-commit.md](test-pattern-wrapped-commit.md)** — for testing exception handlers in code that uses a real database. Generalizable across ORMs and HTTP frameworks.

## Adding a new pattern

1. Write the file with a clear "When to use" section at the top.
2. Include working code that was actually used in a real run.
3. If the pattern came from a debugging session, link to the PR that adopted it.
4. Add it to the index above.
