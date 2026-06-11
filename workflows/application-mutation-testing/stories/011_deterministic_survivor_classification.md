# Story 011: Deterministic Survivor Classification

## Goal

As the workflow, I need simple survivor patterns classified without LLM calls when deterministic rules are sufficient.

## Acceptance Scenarios

- Boundary mutations classify as `Missing edge case`.
- Literal replacements classify as `Missing assertion`.
- Error behavior mutations classify as `Missing error-path test`.
- Ambiguous mutations route to LLM review without a forced classification.
- Evidence-free mutations are blocked and not persisted as supported classifications.

## Executable Test Mapping

`tests/bdd/test_011_deterministic_survivor_classification.py`

## Done Criteria

- The taxonomy is enforced.
- Medium-or-higher deterministic rules persist.
- Ambiguous survivors route to LLM review.
- Every supported classification has evidence.
