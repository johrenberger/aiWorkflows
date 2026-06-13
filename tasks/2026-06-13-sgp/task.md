# Task: 2026-06-13-sgp — Skill Governance Pipeline

## Source

- Spec ingested from Justin (Telegram 8654084485) at 2026-06-14T00:01:13Z
- Stored at: `SOURCE_SPEC.md`
- Project location: `/data/.openclaw/workspace/skill-governance-pipeline/`

## Goal

Build a production-grade Skill Governance Pipeline for the OpenClaw /
MiniMax environment. The pipeline audits existing skills and agents,
enforces quality gates, identifies inefficiencies, detects overlap, and
generates proposed rewritten versions of weak or redundant skills.

## Phases (per source spec)

- **Phase 1** (this segment): discovery, metadata parser, contract
  validator, static token analyzer, executive report skeleton
- **Phase 2**: dependency analyzer, responsibility analyzer,
  deterministic overlap heuristics, technical report, CI gate
- **Phase 3**: MiniMax semantic scoring interface, semantic overlap,
  ROI scorer, recommendation engine
- **Phase 4**: benchmark framework, rewrite generator, proposed rewrite
  output, remediation backlog
- **Phase 5**: governance history, waiver support, full business-grade
  reporting, CI-ready execution

## Status

- Phase 1: ✅ complete (25/25 tests pass; e2e CI tested against
  real test-repo+aiWorkflows catalog)
- Phase 2-5: pending
