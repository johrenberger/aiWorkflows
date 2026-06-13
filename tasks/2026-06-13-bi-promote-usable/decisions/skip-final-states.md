# Decision: skip final states in backend-implementation promotion

**Task:** 2026-06-13-bi-promote-usable
**Status:** `accepted`
**Decided at:** 2026-06-13T22:50:00Z
**Decided by:** software-engineer

## Context

The standard `task-state-management` linter requires walking
through `security_done`, `release_ready`, `deployed`, and
`verified` before `closed`. None of those apply to a
skill-promotion PR (we don't deploy, we don't have a security
scan on a skill README, etc.).

## Decision

Approve testing_done -> closed for this task.

Skip the states: security_done, release_ready, deployed,
verified. The standard `testing_done` exit (with the
calibration reproducer passing) is sufficient evidence for
a skill-promotion PR.

This is the same skip applied to prior promotion PRs in this
session (PRs #30, #31, #32, #33, #34, #40-#44).
