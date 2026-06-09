from __future__ import annotations

from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, safe_read_text
from ..model import FileRecord


def detect_error_logging(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    total_count = 0

    def add(finding: dict) -> None:
        nonlocal total_count
        total_count += 1
        if len(findings) < DEFAULT_MAX_SUMMARY_ITEMS:
            findings.append(finding)

    for record in records:
        if record.skipped:
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        lowered = text.lower()
        if any(term in lowered for term in ("logger", "logging", "log4j", "slf4j", "winston", "pino", "bunyan")):
            add(_f("logging", "logger usage", record))
        if any(term in lowered for term in ("sentry", "@sentry", "datadog", "opentelemetry", "prometheus", "newrelic")):
            add(_f("monitoring/telemetry", _first_match(lowered, ("sentry", "datadog", "opentelemetry", "prometheus", "newrelic")), record))
        if any(term in lowered for term in ("exceptionhandler", "controlleradvice", "middleware", "errorhandler", "global error")):
            add(_f("error handling", "global error handling", record))
        if any(term in lowered for term in ("retry", "backoff", "resilience4j", "tenacity")):
            add(_f("retry", "retry behavior", record))
    return {
        "error_logging": sorted(findings, key=lambda x: (x["category"], x["source_file"])),
        "error_logging_total": total_count,
        "error_logging_truncated": total_count > len(findings),
    }


def _f(category: str, technology: str, record: FileRecord) -> dict:
    return {
        "category": category,
        "technology": technology,
        "source_file": record.path,
        "github_url": record.github_url,
        "confidence": "medium",
    }


def _first_match(text: str, needles: tuple[str, ...]) -> str:
    for needle in needles:
        if needle in text:
            return needle
    return needles[0]
