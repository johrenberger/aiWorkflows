# Decision: skip intermediate states

**Task:** 2026-06-13-rr-validate
**Status:** `accepted`
**Decided at:** 2026-06-13T17:25:00Z
**Decided by:** software-engineer

## Decision

Approve testing_done -> closed for this task.

Skip the states: `security_done`, `release_ready`, `deployed`,
`verified`. The standard `tested` exit (in `testing_done`) is
sufficient evidence for a skill-promotion PR.
