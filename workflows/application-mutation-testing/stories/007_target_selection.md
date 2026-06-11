# Story 007: Mutation Target Selection

## Goal

As the workflow, I need bounded deterministic target selection so mutation execution is fast and focused.

## Acceptance Scenarios

- Given more eligible files than the configured cap, when selection runs, then the cap is enforced.
- Given generated or vendor paths, when selection runs, then they are excluded with rationale.
- Given differing coverage and complexity, when scoring runs, then ordering is deterministic.
- Given missing coverage and fallback enabled, when selection runs, then source files remain eligible.

## Executable Test Mapping

`tests/bdd/test_007_target_selection.py`

## Done Criteria

- Eligibility and scoring are deterministic.
- Exclusions and selections persist.
- Ledger renders selected targets.
