# Story 014: Validation Gates

## Goal

As the workflow, I need machine-checkable validation gates so progress and commit eligibility are evidence-backed.

## Acceptance Scenarios

- Complete structured evidence passes required gates.
- Missing tool evidence fails unless a blocker documents it.
- Evidence-free survivor classification fails.
- Commit remains blocked by default and whenever required gates fail.

## Executable Test Mapping

`tests/bdd/test_014_validation_gates.py`

## Done Criteria

- Gates `MT-VAL-1` through `MT-VAL-12` are evaluated and persisted.
- PASS and BLOCKED require evidence.
- Commit eligibility is deterministic.
