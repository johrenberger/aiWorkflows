# Cross-Repo Handoff Index

**Cycle introduced:** 2026-06-29 cycle-6
**Purpose:** Track work that originates in `aiWorkflows` (dreaming side) but ships in a different repo.

---

## Active handoffs

### H-001 — OpenClaw runtime JSONL emitter → `openclaw/openclaw`

- **Originating PI:** PI-006a (split out of PI-006 per L-016 in cycle 5)
- **Handoff document:** `.openclaw/dreaming/openclaw-run-log-emitter-handoff.md`
- **Spec authority:** `.openclaw/dreaming/openclaw-run-log-spec.md` (cycle 5, PR #63, merge `c258efb`)
- **Parser reference:** `tests/dreaming/ev_parser.py` (cycle 5, 9 tests green)
- **Status:** proposed (out-of-repo; cannot be applied from `aiWorkflows`)
- **Acceptance signal:** the moment a runtime-emitted file lands in `tests/dreaming/fixtures/` and `make dreaming-validate` reports 117+ passed, RS-008 flips from `warning` to `passing`.

---

## How handoffs work

A handoff is a **spec-grounded implementation brief** that a competent implementer on the target repo can apply without reading the source repo. It is not code; it is a contract.

Every handoff has:

1. An originating PI (in `proposed-improvements.md`).
2. A self-contained document under `.openclaw/dreaming/`.
3. An acceptance signal (a downstream test or regression scenario that flips when the work is done).
4. An entry in this index.

When the target repo's PR lands, the dreaming side updates:
- The originating PI's status (`proposed` → `applied` or `partial`).
- The corresponding regression scenario (e.g., RS-008 severity).
- This index (move the entry from "Active" to "Closed").
- A new EV entry in `evidence-index.md` documenting the cross-repo flow.

## Why this is its own artifact

The pattern "dreaming side surfaces a need; another repo fills it; dreaming side reads the result" is becoming regular enough (H-001 is the first, but the shape generalizes — see PI-009's "extend local validation to other workflows" for a dreaming-side analog) that a dedicated index is cheaper than re-discovering the handoff structure per case. New handoffs add rows; closed handoffs move rows.
