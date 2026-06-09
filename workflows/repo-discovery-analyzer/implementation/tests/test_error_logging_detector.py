"""Tests for repo_discovery_analyzer.detectors.error_logging.

Covers every finding branch in detect_error_logging: logger usage,
monitoring/telemetry, global error handling, and retry behavior.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.error_logging import (
    _first_match,
    detect_error_logging,
)
from repo_discovery_analyzer.model import FileRecord


def _record(path: str) -> FileRecord:
    return FileRecord(
        path=path,
        extension=Path(path).suffix.lower(),
        size_bytes=0,
        language_guess="text",
        role_guess="source",
        line_count=None,
        source_line_count=None,
        github_url=f"https://github.com/acme/widget/blob/abc1234/{path}",
        reviewed_by_analyzer=True,
        skipped=False,
        skip_reason=None,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class ErrorLoggingTests(unittest.TestCase):
    def test_logger_usage_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "import logging\nlogger = logging.getLogger(__name__)\n")
            records = [_record("src/app.py")]
            result = detect_error_logging(repo, "acme", "widget", "abc1234", records)
        findings = result["error_logging"]
        cats = {f["category"] for f in findings}
        self.assertIn("logging", cats)
        # "logger usage" is the technology label for the logging branch.
        tech = next(f["technology"] for f in findings if f["category"] == "logging")
        self.assertEqual(tech, "logger usage")

    def test_monitoring_telemetry_branch_uses_first_match(self) -> None:
        # The first matching telemetry keyword (sentry > datadog > opentelemetry
        # > prometheus > newrelic) should be reported as the technology.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "import sentry_sdk\nsentry_sdk.init()\n")
            records = [_record("src/app.py")]
            result = detect_error_logging(repo, "acme", "widget", "abc1234", records)
        monitor = [f for f in result["error_logging"] if f["category"] == "monitoring/telemetry"]
        self.assertEqual(len(monitor), 1)
        self.assertEqual(monitor[0]["technology"], "sentry")

    def test_monitoring_telemetry_falls_through_to_newrelic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "// newrelic agent enabled\n")
            records = [_record("src/app.py")]
            result = detect_error_logging(repo, "acme", "widget", "abc1234", records)
        monitor = [f for f in result["error_logging"] if f["category"] == "monitoring/telemetry"]
        self.assertEqual(len(monitor), 1)
        self.assertEqual(monitor[0]["technology"], "newrelic")

    def test_error_handling_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "@ControllerAdvice\nclass GlobalHandler:\n  pass\n")
            records = [_record("src/app.py")]
            result = detect_error_logging(repo, "acme", "widget", "abc1234", records)
        handling = [f for f in result["error_logging"] if f["category"] == "error handling"]
        self.assertEqual(len(handling), 1)
        self.assertEqual(handling[0]["technology"], "global error handling")

    def test_retry_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "@retry(stop=stop_after_attempt(3))\nasync def call(): pass\n")
            records = [_record("src/app.py")]
            result = detect_error_logging(repo, "acme", "widget", "abc1234", records)
        retry = [f for f in result["error_logging"] if f["category"] == "retry"]
        self.assertEqual(len(retry), 1)
        self.assertEqual(retry[0]["technology"], "retry behavior")

    def test_skipped_records_are_ignored(self) -> None:
        rec = _record("src/skipped.py")
        rec = FileRecord(
            path=rec.path,
            extension=rec.extension,
            size_bytes=rec.size_bytes,
            language_guess=rec.language_guess,
            role_guess=rec.role_guess,
            line_count=rec.line_count,
            source_line_count=rec.source_line_count,
            github_url=rec.github_url,
            reviewed_by_analyzer=False,
            skipped=True,
            skip_reason="too large",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_error_logging(Path(tmp), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["error_logging"], [])
        self.assertEqual(result["error_logging_total"], 0)

    def test_unreadable_record_is_ignored(self) -> None:
        # File does not exist on disk → safe_read_text returns (None, _)
        # → detector short-circuits.
        rec = _record("src/ghost.py")
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_error_logging(Path(tmp), "acme", "widget", "abc1234", [rec])
        self.assertEqual(result["error_logging"], [])

    def test_result_is_sorted_by_category_then_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/zzz.py", "import logging\n")
            _write(repo, "src/aaa.py", "import logging\n")
            records = [_record("src/zzz.py"), _record("src/aaa.py")]
            result = detect_error_logging(repo, "acme", "widget", "abc1234", records)
        # Same category, sorted by source_file.
        files = [f["source_file"] for f in result["error_logging"]]
        self.assertEqual(files, sorted(files))


class FirstMatchHelperTests(unittest.TestCase):
    def test_first_match_returns_first_needle_found(self) -> None:
        self.assertEqual(_first_match("we use sentry here", ("sentry", "datadog")), "sentry")
        self.assertEqual(_first_match("we use datadog", ("sentry", "datadog")), "datadog")

    def test_first_match_returns_first_needle_when_no_match(self) -> None:
        # Defensive fallback: when no needle matches, the function returns
        # the first needle. This means callers should only invoke
        # _first_match after a successful membership check.
        self.assertEqual(_first_match("nothing here", ("fallback1", "fallback2")), "fallback1")


if __name__ == "__main__":
    unittest.main()
