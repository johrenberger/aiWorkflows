# Multi-Module Orchestration Protocol

**Source philosophy:** *Inline the analysis. Sub-agents are fine for isolated read-only research, never for mutating the evidence directory.* — from `app-dev-discovery/prompt.md`, generalized in `shared/concurrency.md`.

This file describes the **3-role split** for running `application-test-coverage` against a large multi-module repository. The roles are a **default-on recommendation**, not a hard requirement — single-agent mode is still valid for small repos.

## The 3 roles

| Role | Count | Lifetime | Scope | Authority |
|---|---|---|---|---|
| **Discoverer** | 1 | Whole run | Read-only on source, writes to `coordination.log` and the ledger's module/section | Owns the module map, the per-file eligibility list, and the work-batch selection |
| **Test-writer** | N (one per active module) | Per-batch | Read source + write to scratch dir `tests/<module>/<file_under_test>Test.<ext>` | Owns the test implementation for its claimed files |
| **Coverage-manager** | 1 | Whole run | Read+write on `TODO_test-coverage.md`, runs coverage command | Owns the per-file coverage table, repair loop, ledger finalization |

**Why these three, and not more:**

- **Discoverer** is the only role that can produce a stable module map and eligibility list. If you had two discoverers, they'd fight over the same source files.
- **Test-writer** is per-module because test writing is the only sub-agent work that's truly parallelizable by module (different test files, different test paths, no shared state). One per active module, not one per file — overhead dominates.
- **Coverage-manager** is single because coverage is repo-wide state. Two coverage managers would step on each other's JaCoCo/pytest-cov/lcov output files.

## When to spawn sub-agents

The decision tree:

```
Is the repo single-module (one build target)?
├── yes → run inline. No sub-agents. Default for ≤50 files.
└── no (multi-module, 4+ modules, or 1,000+ files)
    ├── Phase 3a (module detection) → main agent inline
    ├── Phase 3b (testability classification) → main agent inline OR discoverer sub-agent
    ├── Phase 7 (eligibility) → main agent inline OR discoverer sub-agent
    ├── Phase 8 (work batch) → main agent inline
    ├── Phase 9-10 (test design + impl) → test-writer sub-agents, one per active module
    ├── Phase 11-12 (focused test + coverage recheck) → coverage-manager sub-agent
    └── Phase 13-16 (repair, validation, ledger, commit) → main agent inline
```

The main agent always owns:
- The input validation
- The runtime contract (`TODO_test-coverage.md` skeleton + checkpoints)
- The final commit
- All decisions to halt or continue

## File-claim protocol (concrete)

When a test-writer is about to work on a batch of files:

1. **Test-writer → main:** `claim` message with the file list.
2. **Main agent:** checks the per-file table for conflicts, marks the rows `in-progress` with the writer's agent id, and replies `ack`.
3. **Test-writer:** implements tests, runs focused tests in its own worktree branch, returns a `manifest` with file paths + SHA-256.
4. **Main agent:** verifies hashes, moves files into canonical tree, runs focused tests, marks rows `done` with the new coverage %.
5. **Test-writer:** is now available for the next batch (or done, if all files in scope are claimed).

The `LEASE_TIMEOUT_MINUTES=30` default means a stuck test-writer's claims can be reclaimed by another writer. See `shared/concurrency.md` for the full rules.

## Branch-per-module isolation

For multi-module repos, **one branch per active module**:

```bash
# Main agent setup
WORKSPACE=/data/coverage-runs/broadleaf-2026-06-07
git clone https://github.com/johrenberger/BroadleafCommerce $WORKSPACE
cd $WORKSPACE
git switch -c workflows/coverage-integration-2026-06-07

# Per-test-writer, isolated worktree (parallel)
git worktree add $WORKSPACE-tw-core    -b workflows/coverage-core-2026-06-07
git worktree add $WORKSPACE-tw-common  -b workflows/coverage-common-2026-06-07
git worktree add $WORKSPACE-tw-admin   -b workflows/coverage-admin-2026-06-07
```

Each test-writer works in its own worktree, commits there, and pushes its branch. The main agent reviews and merges each branch back to the run branch as tests pass.

**First-run safety:** start with one module only. `MODULE_LIST=integration` is the recommended first run on BroadleafCommerce (97 files, smallest module, fastest baseline).

## Repair loop (sub-agent failure handling)

If a test-writer's batch fails (tests don't pass after `MAX_REPAIR_ATTEMPTS_PER_FAILURE_CLASS=2` retries):

1. **Main agent:** marks the rows `blocked` in the ledger with the failure class.
2. **Test-writer:** is told to abandon the scratch dir, claims are released.
3. **Main agent:** logs the blocker as `TC-BLK-TestFailure-<class>` in `TODO_test-coverage.md` and moves on to the next batch.
4. After all batches done, the main agent runs the full validation. Blockers surface in the gate results.

## Master ledger assembly

After all module sub-runs complete, the main agent assembles a master ledger:

```
TODO_test-coverage-master.md           # rollup: aggregate, per-module, per-file
TODO_test-coverage-core.md            # core module's per-file detail
TODO_test-coverage-common.md          # common module's per-file detail
TODO_test-coverage-admin.md           # admin module's per-file detail
TODO_test-coverage-integration.md     # integration module's per-file detail
```

The master has a rollup table at the top:

| Module | Files | Eligible | ≥90% | Below 90% | Blocked | Aggregate % |
|---|---:|---:|---:|---:|---:|---:|
| core | 1117 | TBD | TBD | TBD | TBD | TBD |
| common | 1042 | TBD | TBD | TBD | TBD | TBD |
| admin | 729 | TBD | TBD | TBD | TBD | TBD |
| integration | 97 | TBD | TBD | TBD | TBD | TBD |
| **TOTAL** | **2985** | **TBD** | **TBD** | **TBD** | **TBD** | **TBD** |

This is the gate result the user reviews. The per-module files are appendices.

## Resource budget (estimated)

For BroadleafCommerce's 2,985 files split across 4 modules:

| Phase | Time per module | Sub-agents |
|---|---:|---|
| 3a/3b/7 (classification) | 5 min | 1 discoverer |
| 8 (batch selection) | 1 min | main agent |
| 9-10 (test design + impl) | 30-60 min | 4 test-writers in parallel |
| 11-12 (focused + coverage) | 5-10 min | 1 coverage-manager |
| 13-16 (repair, validate, finalize) | 10-20 min | main agent |
| **TOTAL (parallel)** | **~60-90 min** | 6 sub-agents peak |

Single-agent mode would be 4-8 hours because the test-writing phase is sequential. Sub-agents are not optional at this scale — they're the only way the work fits in one session.

## Failure modes

| Failure | Detection | Recovery |
|---|---|---|
| Test-writer diverges from spec | Focused tests fail | Main agent reverts that writer's last batch, sends a `repair` message with the failure class |
| Test-writer stuck (no progress) | Lease expires (30 min) | Main agent reclaims the files, retries with a fresh writer |
| Two writers claim the same file | Main agent's `claim` ack is atomic | Second claim is rejected; second writer picks a different file |
| Coverage command corrupts state | Coverage delta doesn't match expected files | Main agent discards that coverage run, retries in clean worktree |
| Sub-agent modifies canonical ledger | Ledger SHA-256 changes outside main agent's writes | Reject the manifest, instruct sub-agent to use scratch dir only |

## When to abandon and inline

If more than 50% of test-writer batches fail with repair-loop exhaustion, the main agent should **abandon sub-agents** and run the remaining files inline. This is rare but documented so a future agent doesn't get stuck spinning up sub-agents that keep failing.
