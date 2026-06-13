# Decision: skip final states in integration-implementation promotion

**Status:** `accepted`
**Decided at:** 2026-06-13T21:14:30Z
**Decided by:** software-engineer

Skip the states: security_done, release_ready, deployed,
verified.

The standard `testing_done` exit (with the calibration
reproducer passing) is sufficient evidence for a
skill-promotion PR.

This is the same skip applied to prior promotion PRs in this
session.

testing_done -> closed
