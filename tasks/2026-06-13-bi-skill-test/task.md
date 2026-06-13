# Use case #2: Soft-delete pattern on Visit entity (WITH backend-implementation skill)

## Goal

Add a soft-delete pattern to the `Visit` entity in
spring-petclinic-rest:
- Add `deleted_at` (nullable LocalDateTime) column to `Visit`
- `VisitRepository.delete(visit)` becomes a soft delete
  (sets `deleted_at` instead of removing the row)
- `findByPetId` and `findByPetIdAndDateBetween` filter out
  soft-deleted visits
- `findById` returns `null` for soft-deleted visits
- `Visit.deleted` computed property

## Acceptance criteria

1. Adding a `delete_at` column to `Visit` (nullable)
2. `VisitRepository.delete(visit)` sets `deleted_at` instead
   of physically removing the row
3. All read queries (`findById`, `findByPetId`,
   `findByPetIdAndDateBetween`, `findAll`) exclude
   soft-deleted rows
4. `Visit.isDeleted()` helper method
5. New tests: at least 2 covering soft-delete behavior
6. All 239 prior tests must still pass

## Methodology

Follow the `backend-implementation` skill workflow
(packages -> test-first inspection -> smallest safe change
-> validation-runner -> handoff packet).

## Metrics to record (same as use case #1)

- Time elapsed
- Files added/modified
- Lines added (code + test)
- Build cycles to green
- Number of compile errors / test failures
- Number of issues hit that the skill guided/avoided
- Number of handoff packets produced

## State

- Branch: feature/visit-soft-delete
- Started: <to fill>
- Ended: <to fill>
