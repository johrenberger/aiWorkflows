# Task: 2026-06-13-ii-stack

## Goal

Exercise the `integration-implementation` skill against a
Node/Express proxy that calls the re-baselined
`johrenberger/spring-petclinic-rest` fork as a downstream
service. Promote the skill from `draft` to `usable` (or
higher) on the strength of 3 use cases.

## Use case plan

| # | Description | Skill |
|---|---|---|
| UC1 | GET /proxy/pets/:id/visits with date filtering | ❌ no skill (baseline) |
| UC2 | POST /proxy/visits with retry + structured error handling | ✅ with skill |
| UC3 | GET /proxy/pets?type=dog&limit=10 with caching + invalidation | ✅ with skill |

## Stack

- Node 22 (or 24, what's available)
- Express 4
- Axios 1
- Jest + supertest for integration tests
- Target downstream: `johrenberger/spring-petclinic-rest` on `localhost:9966`

## Repo

- New repo at `johrenberger/petclinic-proxy` (NOT yet created)
- Will be re-baselined to remove any upstream links

## Cross-stack validation

After the 3 use cases, re-run 5 of the 14 `validated` skills
(security-review, observability-review, code-change-review,
validation-runner, runbook-authoring) against the new
codebase to confirm they work cross-stack.
