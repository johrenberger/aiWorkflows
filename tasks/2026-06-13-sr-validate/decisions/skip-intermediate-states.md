# Decision: skip intermediate states in security-review promotion

**Task:** 2026-06-13-sr-validate
**Status:** `accepted`
**Decided at:** 2026-06-13T17:20:00Z
**Decided by:** software-engineer

## Context

The skill-maturation plan promotes a skill from `draft` to
`validated` in one PR. The standard `task-state-management`
linter requires walking through `security_done`, `release_ready`,
`deployed`, `verified` before `closed`. None of those apply
to a skill-promotion PR (we don't deploy, we don't have
a security scan on a skill, etc.).

## Decision

Approve testing_done -> closed for this task.

Skip the states: `security_done`, `release_ready`, `deployed`,
`verified`. The standard `tested` exit (in `testing_done`) is
sufficient evidence for a skill-promotion PR.

This is the same skip applied to prior promotion PRs in this
session (PRs #30, #31, #32, #33, #34).
