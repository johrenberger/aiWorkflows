# Story 017: End-to-End Synthetic Repository

## Goal

Prove the deterministic workflow from intake through final summary without external tools.

## Acceptance Scenarios

- Report-only mode renders state and ledger without writes to the source fixture.
- Fake implementation applies a safe test patch in an isolated copy.
- Survivors, classifications, focused tests, recheck, validation, and commit planning persist.

## Executable Test Mapping

`tests/bdd/test_017_end_to_end_synthetic_repo.py`

## Done Criteria

- Both synthetic modes complete without network, real mutation tools, or real LLMs.
