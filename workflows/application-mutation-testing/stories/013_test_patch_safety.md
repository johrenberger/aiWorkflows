# Story 013: Test Patch Safety

## Goal

As the workflow, I need safe test patch validation and controlled application so proposed changes cannot silently weaken tests or modify production code.

## Acceptance Scenarios

- Test-only patches require explicit test-change permission.
- Production and mixed patches fail closed by default.
- Assertion removal and malformed patches are rejected with evidence.
- Accepted patches can be applied and reverted in a synthetic workspace.

## Executable Test Mapping

`tests/bdd/test_013_test_patch_safety.py`

## Done Criteria

- Unified diffs parse deterministically.
- Weakening and file-scope checks persist.
- Apply/revert is controlled and evidence-backed.
