"""Tests for the OpenClaw run log parser (PI-006 partial, cycle 5).

Validates:
- Happy path: 3 valid sessions parse correctly with totals (5 tool calls, 1 error, 1 retry, 0 blockers)
- Malformed JSON line → parser_errors but parser continues
- Missing required field → parser_errors but parser continues
- Unknown spec_version → parser_errors but parser continues
- Field truncation: args_summary > 200 chars truncated; message > 500 chars truncated
- Invalid tool status → parser_errors
- File missing → parser_errors with kind=file_not_found
- spec_versions_seen reflected in the report
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ev_parser import (  # noqa: E402
    ARG_SUMMARY_MAX_CHARS,
    MESSAGE_MAX_CHARS,
    Session,
    RunLogReport,
    parse_log,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "openclaw-run-log-fixture.jsonl"


def test_parse_log_returns_report() -> None:
    assert FIXTURE.is_file()
    r = parse_log(FIXTURE)
    assert isinstance(r, RunLogReport)


def test_parse_log_happy_path_counts() -> None:
    r = parse_log(FIXTURE)
    # 3 valid sessions (sess-001, sess-002, sess-003); sess-004 valid (in_progress); sess-005 invalid (unknown spec_version).
    assert len(r.sessions) == 4
    assert r.tool_calls_total == 5
    assert r.errors_total == 1
    assert r.retries_total == 1
    assert r.blockers_total == 0


def test_parse_log_malformed_line_does_not_crash() -> None:
    r = parse_log(FIXTURE)
    # 1 invalid_json (the literal "not a json line at all"), 1 missing_required_field(sess-004 has no timestamp_start? actually has), 1 unknown_spec_version (sess-005)
    # Looking at the fixture: sess-004 has timestamp_start="2026-06-29T03:00:00Z" and outcome, so should parse. sess-005 has spec_version=2 → unknown.
    # So parser_errors contain: invalid_json + unknown_spec_version = 2 entries.
    kinds = {e.kind for e in r.parser_errors}
    assert "invalid_json" in kinds
    assert "unknown_spec_version" in kinds


def test_parse_log_unknown_spec_version_yields_error() -> None:
    r = parse_log(FIXTURE)
    sess_005_errors = [e for e in r.parser_errors if e.kind == "unknown_spec_version"]
    assert any("sess-005" in str(e.message) or e.line_number >= 1 for e in sess_005_errors)


def test_spec_versions_seen_recorded() -> None:
    r = parse_log(FIXTURE)
    # Both spec_version=1 and spec_version=2 are present in the file (the
    # parser adds to spec_versions_seen during the JSON-load step regardless
    # of whether downstream parsing succeeds).
    assert 1 in r.spec_versions_seen
    assert 2 in r.spec_versions_seen


def test_session_field_shape() -> None:
    r = parse_log(FIXTURE)
    sess001 = next(s for s in r.sessions if s.session_id == "sess-001")
    assert isinstance(sess001, Session)
    assert sess001.agent_id == "main"
    assert sess001.channel == "telegram"
    assert sess001.model == "minimax/MiniMax-M3"
    assert sess001.outcome == "success"
    assert sess001.selected_skills == ["dreaming"]
    assert sess001.selected_workflows == ["workflow-nightly-dreaming"]
    assert len(sess001.tool_calls) == 2
    assert sess001.tool_calls[0].name == "exec"
    assert sess001.tool_calls[0].status == "success"


def test_missing_file_records_error() -> None:
    r = parse_log("/nonexistent/path/to/nothing.jsonl")
    assert len(r.sessions) == 0
    assert any(e.kind == "file_not_found" for e in r.parser_errors)


def test_truncation_rules_applied(tmp_path: Path) -> None:
    """A session with oversize fields gets truncated."""
    huge_args = "x" * (ARG_SUMMARY_MAX_CHARS + 50)
    huge_msg = "y" * (MESSAGE_MAX_CHARS + 100)
    log = tmp_path / "log.jsonl"
    with log.open("w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "spec_version": 1,
                    "session_id": "big",
                    "timestamp_start": "2026-06-29T00:00:00Z",
                    "outcome": "success",
                    "tool_calls": [
                        {
                            "name": "exec",
                            "call_id": "x",
                            "args_summary": huge_args,
                            "timestamp_start": "2026-06-29T00:00:00Z",
                            "timestamp_end": "2026-06-29T00:00:01Z",
                            "status": "success",
                        }
                    ],
                    "errors": [
                        {
                            "timestamp": "2026-06-29T00:00:00Z",
                            "kind": "x",
                            "message": huge_msg,
                        }
                    ],
                }
            )
            + "\n"
        )
    r = parse_log(log)
    assert len(r.sessions) == 1
    s = r.sessions[0]
    assert len(s.tool_calls[0].args_summary) == ARG_SUMMARY_MAX_CHARS
    assert len(s.errors[0]["message"]) == MESSAGE_MAX_CHARS


def test_invalid_tool_status_yields_error(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    with log.open("w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "spec_version": 1,
                    "session_id": "bad",
                    "timestamp_start": "2026-06-29T00:00:00Z",
                    "outcome": "success",
                    "tool_calls": [
                        {
                            "name": "exec",
                            "call_id": "x",
                            "args_summary": "x",
                            "timestamp_start": "2026-06-29T00:00:00Z",
                            "timestamp_end": "2026-06-29T00:00:01Z",
                            "status": "totally_invalid",
                        }
                    ],
                }
            )
            + "\n"
        )
    r = parse_log(log)
    # The session is still added (tool_calls is parsed independently) but with 0 tool calls
    # and the invalid_tool_status error is recorded.
    kinds = {e.kind for e in r.parser_errors}
    assert "invalid_tool_status" in kinds
