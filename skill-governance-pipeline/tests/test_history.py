"""Tests for the governance history module."""
from __future__ import annotations

import tempfile
from pathlib import Path

from skill_governance.history import (
    HistoryEntry,
    append,
    read_all,
    snapshot,
    trend,
)
from skill_governance.models import (
    Decision,
    PipelineResult,
    ScorecardEntry,
)


def test_snapshot_captures_pipeline_state():
    """snapshot() returns a HistoryEntry with the right fields."""
    result = PipelineResult(
        inventory=[],  # 0 artifacts
        findings=[],
        scorecards=[
            ScorecardEntry(artifact_name="a", roi_score=80, decision=Decision.KEEP, rationale="ok"),
            ScorecardEntry(artifact_name="b", roi_score=30, decision=Decision.MERGE, rationale="dup"),
        ],
        health_score=70,
        ci_blocking_count=2,
        finished_at="2026-06-13T22:00:00Z",
    )
    entry = snapshot(result, note="unit test")
    assert entry.health_score == 70
    assert entry.ci_blocking_count == 2
    assert entry.inventory_count == 0
    assert entry.finding_count == 0
    assert entry.decision_distribution == {"keep": 1, "merge": 1}
    assert entry.note == "unit test"


def test_append_and_read_round_trip(tmp_path):
    """append() + read_all() round-trip preserves entries."""
    p = tmp_path / "history.jsonl"
    entry1 = HistoryEntry(
        timestamp="2026-06-13T10:00:00Z", health_score=80, ci_blocking_count=2,
        inventory_count=100, finding_count=5, decision_distribution={"keep": 100},
        waiver_count=0,
    )
    entry2 = HistoryEntry(
        timestamp="2026-06-13T22:00:00Z", health_score=70, ci_blocking_count=4,
        inventory_count=120, finding_count=8, decision_distribution={"rewrite": 120},
        waiver_count=1,
    )
    append(p, entry1)
    append(p, entry2)
    history = read_all(p)
    assert len(history) == 2
    # Sorted most-recent first
    assert history[0].timestamp == "2026-06-13T22:00:00Z"
    assert history[1].timestamp == "2026-06-13T10:00:00Z"


def test_trend_with_no_history():
    """Empty history returns 0 runs."""
    assert trend([])["runs"] == 0


def test_trend_computes_delta():
    """Trend shows delta between newest and oldest health scores."""
    entries = [
        HistoryEntry(
            timestamp="2026-06-13T22:00:00Z", health_score=80, ci_blocking_count=0,
            inventory_count=100, finding_count=0, decision_distribution={}, waiver_count=0,
        ),
        HistoryEntry(
            timestamp="2026-06-13T10:00:00Z", health_score=60, ci_blocking_count=4,
            inventory_count=100, finding_count=10, decision_distribution={}, waiver_count=0,
        ),
    ]
    t = trend(entries)
    assert t["runs"] == 2
    assert t["last_health"] == 80
    assert t["oldest_health"] == 60
    assert t["delta"] == 20


def test_read_all_handles_missing_file(tmp_path):
    """Missing history file returns empty list."""
    assert read_all(tmp_path / "missing.jsonl") == []
