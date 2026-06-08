# Profile Tiers — Per-Profile Behavior Matrix

This doc details the three generation profiles and what each one is allowed to touch. The matrix matches `workflow.md` and the CTG-VAL-* gates in `validation.md`.

## The matrix

| Action | `safe` | `balanced` | `aggressive` |
|---|:---:|:---:|:---:|
| Add new test files | ✅ | ✅ | ✅ |
| Add new fixtures in `src/test/resources/`, `testdata/`, etc. | ❌ | ✅ | ✅ |
| Add test base classes (e.g. `AbstractIntegrationTest.java`) | ❌ | ✅ | ✅ |
| Add test config (e.g. `application-test.yml`, `pytest.ini` additions) | ❌ | ✅ | ✅ |
| Add test-only dependencies (Maven `<scope>test</scope>`, npm `devDependencies`, etc.) | ❌ | ✅ | ✅ |
| Modify production source (`src/main/`, `src/`, `lib/`) | ❌ | ❌ | ✅ (single-purpose, revertible commits only) |
| Add `protected` accessors to production classes | ❌ | ❌ | ✅ |
| Add constructor injection for `@Autowired` fields | ❌ | ❌ | ✅ |
| Add `@VisibleForTesting` annotations | ❌ | ❌ | ✅ |
| Extract methods for testability | ❌ | ❌ | ✅ |
| Add `.github/workflows/test-generation-validation.yml` | ❌ | ❌ | ✅ |
| Add `package.json` runtime dependencies (not dev) | ❌ | ❌ | ✅ |
| Modify existing CI files | ❌ | ❌ | ❌ (always — we add a new one or leave CI alone) |
| Push branch to origin | ✅ | ✅ | ✅ |
| Open PR on the target repo | ✅ | ✅ | ✅ |
| Auto-merge the PR | ❌ | ❌ | ❌ (always) |

## Profile selection

| Situation | Profile |
|---|---|
| Auditing a third-party repo where I have no commit rights | `safe` |
| Working on my own repo, want to add test scaffolding without touching production | `safe` |
| Working on my own repo, the tests need new fixtures or test deps | `balanced` |
| Working on a legacy repo where the source is hard to test as-is, and I'm willing to add testability hooks | `aggressive` |
| First contact with a repo (don't know the conventions yet) | `safe` + `DRY_RUN=true` |
| Running in CI as part of a test-generation pipeline | `safe` (CI is not the place to touch production) |

## What each profile emits in `detected-stack.json`

All profiles emit the same `detected-stack.json` schema. The difference is in what the generator is *allowed* to do with the detection, not what it detects.

## What each profile emits in `templates-applied.json`

All profiles emit the same `templates-applied.json` schema. The difference is in the imports needed and the testability assumptions.

For example, a Java test in `safe` profile will use only public APIs and will not import any new dependencies. The same test in `aggressive` profile may import Mockito's `ReflectionTestUtils` if the source has `@VisibleForTesting` fields.

## What each profile emits in `test-execution-results.json`

All profiles emit the same schema when Phase 7 runs. The only difference is in the `repair_attempts` and `final_outcome` fields:

- `safe` profile: 0 production-code repairs (impossible by construction)
- `balanced` profile: 0 production-code repairs; test config repairs possible
- `aggressive` profile: production-code repairs possible (e.g. adding a `protected` accessor and re-running the test)

## Upgrading profiles

If you start with `safe` and find that gaps are being deferred with `needs_testability_hook`, you can re-run with `aggressive` and `ALLOW_PRODUCTION_FIXES=true`. The workflow will:

1. Re-detect the stack (Phase 3) — same as before.
2. Re-select gaps (Phase 4) — same gaps, but the previously-deferred ones are now eligible.
3. Re-assign templates (Phase 5) — the templates may now include testability hooks.
4. Re-generate (Phase 6) — the previously-deferred gaps are now generated, possibly with production-code changes.
5. Open a new PR (Phase 8) — the new PR is on a new branch, so both PRs can coexist.

The `safe` PR and the `aggressive` PR are independent. The user can merge one, both, or neither.

## Downgrading profiles

If you start with `aggressive` and the PR is too large (production-code changes are too invasive), you can:

1. Close the `aggressive` PR.
2. Re-run with `safe` — the same gaps will be generated, but with no production-code changes.
3. The result is a smaller, safer PR. The previously-deferred gaps (with `needs_testability_hook`) will be deferred again.
4. Open follow-up issues for each testability improvement, and tackle them in separate `aggressive` runs.

## When to pick which

The decision tree:

```
Do you own the repo AND have commit rights AND want to improve testability?
  → aggressive
Do you own the repo AND have commit rights but want to limit blast radius?
  → balanced
Do you own the repo but want zero source impact?
  → safe
Are you auditing a repo you don't own?
  → safe + DRY_RUN=true
Is this the first run against a repo?
  → safe + DRY_RUN=true (always)
```

## What the profiles do NOT change

- **The gap selection logic** is the same across all profiles. The filter, max, and focus are profile-independent.
- **The template selection logic** is the same across all profiles. The template is picked from the detected stack, not the profile.
- **The generation rules** (no reflection in `safe`, no `Thread.sleep`, no `toString()`) are the same across all profiles. The generator's contract is the same; the *allowance* for what can be added is what differs.
- **The PR format** is the same. The PR title and body template don't change with profile.
- **The handoff contracts** are the same. The downstream workflows (mutation testing, coverage) don't care which profile generated the tests.
