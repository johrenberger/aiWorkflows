# Task: 2026-06-13-bi-baseline

## Goal

**Establish a baseline for the `backend-implementation` skill promotion.**

Implement use case #1 on the PetClinic-REST fork *without* using
the skill. Record metrics so we can compare against a
"with-skill" attempt later.

## Use case #1

**Add a new REST endpoint:**

`GET /api/pets/{petId}/visits?from=YYYY-MM-DD&to=YYYY-MM-DD`

Returns all visits for a given pet, optionally filtered by
a date range. Sorted by visit date descending.

### Acceptance criteria

- Endpoint exists at `/api/pets/{petId}/visits` (V1 or V2 — pick what fits)
- Accepts optional `from` and `to` query params (ISO 8601 dates)
- Returns empty list if no visits match (NOT 404)
- Returns 404 if pet doesn't exist
- Each visit returned has at least: id, petId, visitDate, description
- 2 tests:
  1. Returns visits for a pet, sorted by date desc
  2. Filters by date range correctly
- Existing 237/237 tests still pass

## In scope

- New endpoint (controller + service method)
- Date range filtering (repository query)
- 2 tests
- 1 PR (after skill-exercise comparison)

## Out of scope

- Pagination (use case #4)
- Caching (use case #3)
- Soft-delete (use case #2)
- Authentication changes

## Success

- Endpoint works (verified by curl/MockMvc)
- 2 new tests pass
- All 237 existing tests still pass
- PR opened
- Metrics recorded in this workspace

## Metrics to record

| Metric | Value |
|---|---|
| Time taken (minutes) | ? |
| Lines of code added | ? |
| Lines of test code added | ? |
| Number of files modified | ? |
| Number of files added | ? |
| Build cycles to green | ? |
| Issues / surprises | ? |
| Deviations from existing patterns | ? |
