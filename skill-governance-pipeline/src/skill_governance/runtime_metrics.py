"""Runtime metrics: optional ingest of skill invocation logs.

Implements the runtime portion of Core Requirement 7.

Log format: JSON-lines, one JSON object per line. Required fields:
- artifact_name: str
- total_tokens: int
- success: bool
- timestamp: str (ISO 8601)
Optional fields:
- retries: int
- input_tokens, output_tokens: int

Aggregated per artifact: invocations, total_tokens, total_input_tokens,
total_output_tokens, retries.
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import RuntimeTokenMetrics


def ingest(log_paths) -> list[RuntimeTokenMetrics]:
    """Ingest runtime token metrics from log files.

    Args:
        log_paths: A list of Path objects, or a single Path or str.

    Returns:
        A list of RuntimeTokenMetrics, one per unique artifact_name
        across all log files. Malformed lines are skipped silently.
    """
    if isinstance(log_paths, (str, Path)):
        log_paths = [Path(log_paths)]
    log_paths = [Path(p) for p in log_paths]
    # Aggregate by artifact_name
    aggregates: dict[str, RuntimeTokenMetrics] = {}
    for log_path in log_paths:
        if not log_path.exists():
            continue
        try:
            text = log_path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
            if not isinstance(entry, dict):
                continue
            name = entry.get("artifact_name")
            if not isinstance(name, str):
                continue
            tokens = int(entry.get("total_tokens", 0) or 0)
            input_tokens = int(entry.get("input_tokens", 0) or 0)
            output_tokens = int(entry.get("output_tokens", 0) or 0)
            retries = int(entry.get("retries", 0) or 0)
            if name not in aggregates:
                aggregates[name] = RuntimeTokenMetrics(
                    artifact_name=name,
                    invocations=0,
                    total_input_tokens=0,
                    total_output_tokens=0,
                    total_tokens=0,
                    retries=0,
                )
            m = aggregates[name]
            m.invocations += 1
            m.total_input_tokens += input_tokens
            m.total_output_tokens += output_tokens
            m.total_tokens += tokens
            m.retries += retries
    return list(aggregates.values())
