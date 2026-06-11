# Story 015: Mutation Recheck

## Goal

As the workflow, I need a scoped mutation recheck so improvement and remaining survivors are evidence-backed.

## Acceptance Scenarios

- Recheck preserves baseline tool and target scope.
- Improved and unchanged fixture results persist before/after evidence.
- Timeouts and missing baselines fail safely.
- Remaining survivors and score deltas render from state.

## Executable Test Mapping

`tests/bdd/test_015_mutation_recheck.py`

## Done Criteria

- Fake recheck planning/execution persists.
- Deltas exist only when both scores exist.
- Remaining survivors remain visible.
