# Story 012: LLM Contracts

## Goal

As the workflow, I need schema-validated LLM request and response contracts so fake LLM work is bounded and auditable.

## Acceptance Scenarios

- Classification requests contain the exact taxonomy, constraints, packet, and schema version.
- Valid evidence-backed responses are accepted.
- Missing evidence, unknown classifications, and score invention are rejected.
- The fake client returns deterministic configured responses without network access.

## Executable Test Mapping

`tests/bdd/test_012_llm_contracts.py`

## Done Criteria

- Request and response schemas exist.
- The fake client and validator are deterministic.
- Accepted and rejected outcomes persist separately.
- No real LLM calls or patch generation exist.
