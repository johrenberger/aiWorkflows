"""BDD-TDD coverage tests for CTA-GAP-009: history.trend() per-metric deltas.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-GAP-009 is a P2 gap (T3 risk):

    "history.trend() is implemented but not tested. Need tests for
    the trend shape: delta_health, delta_findings, delta_blocking
    over a sequence of HistoryEntries."

The current trend() returns:
    {"runs", "last_health", "oldest_health", "delta", "first_run", "last_run"}

The gap calls for per-metric deltas:
    delta_health, delta_findings, delta_blocking

The `delta` key is the current alias for delta_health. The new keys
(delta_findings, delta_blocking) are added by the fix.

These tests lock:
- trend(3 entries, health 50->60->70, findings 10->8->5, blocking 5->3->2)
  -> dict with delta_health=20, delta_findings=-5, delta_blocking=-3
- trend(1 entry) -> delta_*=0
- trend(0 entries) -> {"runs": 0} (no deltas)
- Trend is computed as newest - oldest (newest has the latest timestamp)

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
- Red-phase: tests fail against the current code (red)
- Green-phase: tests pass after fixing `trend()`
"""
from __future__ import annotations

from skill_governance.history import HistoryEntry, trend


def _entry(timestamp: str, health: int, finding_count: int, blocking: int) -> HistoryEntry:
    return HistoryEntry(
        timestamp=timestamp,
        health_score=health,
        ci_blocking_count=blocking,
        inventory_count=100,
        finding_count=finding_count,
        decision_distribution={},
        waiver_count=0,
    )


# ===========================================================================
# SCENARIO 1: trend(3 entries) returns per-metric deltas
#
# Given: 3 HistoryEntries in DESC order (newest first, matching
#        read_all's output) with health 70, 60, 50 and finding counts
#        5, 8, 10 and blocking 2, 3, 5
# When:  trend() is called
# Then:  delta_health=20 (70-50), delta_findings=-5 (5-10), delta_blocking=-3 (2-5)
# ===========================================================================
def test_trend_returns_per_metric_deltas_for_three_entries():
    """trend() with 3 entries returns delta_health=20, delta_findings=-5, delta_blocking=-3.

    The trend() function operates on entries in DESC order (newest first),
    matching the output of read_all(). entries[0] is treated as newest.
    """
    entries = [
        _entry("2026-06-13T22:00:00Z", health=70, finding_count=5, blocking=2),   # newest (entries[0])
        _entry("2026-06-13T16:00:00Z", health=60, finding_count=8, blocking=3),
        _entry("2026-06-13T10:00:00Z", health=50, finding_count=10, blocking=5),  # oldest (entries[-1])
    ]
    t = trend(entries)
    assert t.get("delta_health") == 20, f"expected delta_health=20, got {t.get('delta_health')}"
    assert t.get("delta_findings") == -5, f"expected delta_findings=-5, got {t.get('delta_findings')}"
    assert t.get("delta_blocking") == -3, f"expected delta_blocking=-3, got {t.get('delta_blocking')}"
    assert t["runs"] == 3


# ===========================================================================
# SCENARIO 2: trend(1 entry) returns zeros for all deltas
#
# Given: a single HistoryEntry
# When:  trend() is called
# Then:  delta_health=0, delta_findings=0, delta_blocking=0
# ===========================================================================
def test_trend_returns_zeros_for_single_entry():
    """trend() with 1 entry has no delta (newest == oldest)."""
    entries = [_entry("2026-06-13T22:00:00Z", health=80, finding_count=10, blocking=2)]
    t = trend(entries)
    assert t.get("delta_health") == 0
    assert t.get("delta_findings") == 0
    assert t.get("delta_blocking") == 0
    assert t["runs"] == 1


# ===========================================================================
# SCENARIO 3: trend(0 entries) returns the no-runs shape
#
# Given: empty history
# When:  trend() is called
# Then:  returns {"runs": 0} (no deltas to compute)
# ===========================================================================
def test_trend_returns_no_runs_shape_for_empty_history():
    """trend([]) returns {"runs": 0} and does not crash on missing keys."""
    t = trend([])
    assert t["runs"] == 0


# ===========================================================================
# SCENARIO 4: trend computes deltas as (newest - oldest)
#
# Given: 2 entries in DESC order (newest entries[0]=health 90, oldest entries[-1]=health 30)
# When:  trend() is called
# Then:  delta_health = 90 - 30 = 60 (positive, because newest > oldest)
# ===========================================================================
def test_trend_delta_is_newest_minus_oldest_health():
    """trend() delta_health = entries[0].health - entries[-1].health."""
    entries = [
        _entry("2026-06-13T22:00:00Z", health=90, finding_count=2, blocking=0),   # newest
        _entry("2026-06-13T10:00:00Z", health=30, finding_count=20, blocking=10),  # oldest
    ]
    t = trend(entries)
    assert t["delta_health"] == 60  # 90 - 30
    assert t["delta_findings"] == -18  # 2 - 20
    assert t["delta_blocking"] == -10  # 0 - 10


# ===========================================================================
# SCENARIO 5: trend works with negative deltas (regression)
#
# Given: 2 entries (newest health 30, oldest health 90) - regression case
# When:  trend() is called
# Then:  delta_health = 30 - 90 = -60 (negative)
# ===========================================================================
def test_trend_supports_negative_deltas():
    """trend() supports negative deltas (regression over time)."""
    entries = [
        _entry("2026-06-13T22:00:00Z", health=30, finding_count=20, blocking=10),  # newest
        _entry("2026-06-13T10:00:00Z", health=90, finding_count=2, blocking=0),    # oldest
    ]
    t = trend(entries)
    assert t["delta_health"] == -60
    assert t["delta_findings"] == 18
    assert t["delta_blocking"] == 10
