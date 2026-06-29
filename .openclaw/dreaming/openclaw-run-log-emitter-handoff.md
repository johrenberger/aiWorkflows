# OpenClaw Run Log Emitter — Implementation Handoff (PI-006 Part A)

**Cycle:** 2026-06-29 cycle-6
**Target repo:** `openclaw/openclaw` (runtime package)
**Source repo for this handoff:** `johrenberger/aiWorkflows` — the dreaming side
**Spec authority:** `.openclaw/dreaming/openclaw-run-log-spec.md` (cycle 5, merged via PR #63)
**Parser (canonical reference):** `tests/dreaming/ev_parser.py` (cycle 5, 9 tests green)

---

## What this is

Cycle 5 (PR #63 in `aiWorkflows`) shipped the **downstream** side of PI-006: a JSONL run-log spec, a parser, a fixture, and 9 pytest cases. The **upstream** side — code inside the OpenClaw runtime that emits those JSONL records — was declared out-of-scope for the dreaming repo and is the work this handoff describes.

This document is the **complete, spec-grounded implementation brief** for the OpenClaw-side PR. It is intended to be copy-pasted (or referenced) into the PR description for the runtime-package change.

The implementer does **not** need to read the dreaming side. Everything below is self-contained.

## Scope of the runtime change

Add an opt-in **JSONL run-log writer** to the OpenClaw runtime that:

1. Emits one JSONL record per **session** (per `session_id`).
2. Captures per-session the fields the spec requires + the fields the parser validates strictly.
3. Hard-truncates `args_summary` and `errors[].message` / `blockers[].message` to the parser's budgets **at emit time**, not at parse time. (The parser also truncates, but emitting pre-truncated is the contract — full args never touch the log.)
4. Honors the spec's permissive-default contract: optional fields can be absent; new optional fields can be added later without spec bumps.
5. Is **opt-in** (a runtime flag, default OFF in v1). The dreaming cycle used the fixture; production rollout is gated.

## Output file shape

- One JSON object per line, JSONL.
- UTF-8, no BOM, `\n` record separator.
- Default path: `<openclaw-data-dir>/run-logs/<UTC-YYYY-MM-DD>.jsonl` (date partitioned by the runtime's local-day boundary, by `timestamp_start`'s UTC date).
- File rotation: append on each session close; never read by the runtime.
- File locking: not required for v1 (single-writer process model assumed). Document the assumption.

## Required emit contract

Each session-close event **must** produce exactly one record. The record's `session_id` is the runtime's session handle. Required fields (parser hard-rejects otherwise):

| Field | Type | Source in runtime |
| --- | --- | --- |
| `spec_version` | int (literal `1` for v1) | constant |
| `session_id` | string (uuid or runtime handle) | existing session handle |
| `timestamp_start` | string (ISO-8601 UTC, with `Z`) | existing session-start timestamp |
| `outcome` | string enum | new — see "Outcome mapping" below |

If any of these four are missing at emit time, the runtime **must** still write a record — with the field present but the offending value replaced by a documented placeholder (`"<missing>"` for strings, `0` for `spec_version`, `"unknown"` for `outcome`) — and **must** increment an internal `emit_degraded_total` counter. Do not silently drop sessions; the parser's `parser_errors` channel is for downstream visibility, but the runtime is responsible for emitting something usable.

## Strictly-enforced fields (when present)

These have parser-side enforcement. Pre-truncate at emit time so the runtime is the source of truth on the budget.

| Field | Constraint | Emit-time behavior |
| --- | --- | --- |
| `tool_calls[].status` | ∈ {`success`, `error`, `timeout`, `blocked`, `permission_denied`} | Map runtime's internal status; if unmappable, write `"unknown"` (do **not** drop the tool call). The parser will record a `parser_error` of kind `invalid_tool_status`, which is the correct downstream signal. |
| `tool_calls[].args_summary` | ≤ 200 chars, hard-truncated | Build from the tool name + a short, deterministic summary of *what* the call did (e.g., `"read file"`, `"exec make dreaming-validate"`, `"message send telegram"`). **Never** include the full argument payload. |
| `errors[].message` | ≤ 500 chars, hard-truncated | Include the runtime's error string verbatim up to the limit; append `"...[truncated]"` only if you want to flag it. The parser also truncates, but emit-time truncation is the contract. |
| `blockers[].message` | ≤ 500 chars, hard-truncated | Same. |
| `spec_version` | int literal `1` | Constant for v1. Bump + parser change required to add a new version. |

## Outcome mapping

The runtime should derive `outcome` from the session's final state. Recommended mapping:

| Runtime state | `outcome` value |
| --- | --- |
| Session completed all planned work | `"success"` |
| Session completed some work, some failures, no unrecoverable error | `"partial"` |
| Session hit an unrecoverable error and aborted | `"failure"` |
| Session is still running at emit time (e.g., on graceful shutdown with an in-flight session) | `"in_progress"` |

The parser accepts exactly these four values. Anything else triggers a `parser_error` of kind `invalid_outcome`.

## Optional but recommended fields

These are not required, but the parser is built to consume them and the dreaming side will read them. Emit them if the runtime has them.

| Field | Type | Source in runtime |
| --- | --- | --- |
| `model` | string (e.g., `"minimax/MiniMax-M3"`) | runtime model handle |
| `agent_id` | string (e.g., `"main"`, `"subagent-1"`) | agent registration |
| `channel` | string (e.g., `"telegram"`, `"cli"`) | inbound channel |
| `timestamp_end` | string (ISO-8601 UTC) | session-end timestamp; absent if `outcome == "in_progress"` |
| `selected_skills` | array of string | names of skills activated this session |
| `selected_workflows` | array of string | names of workflows activated this session |
| `selected_agents` | array of string | sub-agent ids spawned this session |
| `tool_calls` | array of objects (see below) | per tool-call record |
| `errors` | array of `{timestamp, kind, message}` | per-error record |
| `retries` | array of `{tool_call_id, count}` | per-retried-tool aggregate |
| `blockers` | array of `{timestamp, blocker_id, message}` | per-blocker record |

The `tool_calls` shape is:

```json
{
  "name": "string (tool name)",
  "call_id": "string (runtime-assigned)",
  "args_summary": "string (<= 200 chars; full args are NOT logged)",
  "timestamp_start": "string (ISO-8601 UTC)",
  "timestamp_end": "string (ISO-8601 UTC; absent if ongoing)",
  "status": "string enum"
}
```

The `name` and `call_id` are required inside each `tool_calls` entry — the parser drops tool calls missing these and records a `parser_error` of kind `missing_tool_call_field`.

## Schema-versioning rules (read carefully)

The parser enforces a tight versioning contract:

- **Adding optional fields is silent.** Older parsers ignore them.
- **Removing a field is breaking.** Requires bumping `spec_version` and updating the parser.
- **Tightening a required set is breaking.** Same as above.
- **Unknown `spec_version` → `parser_error` of kind `unknown_spec_version`.**

For v1, the implementer should NOT add new fields beyond the spec without coordinating with the dreaming side. (The dreaming side can be updated by a parser patch; the spec is the contract.) If the runtime genuinely needs a new field, propose a spec amendment first.

## Anti-CoT invariant (read carefully)

The `args_summary ≤ 200 chars` rule is **the dream-workflow's anti-chain-of-thought feature at the format level.** The runtime must NEVER emit a full argument payload, even temporarily, even in an in-memory buffer that gets summarized later. Summary is a runtime-time decision; the full payload must not be retained for log purposes. This is a hard rule with no exceptions, not a soft guideline.

(See `.openclaw/dreaming/validation-checklist.md` "No hidden chain-of-thought capture" for the dreaming-side framing. The runtime side inherits the same invariant.)

## Suggested implementation skeleton

The implementer should pick a language consistent with the rest of the OpenClaw runtime. The pseudocode below is language-agnostic.

```
on session_start(session_id, ts):
    session = { spec_version: 1, session_id, timestamp_start: ts }
    pending_sessions[session_id] = session

on tool_call_start(session_id, call_id, name, args):
    tc = {
        name, call_id,
        args_summary: summarize(name, args),   # runtime-side, < 200 chars
        timestamp_start: now_iso8601_utc(),
    }
    pending_sessions[session_id].tool_calls.append(tc)

on tool_call_end(session_id, call_id, status, error=None):
    tc = find_pending_tool_call(...)
    tc.timestamp_end = now_iso8601_utc()
    tc.status = map_status(status)             # see outcome/status mapping
    if error:
        pending_sessions[session_id].errors.append({
            timestamp: now_iso8601_utc(),
            kind: classify_error(error),
            message: truncate(str(error), 500),
        })

on session_end(session_id, outcome, reason=None):
    s = pending_sessions.pop(session_id)
    s.timestamp_end = now_iso8601_utc()
    s.outcome = map_outcome(outcome)
    write_jsonl_line(dated_log_path(s.timestamp_start), s)
```

`summarize(name, args)` is the critical function. It must:
- Produce a deterministic, short description of the call.
- NOT include any payload that resembles chain-of-thought content (e.g., long reasoning text, free-form user content, model output).
- Cap at 200 chars.

Examples (illustrative, not prescriptive):
- `read_file(path=README.md)` → `"read README.md"`
- `exec(command="make dreaming-validate")` → `"make dreaming-validate"`
- `message(channel=telegram, body="...")` → `"send telegram (240 chars)"` (length, not body)
- `web_search(query="...")` → `"web_search: <truncated query>"` (truncate the query itself)

## Validation — what the implementer must do before opening the PR

1. **Emit a fixture session** with at least: 1 success tool call, 1 error tool call, 1 retry, 1 blocker.
2. **Pipe the JSONL file** through `ev_parser.parse_log()` from the dreaming side. The parser returns a `RunLogReport`. Required: `len(sessions) >= 1`, `tool_calls_total >= 3`, `errors_total >= 1`, `retries_total >= 1`, `blockers_total >= 1`, **zero `parser_errors` of kind `missing_required_field`, `invalid_outcome`, or `unknown_spec_version`**. (Truncation `parser_errors` are acceptable; truncation is silent at the parser level, so this is a runtime-side validation, not a parser-side one.)
3. **Test oversize truncation** by emitting a session with a 5000-char `args_summary` and a 2000-char error `message`. Confirm the emitted file's `args_summary` is ≤ 200 chars and the `message` is ≤ 500 chars.
4. **Test outcome mapping** by emitting one session of each `outcome` value and parsing the result; confirm zero `invalid_outcome` `parser_errors`.
5. **Test missing-data degradation** by deliberately omitting `timestamp_end` for an in-progress session and `model` for a session where it's not set. Confirm the parser still produces a valid session (no `missing_required_field`).
6. **Run the parser's existing 9 tests** in the dreaming side against a runtime-emitted file. All 9 should pass.
7. **Run `make dreaming-validate`** in `aiWorkflows` after copying the runtime-emitted file into `tests/dreaming/fixtures/`. Confirm 117+ tests pass.

## Rollout plan (suggested)

- **Phase 1 (this PR)**: opt-in flag, default OFF. Emit-only; no parser-side changes needed (parser already exists, cycle 5).
- **Phase 2 (follow-up)**: enable by default in nightly-dreaming-validation CI; the dreaming test suite already exercises the parser, so the moment the runtime emits a conformant file, RS-008 (the OpenClaw run log evidence minimum, currently `warning`) flips from `fail` to `pass`.
- **Phase 3 (later cycle)**: bump `spec_version` to `2` if the runtime needs to add genuinely new fields; coordinate with the dreaming side on the parser patch.

## Open questions for the runtime implementer

- **What is the runtime's session boundary?** The spec assumes a session has a single start and end. If the runtime's model is "per turn" rather than "per session," the spec needs an amendment, not just an emitter. (Confirm with the dreaming side before opening the PR.)
- **What happens on crash?** If the runtime aborts without a clean session_end, the session is lost (no `timestamp_end`, no `outcome`). The recommended fallback is: on next startup, scan for any pending sessions older than N hours and write a record with `outcome = "failure"` and a synthetic `timestamp_end` = startup time. Document the choice; do not skip it.
- **Cross-process emission.** If the runtime forks or spawns long-lived sub-agents that each have their own session_id, each sub-agent must write its own record. The current spec is per-session, not per-process.

## Acceptance criteria for this handoff

This handoff is **done** when:

- [ ] The runtime has an opt-in JSONL emitter matching the contract above.
- [ ] Validation steps 1–7 all pass.
- [ ] The dreaming side's `make dreaming-validate` reports 117+ passed with a runtime-emitted file in `tests/dreaming/fixtures/`.
- [ ] The runtime PR description references this handoff document and the dreaming spec by URL.
- [ ] RS-008 in `.openclaw/dreaming/regression-scenarios.md` is updated from `warning` to `passing-in-CI` once the CI workflow consumes a real emitted file.

## Refs

- **Spec (cycle 5):** `.openclaw/dreaming/openclaw-run-log-spec.md` (PR #63, merge `c258efb`)
- **Parser (cycle 5):** `tests/dreaming/ev_parser.py`, `tests/dreaming/test_openclaw_run_log_parser.py` (9 tests)
- **Fixture (cycle 5):** `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl`
- **Lessons / patterns:** L-007, L-016, RS-008, RS-016, P-IP-001, P-IP-004
- **PI ledger:** PI-006 (`partial` post-cycle-5) → PI-006 Part A (this handoff); PI-006 Part B was cycle 5's deliverable.
- **Dreaming PRs:** PR #59 (cycle 1, baseline), PR #60 (cycle 2, PI-008), PR #61 (cycle 3, RS-013/014), PR #62 (cycle 4, RS-015/PI-012), PR #63 (cycle 5, PI-006 partial).
