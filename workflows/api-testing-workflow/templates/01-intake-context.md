# Stage 1 — Intake and Environment Assessment (template)

This is the `artifacts/api_testing_context.md` content scaffold. The agent
fills it from real evidence found in the target repo.

## Target summary

_Replace with one-paragraph description of the API target._

## Execution mode

(auto | black_box | gray_box | repo_only) — _and one-line justification_

## Detected framework

- Repository language:
- API framework:
- Package manager:
- Runtime/start command:
- Test framework in use:
- Existing API documentation:

## OpenAPI / Swagger availability

_File path or URL, or "not found" with the evidence used to confirm absence._

## Postman collection availability

_File path, or "not found"._

## Frontend / API client usage

_Files that consume the API, with paths._

## Auth mechanism

- Type (none | bearer | basic | cookie | oauth2 | api_key | unknown):
- Where it's enforced:
- Required env vars:

## Authorization model

_Notes on role / ownership / tenant boundaries, if visible._

## Required environment variables

_List with one-line description each._

## External dependencies

- Database:
- Cache:
- Queue / events:
- Third-party APIs:
- Other:

## Local run feasibility

- Installable locally: yes | no | unknown
- Reason:

## Deployed base URL

_URL or "not available"._

## Production-likeness

(production-like | staging | local | unknown)

## Safety constraints

(Repeat from run metadata; restate here for artifact self-containedness.)

## Blockers

_Concrete blockers for executing tests, with evidence._

## Assumptions

_Concrete assumptions made to make progress, with evidence._
