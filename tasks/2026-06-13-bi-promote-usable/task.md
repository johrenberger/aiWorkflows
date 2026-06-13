# Task: 2026-06-13-bi-promote-usable

## Goal

Promote `backend-implementation` from `draft` to `usable`, on
the strength of 3 use-case exercises (UC2, UC3, UC4) on the
re-baselined `johrenberger/spring-petclinic-rest` fork.

## Why

Per the 2026-06-13 re-assessment, this skill was undervalued at
`draft`. The 4-use-case exercise from 2026-06-13 (commit
`a6cac9b` on aiWorkflows) is a calibration reproducer that
meets the `usable` bar:

1. **Real tasks** — 4 distinct backend implementation tasks
   on a real Spring Boot 4 codebase
2. **Real artifacts** — 3 implementation reports + 3 handoff
   packets produced
3. **Honest accounting** — 1 issue caught (JPA+cache), 1 issue
   not caught (skipped states), 1 issue introduced (UC3
   `@Cacheable` reverted)
4. **Workflow followed** — 3/4 use cases followed the skill's
   7-step workflow + java-spring profile

The original `draft` level was based on "skill exists and is
documented." The `usable` level requires "skill has been
exercised and produces valuable artifacts" — which is now true.

NOT promoted to `validated` because:
- The skill did NOT catch issues a no-skill run also missed
  (UC1 baseline produced 239/239 working tests without it)
- The skill CAN introduce issues (UC3 cache problem)
- The skill is best for typical CRUD work, risky for
  advanced patterns (caching, async, transactions)

## In scope

- 1 PR to johrenberger/test-repo: `draft` → `usable` in
  `skills/README.md` (line ~128)
- 1 calibration reproducer at `reproduce.py` (~100 lines)
- 1 calibration report at `reports/calibration-report.md`
- 1 task workspace (state: testing_done)

## Out of scope

- The `validated` level (4+ use cases needed; 3 done is
  statistically thin per lesson from validated skills)
- The 4 use case branches on `spring-petclinic-rest` (PRs
  #1-#4 already open, pending merge by user)
- Changes to the skill content itself (the skill content is
  fine; it's the maturity level that needs updating)

## Deliverables

- `reproduce.py` — verifies all 3 with-skill use cases have
  implementation reports + handoff packets
- `reports/calibration-report.md` — 3/3 artifacts present,
  decision: USABLE
- PR to test-repo: 1-line README change
