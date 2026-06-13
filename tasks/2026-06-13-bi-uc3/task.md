# Use case #3: Caching on PetService.findById with eviction (WITH backend-implementation skill)

## Goal

Add a cache to `PetService.findById` so that repeated lookups
for the same pet are served from cache. The cache is
**invalidated** when a pet is saved (added) or deleted.

## Acceptance criteria

1. `findPetById` is cached — second call with the same id
   returns the cached value without hitting the repository
2. `savePet` evicts the pet from the cache (because
   save can either insert a new pet or update an existing
   one)
3. `deletePet` evicts the pet from the cache
4. New tests: at least 2 covering cache behavior
5. All 237 baseline tests must still pass (this worktree
   starts from `master` so the baseline is 237 tests, not
   239 from UC1/UC2 which are on different branches)

## Methodology

Follow the `backend-implementation` skill workflow:
- profile: java-spring
- 7 steps: discovery gate, backend ownership, inspect
  patterns, tests, implement smallest safe change,
  validation-runner, handoff packet

## Constraints

- No new dependencies (use Spring's built-in
  `org.springframework.cache` and `@Cacheable`/`@CacheEvict`)
- No new Spring starters
- No cross-cutting concerns (no global CacheConfig if not
  needed)
- No destructive migrations

## Metrics to record

- Time elapsed
- Files added/modified
- Lines added (code + test)
- Build cycles to green
- Number of compile errors / test failures
- Number of issues hit that the skill guided/avoided
