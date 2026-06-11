# Story 009: Mutation Result Normalization

## Goal

As the workflow, I need mutation tool outputs normalized into a common result model so later survivor analysis is bounded and evidence-based.

## Acceptance Scenarios

- Given mutmut text output, when normalized, then killed, survived, and timeout evidence is recorded.
- Given Stryker JSON or PIT XML, when normalized, then common mutant statuses are used.
- Given insufficient count evidence, when normalized, then the score remains unavailable.

## Executable Test Mapping

`tests/bdd/test_009_mutation_result_normalization.py`

## Done Criteria

- Fixture parsers produce common normalized models.
- Scores are computed only from evidence-backed counts.
- Results and survivors persist and render.
