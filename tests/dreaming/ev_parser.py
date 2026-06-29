"""OpenClaw run log parser (PI-006 partial, cycle 5).

Downstream side of PI-006. Reads JSONL run logs that match
`.openclaw/dreaming/openclaw-run-log-spec.md` and produces a
deterministic `RunLogReport`. The runtime side (the code that
emits these logs) is in OpenClaw core and is out of cycle-5 scope.

This module is intentionally minimal: a strict-required schema, an
extensible optional-fields contract, and explicit handling for malformed
lines (they become `parser_errors`, never crashes).

Validation lives in `tests/dreaming/test_openclaw_run_log_parser.py`.
The fixture it consumes is `tests/dreaming/fixtures/openclaw-run-log-fixture.jsonl`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_SPEC_VERSIONS = (1,)
ARG_SUMMARY_MAX_CHARS = 200
MESSAGE_MAX_CHARS = 500

_VALID_TOOL_STATUSES = frozenset(
    {"success", "error", "timeout", "blocked", "permission_denied"}
)
_VALID_OUTCOMES = frozenset({"success", "partial", "failure", "in_progress"})


@dataclass
class ToolCall:
    name: str
    call_id: str
    args_summary: str
    timestamp_start: str
    timestamp_end: str | None
    status: str


@dataclass
class Session:
    session_id: str
    agent_id: str | None
    channel: str | None
    model: str | None
    timestamp_start: str
    timestamp_end: str | None
    outcome: str
    selected_skills: list[str] = field(default_factory=list)
    selected_workflows: list[str] = field(default_factory=list)
    selected_agents: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    retries: list[dict] = field(default_factory=list)
    blockers: list[dict] = field(default_factory=list)


@dataclass
class ParserError:
    line_number: int
    kind: str
    message: str


@dataclass
class RunLogReport:
    sessions: list[Session] = field(default_factory=list)
    parser_errors: list[ParserError] = field(default_factory=list)
    spec_versions_seen: set[int] = field(default_factory=set)

    @property
    def tool_calls_total(self) -> int:
        return sum(len(s.tool_calls) for s in self.sessions)

    @property
    def errors_total(self) -> int:
        return sum(len(s.errors) for s in self.sessions)

    @property
    def retries_total(self) -> int:
        return sum(len(s.retries) for s in self.sessions)

    @property
    def blockers_total(self) -> int:
        return sum(len(s.blockers) for s in self.sessions)


def _truncate(s: str | None, max_chars: int) -> str:
    """Hard-truncate a string field to its budget. Used for
    args_summary and message fields per the spec."""
    if s is None:
        return ""
    return s if len(s) <= max_chars else s[:max_chars]


def _parse_tool_call(raw: dict, line_number: int, errs: list[ParserError]) -> ToolCall | None:
    try:
        name = raw["name"]
        call_id = raw.get("call_id", "")
        args_summary = _truncate(raw.get("args_summary", ""), ARG_SUMMARY_MAX_CHARS)
        ts_start = raw.get("timestamp_start", "")
        ts_end = raw.get("timestamp_end")
        status = raw.get("status", "success")
    except KeyError as e:
        errs.append(
            ParserError(line_number, "missing_tool_call_field", f"missing {e}")
        )
        return None
    if status not in _VALID_TOOL_STATUSES:
        errs.append(
            ParserError(
                line_number,
                "invalid_tool_status",
                f"tool status {status!r} not in valid set",
            )
        )
        return None
    return ToolCall(name, call_id, args_summary, ts_start, ts_end, status)


def _parse_session(raw: dict, line_number: int, errs: list[ParserError]) -> Session | None:
    """Parse a single JSONL record into a Session. Returns None if a required
    field is missing; otherwise returns the Session with normalizations applied."""
    try:
        spec_version = int(raw["spec_version"])
        session_id = raw["session_id"]
        timestamp_start = raw["timestamp_start"]
        outcome = raw["outcome"]
    except (KeyError, ValueError, TypeError) as e:
        errs.append(
            ParserError(
                line_number,
                "missing_required_field",
                f"required field missing or wrong type: {e}",
            )
        )
        return None
    if spec_version not in SUPPORTED_SPEC_VERSIONS:
        errs.append(
            ParserError(
                line_number,
                "unknown_spec_version",
                f"spec_version={spec_version} not in {SUPPORTED_SPEC_VERSIONS}",
            )
        )
        return None
    if outcome not in _VALID_OUTCOMES:
        errs.append(
            ParserError(
                line_number,
                "invalid_outcome",
                f"outcome {outcome!r} not in valid set",
            )
        )
        return None
    tool_calls: list[ToolCall] = []
    for tc in raw.get("tool_calls", []) or []:
        parsed = _parse_tool_call(tc, line_number, errs)
        if parsed is not None:
            tool_calls.append(parsed)
    errors = []
    for e in raw.get("errors", []) or []:
        if isinstance(e, dict):
            e2 = {**e, "message": _truncate(e.get("message", ""), MESSAGE_MAX_CHARS)}
            errors.append(e2)
    blockers = []
    for b in raw.get("blockers", []) or []:
        if isinstance(b, dict):
            b2 = {**b, "message": _truncate(b.get("message", ""), MESSAGE_MAX_CHARS)}
            blockers.append(b2)
    retries = []
    for r in raw.get("retries", []) or []:
        if isinstance(r, dict):
            retries.append(r)
    return Session(
        session_id=session_id,
        agent_id=raw.get("agent_id"),
        channel=raw.get("channel"),
        model=raw.get("model"),
        timestamp_start=timestamp_start,
        timestamp_end=raw.get("timestamp_end"),
        outcome=outcome,
        selected_skills=list(raw.get("selected_skills") or []),
        selected_workflows=list(raw.get("selected_workflows") or []),
        selected_agents=list(raw.get("selected_agents") or []),
        tool_calls=tool_calls,
        errors=errors,
        retries=retries,
        blockers=blockers,
    )


def parse_log(path: str | Path) -> RunLogReport:
    """Parse a JSONL OpenClaw run log file.

    Malformed lines become `parser_errors` entries and the parser
    continues. Returns an empty report (rather than raising) if the
    file is missing or empty."""
    p = Path(path)
    report = RunLogReport()
    if not p.is_file():
        report.parser_errors.append(
            ParserError(0, "file_not_found", f"file not found: {p}")
        )
        return report
    with p.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                report.parser_errors.append(
                    ParserError(lineno, "invalid_json", str(e))
                )
                continue
            if not isinstance(record, dict):
                report.parser_errors.append(
                    ParserError(
                        lineno,
                        "invalid_top_level",
                        f"expected object, got {type(record).__name__}",
                    )
                )
                continue
            try:
                report.spec_versions_seen.add(int(record.get("spec_version", -1)))
            except (TypeError, ValueError):
                pass
            session = _parse_session(record, lineno, report.parser_errors)
            if session is not None:
                report.sessions.append(session)
    return report
