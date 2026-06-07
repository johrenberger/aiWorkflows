# Concurrency

**Cross-workflow rules for spawning sub-agents and coordinating parallel work.**

The other workflows in this repo (`app-dev-discovery`, `application-test-coverage`, `application-mutation-testing`) all assume a single executing agent. On a small repository (≤50 source files), this is fine. On a large multi-module repository (1,000+ source files), the work must be split across sub-agents to fit in a single session's context budget.

This file documents the rules any workflow must follow when it spawns sub-agents.

## Source philosophy

`app-dev-discovery`'s prompt says: *"Do not spawn sub-agents for the analysis phases. Do the work inline so evidence is consistent and the workflow is atomic. Sub-agents are fine only for isolated read-only research, never for mutating the evidence directory."*

That principle generalizes:

- **Inline the analysis.** The main agent maintains the canonical evidence directory and ledger. Sub-agents are subordinate to the main agent's view of truth.
- **Sub-agents are fine for read-only research.** Inventory, classification, gap-mapping, test design — anything that returns a proposal, not a mutation.
- **Sub-agents are NOT fine for shared-state mutations.** Test-file writes, ledger updates, commit creation — these go through the main agent.
- **Sub-agents MAY write to a scratch directory** (e.g. `/tmp/<role>-<id>/`) that the main agent reviews and either promotes to the canonical state or discards.

## File-claim protocol (cross-workflow)

When two or more sub-agents are working in parallel on disjoint file sets, they need a way to **claim files** so they don't double-work.

The protocol is a single line per file in the workflow ledger:

```markdown
| File | Claimed-By | Status | Test-Path | Final-% | Notes |
|------|-----------|--------|-----------|--------:|-------|
| core/src/main/java/FooService.java | tw-01 | done | src/test/java/core/FooServiceTest.java | 95% | happy + 4 error paths |
| core/src/main/java/BarService.java | tw-02 | in-progress | — | — | — |
| common/src/main/java/BazUtil.java | (unclaimed) | — | — | — | — |
```

- `Claimed-By` is a stable agent id (`tw-01`, `tw-02`, ...; `disc-01` for discoverer; `cov-01` for coverage manager).
- `Status` is one of: `unclaimed`, `in-progress`, `done`, `blocked`, `reverted`.
- The main agent is the **single writer** to this table. Sub-agents send a claim request to the main agent, the main agent writes the row, and the sub-agent proceeds.

**Lease expiry:** if a sub-agent's `in-progress` row is older than `LEASE_TIMEOUT_MINUTES=30` (default), the main agent reclaims it for another agent. This prevents zombie claims from blocking the run.

## Atomic write semantics

When a sub-agent writes files to a scratch directory and the main agent later promotes them to the canonical tree:

1. The sub-agent writes only to a **scratch directory it owns** (e.g. `/tmp/tw-01/scratch/`).
2. The sub-agent's final response includes a **manifest** of files written, with absolute paths and SHA-256 hashes.
3. The main agent **verifies the SHA-256 hashes** match between the scratch directory and the manifest, then atomically moves the files into the canonical tree (`mv` from scratch to canonical, not `cp` + `rm` — preserves atomicity).
4. The main agent **runs the focused tests** for the moved files before promoting the next batch. If tests fail, the batch is reverted, the sub-agent is told to fix, and the cycle restarts.

## Branch-per-module isolation

For multi-module repositories, the recommended isolation strategy is **one branch per module**:

```bash
# Per-module branch naming: workflows/coverage-<module>-YYYY-MM-DD
git switch -c workflows/coverage-core-2026-06-07 origin/main
# ... do work for core/ module ...
# ... focused tests pass, commit, push ...

git switch -c workflows/coverage-common-2026-06-07 origin/main
# ... do work for common/ module ...
# ... focused tests pass, commit, push ...
```

The main agent opens **one PR per module** when `ALLOW_COMMIT=true`. This keeps PRs reviewable in isolation and makes failures easy to revert.

If a workflow does NOT use branch-per-module isolation (e.g. a single small-repo run), it works directly on the active branch and skips the merge step.

## When NOT to use sub-agents

Spawning sub-agents has overhead. **Default to inline for these cases:**

- Repositories with ≤50 eligible source files
- Single-module repositories (the workflow's natural unit)
- Any phase that mutates the canonical ledger or evidence directory
- Any phase that requires running a full test suite (sequential bottleneck)

For BroadleafCommerce-class targets (1,000+ files, 4+ modules), the orchestration pattern in `application-test-coverage/_docs/multi-module-orchestration.md` applies.

## Coordination messages (template)

Sub-agents and the main agent exchange messages in a small, fixed shape:

```text
FROM: <agent-id>
TO:   main
TYPE: claim | unclaim | status | manifest | done | error
REF:  <stable-id>
BODY: <one paragraph, max 200 words>
```

The `REF` is a stable identifier for the message's subject (file path, batch id, etc.). The main agent logs every message in a `coordination.log` file in the canonical workspace for auditability.
