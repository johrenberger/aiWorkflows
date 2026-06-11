# Story 006: Coverage Ingestion

## Goal

As the workflow, I need to consume coverage context so mutation targets are selected where mutation testing is useful.

## Acceptance Scenarios

- Given multiple coverage formats, when ingestion runs, then the documented priority is used.
- Given Cobertura XML or LCOV, when ingestion runs, then file-level coverage is extracted.
- Given no artifacts, when ingestion runs, then missing coverage is explicit.

## Executable Test Mapping

`tests/bdd/test_006_coverage_ingestion.py`

## Done Criteria

- Coverage priority is deterministic.
- XML and LCOV fixtures parse.
- Missing coverage is explicit.
- Coverage summaries persist and render.
