"""Runtime metrics: optional ingest of skill invocation logs.

Implements the runtime portion of Core Requirement 7.

Phase 1: stub.
Phase 5: real log parser.
"""
from __future__ import annotations

from pathlib import Path

from .models import RuntimeTokenMetrics


def ingest(log_paths: list[Path]) -> list[RuntimeTokenMetrics]:  # pragma: no cover - stub
    """Ingest runtime token metrics from log files."""
    return []
