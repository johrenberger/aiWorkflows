# Output Rules

## Ledger Rules

Each workflow must maintain exactly one primary ledger:

- `application-test-coverage` -> `TODO_test-coverage.md`
- `application-mutation-testing` -> `TODO_mutation-testing.md`

### Project Root

The ledger lives at the **root of the project being analyzed**, not at
the root of the input repository. For a single-project repository, the
project root is the repository root, so the ledger lives at
`<repo_root>/<ledger_name>`. For a repository that contains the target
project as a subdirectory, the ledger lives at
`<subpath>/<ledger_name>`.

Why this matters: when the input repository is a monorepo or workflow
bundle that contains multiple projects (e.g. `aiWorkflows` containing
both `skill-governance-pipeline/` and `workflows/repo-discovery-analyzer/`
as separate projects), writing the ledger at the input repository root
mixes artifacts from unrelated projects and makes the ledger hard to
find. Writing the ledger inside the project being analyzed keeps each
project's artifacts isolated and discoverable.

How to determine the project root:

1. If `MODULE_LIST` is set to a single subpath, the project root is
   that subpath.
2. Otherwise, the project root is the smallest directory that contains
   all of the project's source files (typically the same directory
   the build system operates on, e.g. `src/` lives directly inside it).
3. If ambiguous, record the choice in the ledger's
   `TC-CTX-1 [Repository]` field with the path used and a one-line
   rationale, and proceed.

The `PROJECT_ROOT` input is exposed in workflow prompts so the LLM has
an unambiguous target. When the LLM has to make this decision itself
(legacy behavior), it MUST record the choice in the ledger.

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
