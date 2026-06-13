# Baseline metrics — backend-implementation exercise (no skill)

## Use case #1
`GET /api/pets/{petId}/visits?from=YYYY-MM-DD&to=YYYY-MM-DD`

Returns all visits for a pet, optionally filtered by a date
range, sorted by visit date descending.

## Time

| Phase | Start | End | Duration |
|---|---|---|---|
| Total | 2026-06-13T19:17:30Z | 2026-06-13T19:23:06Z | **5 min 36 sec** |

## Code

| Metric | Value |
|---|---|
| Files added | 1 (test class) |
| Files modified | 6 |
| Lines added (code) | 68 |
| Lines added (test) | 142 |
| Lines added (total) | 210 |
| Lines removed | 1 |

### Per-file changes

| File | Lines added |
|---|---|
| `VisitRepository.java` (interface) | 4 |
| `JdbcVisitRepositoryImpl.java` | 22 |
| `JpaVisitRepositoryImpl.java` | 10 |
| `VisitRestControllerV1.java` (controller) | 25 |
| `ClinicService.java` (interface) | 1 |
| `ClinicServiceImpl.java` | 6 |
| `VisitRestControllerV1PetVisitsTests.java` (new test) | 142 |

## Tests

| Metric | Value |
|---|---|
| Tests before | 237 |
| Tests after | **239** |
| New tests | 2 |
| Failing tests | 0 |
| Build cycles to green | 2 (1 compile error: missing `Collection` import + type mismatch; 1 test run) |

## Issues / surprises

1. **Collection vs List type mismatch on `toVisitsDto`** — The
   `VisitMapper.toVisitsDto` returns `Collection<VisitDto>`
   but the controller method signature said `List<VisitDto>`.
   Fix: wrap in `new ArrayList<>(...)` to match the
   `ResponseEntity<List<VisitDto>>` return type. Took 1
   compile error to catch.

2. **3 repository impls to update, not 1** — `VisitRepository`
   is implemented by 3 different concrete classes
   (JPA, JDBC, Spring Data). I had to update 2 of them
   (JPA + JDBC) because the Spring Data interface uses
   Spring Data naming convention. **Gut-feel: I didn't
   initially realize there were 3 impls; discovered only
   when compile failed on the JPA impl.**

3. **V1 controllers implement an OpenAPI-generated interface
   `VisitsApi`** — adding a new method required either
   modifying the interface (re-generate from OpenAPI spec)
   or adding the method directly to the controller class
   (not in the interface). I chose the latter (gut-feel:
   smaller diff, doesn't require touching the spec).

4. **Date filter design choice** — chose to push the filter
   to the DB (`findByPetIdAndDateBetween`) rather than
   filter in-memory. Rationale: in-memory filter would
   break at scale, and Spring Data naming convention
   makes the query "free" once the method name is right.

## Deviations from existing patterns

1. **Returned `List<VisitDto>` instead of `Collection<VisitDto>`**
   in the new controller method signature. Existing methods
   use `Collection<VisitDto>` (because the mapper returns
   Collection). The List was needed for the type-safe
   `ResponseEntity<List<VisitDto>>` with sort-then-convert.
   Fix would be to use `Collection<VisitDto>` and just
   accept the `List` cast.

2. **Added to V1 (not V2)** — V2 is the modernized API,
   but V1 has the full Visit API already. Adding a
   `pets/{petId}/visits` endpoint to V1 is more useful
   because V1 is what the existing tests are wired against.
   V2 would require a new interface (`PetV2Api`).

## What the skill would have changed (preliminary)

Without having used the skill, my guesses for what the skill
might have caught/guided:

- **Pre-flight check** ("is this in the right place?") might
  have flagged that V2 is the preferred location for new
  endpoints. I added to V1.
- **Workflow step** ("does this match existing patterns?")
  might have flagged the `List<VisitDto>` vs
  `Collection<VisitDto>` deviation.
- **Validation step** ("are all 3 impls updated?") might
  have prompted me to check the SDJ impl from the start
  rather than after a compile error.
- **Handoff step** ("did you update the OpenAPI spec?")
  might have flagged that the new endpoint isn't in the
  OpenAPI spec because I bypassed the interface.

## Verdict

Baseline established: 5 min 36 sec, 210 lines, 2/2 tests
passing on second compile, all 237 prior tests still pass.

**No skill used.** Pure gut-feel implementation.

The next step (use case #2: soft-delete pattern) will be
done with the `backend-implementation` skill workflow, and
we'll compare.
