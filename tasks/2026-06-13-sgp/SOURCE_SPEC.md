# Skill Governance Pipeline — Source Spec

Source: Justin (Telegram 8654084485) at 2026-06-14T00:01:13Z
Original filename: SkillGovernancePipelineInstructions---a72f0ffd-a7ad-4cdb-ad34-d76f6ce9d027.md

## What this is

A production-grade Skill Governance Pipeline for the OpenClaw/MiniMax
environment. The pipeline audits existing skills and agents, enforces
quality gates, identifies inefficiencies, detects overlap, and generates
proposed rewritten versions of weak or redundant skills.

## Deliverable

A new Python application at `skill-governance-pipeline/` with:

- CLI commands: `scan`, `validate`, `benchmark`, `recommend`, `rewrite`, `report`, `ci`, `full`
- Discovery → metadata → contract → dependency → responsibility →
  overlap → token → ROI → benchmark → rewrite → recommend → report → CI gate
- 17 numbered core requirements
- 5 implementation phases
- MiniMax semantic scoring for judgment, deterministic checks elsewhere
- Executive + technical reports
- CI gate that blocks on critical findings
- Waivers for justified exceptions

## Quality bar (from spec)

- Real governance pipeline, not generic prompt analyzer
- Deterministic first, MiniMax only where judgment is valuable
- Token savings never override quality
- Failed CI checks block by default
- Proposed rewrites generated but not auto-applied
- Stable, repeatable, suitable for engineering leadership

## Definition of Done

- Pipeline runs end-to-end against a sample OpenClaw skill/agent library
- CI mode blocks critical governance failures
- Semantic overlap scoring works through MiniMax or mocked interface
- Proposed rewritten skills generated for weak artifacts
- Reports are business-grade and decision-ready
- Unit tests validate core behavior
- README explains setup, commands, configuration, outputs, operating model
