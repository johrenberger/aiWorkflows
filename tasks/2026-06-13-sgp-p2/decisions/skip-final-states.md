# Decision: skip final states in SGP Phase 2 close

**Status:** `accepted`
**Decided at:** 2026-06-13T22:20:30Z
**Decided by:** software-engineer

Skip the states: security_done, release_ready, deployed,
verified.

testing_done -> closed

Phase 2 is a local-only milestone; security, release, deploy,
and verify are reserved for the final Phase 5 gate when the
full pipeline is complete and CI-ready.
