# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for
the v2 (test-factory) and mutation work in the aiWorkflows repo.
ADRs document the design decisions that shape the system, with
the format:

- **Status** (Accepted / Superseded)
- **Context** (what was the situation before the decision)
- **Considered options** (what we weighed)
- **Decision outcome** (what we chose and why)
- **Consequences** (positive, negative, neutral)
- **Follow-up** (subsequent stories or future work)
- **More information** (links to PRs, story markdown, calibration data)

## Why these ADRs exist

The 2026-06-13 skill-progress review (Gap 3) noted that the
`architecture-decision` skill wasn't invoked for the 4 material
design decisions in stories 020, 022, 024, 026. These ADRs
backfill that gap.

Each ADR also serves as a **calibration pass** for the
`code-change-review` reproducer. See
`tasks/2026-06-13-ccr-validated-reproducer/reports/calibration-history.md`
(in the workspace) for the cumulative calibration data.

## Index

| # | Title | Story | Date |
|---|---|---|---|
| [0001](0001-v2-coverage-generation-default-on.md) | v2 coverage generation default-on | 020 | 2026-06-10 |
| [0002](0002-jacoco-path-matching-additive-regression-net.md) | JaCoCo path-matching: additive regression net | 022 | 2026-06-11 |
| [0003](0003-zero-coverage-priority-visibility-only.md) | Zero-coverage priority is visibility-only | 024 | 2026-06-12 |
| [0004](0004-pit-policy-chain-test-compile.md) | PIT policy chains `test-compile` | 026 / 030 | 2026-06-12 / 2026-06-13 |

## Out of scope (intentionally not in this directory)

- Story 021 (JaCoCo argLine late-binding): a code fix, not a
  design decision worth an ADR.
- Story 023 (`--module auto`): a CLI convenience; the design
  is captured in the CLI's `MODULE_AUTO` sentinel. Not a
  multi-option decision.
- Story 025 (`--coverage-out`): a flag-add. Default-flip ADR
  (0001) covers the design pattern; no separate ADR needed.
- Story 027 (Broadleaf EfficientLRUMap test): off-repo work.
  Would be a Broadleaf ADR, not an aiWorkflows ADR.
- Story 028 (promote task-state-management): a doc change.
  No design decision.
- Story 029-032 (PR #41 follow-ups): the design decisions are
  the ones in 020, 022, 024, 026. Story 029 (coverage_out_dir
  flatten) is a contract fix, not a multi-option decision.
  Story 030 is the docstring fix covered by ADR 0004.
  Story 031 (zero_coverage split) is an extension of ADR 0003.
  Story 032 (TypedDict) is a typing pattern, captured in the
  story markdown.
