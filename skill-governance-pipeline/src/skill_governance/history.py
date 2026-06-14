"""Governance history: track pipeline runs over time.

Implements the history portion of Core Requirement 5 (Phase 5).

Each pipeline run produces a snapshot. History is persisted
as a JSONL file at `output/governance_history.jsonl` so
trends (health score, blocking count, decision distribution)
can be computed across runs.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import PipelineResult


@dataclass
class HistoryEntry:
    """A single pipeline run snapshot."""

    timestamp: str  # ISO 8601 UTC, Z
    health_score: int
    ci_blocking_count: int
    inventory_count: int
    finding_count: int
    decision_distribution: dict[str, int]
    waiver_count: int
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def snapshot(result: PipelineResult, note: str = "") -> HistoryEntry:
    """Build a HistoryEntry from a PipelineResult."""
    decision_dist: dict[str, int] = {}
    for s in result.scorecards:
        d = s.decision.value
        decision_dist[d] = decision_dist.get(d, 0) + 1
    return HistoryEntry(
        timestamp=result.finished_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        health_score=result.health_score,
        ci_blocking_count=result.ci_blocking_count,
        inventory_count=len(result.inventory),
        finding_count=len(result.findings),
        decision_distribution=decision_dist,
        waiver_count=len(result.waivers),
        note=note,
    )


def append(history_path: Path, entry: HistoryEntry) -> None:
    """Append a history entry to the JSONL file."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict(), sort_keys=True) + "\n")


def read_all(history_path: Path) -> list[HistoryEntry]:
    """Read all history entries (most recent first)."""
    if not history_path.exists():
        return []
    out: list[HistoryEntry] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.append(HistoryEntry(
            timestamp=data.get("timestamp", ""),
            health_score=int(data.get("health_score", 0)),
            ci_blocking_count=int(data.get("ci_blocking_count", 0)),
            inventory_count=int(data.get("inventory_count", 0)),
            finding_count=int(data.get("finding_count", 0)),
            decision_distribution=dict(data.get("decision_distribution", {})),
            waiver_count=int(data.get("waiver_count", 0)),
            note=str(data.get("note", "")),
        ))
    out.sort(key=lambda e: e.timestamp, reverse=True)
    return out


def trend(history: Iterable[HistoryEntry]) -> dict:
    """Compute a simple trend summary across the last N entries.

    The trend dict includes per-metric deltas (delta_health, delta_findings,
    delta_blocking) computed as (newest - oldest) across the supplied
    entries. The single-metric `delta` key is preserved for backward
    compatibility (it equals `delta_health`).
    """
    entries = list(history)
    if not entries:
        return {"runs": 0}
    newest = entries[0]
    oldest = entries[-1]
    delta_health = newest.health_score - oldest.health_score
    delta_findings = newest.finding_count - oldest.finding_count
    delta_blocking = newest.ci_blocking_count - oldest.ci_blocking_count
    return {
        "runs": len(entries),
        "last_health": newest.health_score,
        "oldest_health": oldest.health_score,
        "delta": delta_health,
        "delta_health": delta_health,
        "delta_findings": delta_findings,
        "delta_blocking": delta_blocking,
        "first_run": oldest.timestamp,
        "last_run": newest.timestamp,
    }
