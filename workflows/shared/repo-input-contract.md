# Repository Input Contract

## Required Input

```text
INPUT_GITHUB_REPO=<github-url>
```

The workflow must accept a GitHub repository URL as the target application.

## Optional Inputs

```text
INPUT_BRANCH=<branch-name>
MODE=implementation|analysis
COVERAGE_TARGET_PER_FILE=90
ALLOW_PRODUCTION_FIXES=false
ALLOW_COMMIT=false
ALLOW_DEPENDENCY_INSTALL=false
ALLOW_CI_CHANGES=true
ALLOW_TEST_CONFIG_CHANGES=true
MAX_FILES_PER_BATCH=5
MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2
MAX_BASELINE_TEST_MINUTES=20
ENABLE_TESTABILITY_CLASSIFICATION=true
MULTI_MODULE_MODE=off|auto|explicit
MODULE_LIST=<comma-separated module names>
```

## Repository Handling

The workflow must:

- Clone the repository if it is not already present locally.
- Checkout `INPUT_BRANCH` if provided.
- Capture the current commit hash.
- Capture working tree status before changes.
- Avoid destructive git operations.
- Never force push.
- Never reset user changes unless explicitly authorized.

## Required Baseline Metadata

Record the following in the workflow ledger:

- Repository URL
- Branch
- Commit hash
- Working tree status
- Timestamp
- Detected package manager
- Detected language stack
- Detected test framework
- Commands attempted
- Commands skipped and why
