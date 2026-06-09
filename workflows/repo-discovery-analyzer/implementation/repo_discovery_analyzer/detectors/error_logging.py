from __future__ import annotations

from pathlib import Path

from ..io_utils import safe_read_text
from ..model import FileRecord


def detect_error_logging(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    for record in records:
        if record.skipped:
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        lowered = text.lower()
        if any(term in lowered for term in ("logger", "logging", "log4j", "slf4j", "winston", "pino", "bunyan")):
            findings.append(_f("logging", "logger usage", record))
        if any(term in lowered for term in ("sentry", "@sentry", "datadog", "opentelemetry", "prometheus", "newrelic")):
            findings.append(_f("monitoring/telemetry", _first_match(lowered, ("sentry", "datadog", "opentelemetry", "prometheus", "newrelic")), record))
        if any(term in lowered for term in ("exceptionhandler", "controlleradvice", "middleware", "errorhandler", "global error")):
            findings.append(_f("error handling", "global error handling", record))
        if any(term in lowered for term in ("retry", "backoff", "resilience4j", "tenacity")):
            findings.append(_f("retry", "retry behavior", record))
    return {"error_logging": sorted(findings, key=lambda x: (x["category"], x["source_file"]))}


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

