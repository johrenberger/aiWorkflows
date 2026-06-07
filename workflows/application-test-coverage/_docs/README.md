# `application-test-coverage/_docs/`

Reusable patterns and operational procedures specific to the **test coverage workflow**. These are reference material for anyone running or extending the workflow — not workflow specs themselves.

The leading underscore on `_docs/` marks it as metadata, not a workflow (a future workflow-loader can ignore this directory without explicit configuration).

## Contents

- **[multi-module-orchestration.md](multi-module-orchestration.md)** — the 3-role split (discoverer / test-writer / coverage-manager), file-claim protocol, branch-per-module isolation, repair-loop failure handling, and resource budget for BroadleafCommerce-class targets.

## Cross-references

- **`workflows/_docs/`** (the repo-wide directory) has patterns generalizable across all workflows
- **`workflows/shared/concurrency.md`** has the cross-workflow rules for spawning sub-agents (this directory's orchestration file references it)
- **`workflows/shared/repo-input-contract.md`** lists the optional inputs the coverage workflow reads

## Adding a new file

1. Write the file with a clear "When to use" section at the top.
2. Reference the cross-cutting `workflows/shared/` rules when applicable.
3. Update this index.
