# OpenClaw Run Log Specification

This document defines the **JSONL log format** that the downstream `ev_parser.py` (under `tests/dreaming/`) consumes. It is **part of PI-006**, applied in cycle 5 as the **downstream side** of the PI-006 work.

The **runtime side** — code in OpenClaw core that emits these logs — is outside this PR's scope. That code lives in OpenClaw itself and requires a separate change there. The point of this spec is to:

1. Be a **stable contract** so OpenClaw can emit logs that match this parser.
2. Be **parseable today** with fixture data, so dreaming's Stage 1 can move toward log-based evidence collection without waiting on the runtime change.
3. Be **extensible** — added fields are ignored by the parser unless they affect existing rules (we'll version the spec, not break it).

If you are an OpenClaw maintainer reading this: every field below is the **minimum** dreaming needs to start replacing `git log`-and-`grep` with deterministic evidence reads. Truncation/omission is allowed at the field level; the parser treats absent fields as "unknown."

## File format

- One JSON object per line (JSON Lines / `.jsonl`).
- UTF-8, no BOM.
- Newline (`\n`) is the record separator. Carriage returns are normalized by the parser before parsing.
- Lines that don't parse as JSON are recorded as `parser_errors` and excluded from the rest of the report.
- File extension: `.jsonl` by convention; the parser accepts either `.jsonl` or any file with JSONL content.
- Schema version: `spec_version` field on each record (see below).

## Record schema (v1)

```json
{
  "spec_version": 1,
  "session_id": "string (uuid or runtime-assigned handle, required)",
  "agent_id": "string (e.g. 'main', 'subagent-1')",
  "channel": "string (e.g. 'telegram', 'cli')",
  "model": "string (e.g. 'minimax/MiniMax-M3')",
  "timestamp_start": "string (ISO-8601 UTC)",
  "timestamp_end": "string (ISO-8601 UTC; absent if session is ongoing)",
  "outcome": "string enum: 'success' | 'partial' | 'failure' | 'in_progress'",
  "selected_skills": ["array of string"],
  "selected_workflows": ["array of string"],
  "selected_agents": ["array of string"],
  "tool_calls": [
    {
      "name": "string (tool name)",
      "call_id": "string (runtime-assigned)",
      "args_summary": "string (short, < 200 chars; full args are NOT logged)",
      "timestamp_start": "string (ISO-8601 UTC)",
      "timestamp_end": "string (ISO-8601 UTC; absent if ongoing)",
      "status": "string enum: 'success' | 'error' | 'timeout' | 'blocked' | 'permission_denied'"
    }
  ],
  "errors": [{"timestamp": "ISO-8601 UTC", "kind": "string", "message": "string (< 500 chars)"}],
  "retries": [{"tool_call_id": "string", "count": "int"}],
  "blockers": [{"timestamp": "ISO-8601 UTC", "blocker_id": "string", "message": "string"}]
}
```

## Required vs optional

- **Required**: `spec_version`, `session_id`, `timestamp_start`, `outcome`
- **Optional but recommended**: `model`, `agent_id`, `timestamp_end`, `tool_calls`
- **`args_summary` MUST be ≤ 200 chars.** The full argument payload is excluded by design; the dream-workflow **must not** auto-inject or capture chains of thought, and the run log enforces this at the format level. (See `.openclaw/dreaming/validation-checklist.md` "No hidden chain-of-thought capture.")
- **`message` fields (errors, blockers) MUST be ≤ 500 chars.** Same rationale.

## Schema versioning

- New optional fields: silent. Older parsers ignore them.
- Removed fields: requires bumping `spec_version` and updating the parser.
- Required-field tightenings: requires bumping `spec_version` and updating the parser.
- The parser asserts `spec_version` is known; unknown versions raise a typed error that becomes `parser_errors[].kind = "unknown_spec_version"`.

## What this spec is NOT

- **Not** a memory-log. Memory is captured by the user's manual `memory/<date>.md` files and is out of this scope.
- **Not** a tool-arguments recorder. Reasoning content is excluded by field-level truncation rules.
- **Not** a substitution for git. Git remains the authoritative source for code-level diffs. This log adds **runtime events** that git does not capture.

## Validation

The parser is exercised in `tests/dreaming/test_openclaw_run_log_parser.py`:

- `parse_log(path)` returns a `RunLogReport` with `sessions`, `tool_calls_total`, `errors_total`, `retries_total`, `blockers_total`, `parser_errors`.
- Each session appears in `report.sessions` with normalized fields.
- Invalid lines become `parser_errors` entries; they do not crash the parser.
- A fixture log under `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl` exercises the happy path and several error cases.

## Review notes (cycle 5)

- This is **PI-006 partial**. The runtime side (the code that emits these logs from the OpenClaw runtime) is outside cycle-5's scope; that's an OpenClaw-side change requiring a separate PR there.
- The downstream parser is what we control. We are establishing the format now so the runtime side can implement against a known contract.
- Future cycles may remove this comment block and add a separate `runtime` section once the OpenClaw side emits compatible logs.
