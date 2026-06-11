# Story 016: Commit Gate

## Goal

Block commits by default and produce branch-safe, evidence-backed commit plans.

## Acceptance Scenarios

- Commit permission and validation evidence are both required.
- Unexpected production changes block planning.
- Protected branches produce a generated workflow branch.
- Fake execution persists a synthetic commit SHA.

## Executable Test Mapping

`tests/bdd/test_016_commit_gate.py`

## Done Criteria

- Commit, branch, and changed-file gates persist and render.
- No real commit is created by default.
