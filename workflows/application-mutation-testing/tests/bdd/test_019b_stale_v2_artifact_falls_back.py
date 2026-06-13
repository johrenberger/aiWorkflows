"""Story 019, open 3: stale v2 (test-factory) artifact detection.

If ``analysis-artifacts/risk_scores.json`` is older than the repo's
HEAD commit by more than ``v2_max_age_hours`` (default 24h), the v2
artifact is treated as stale and mutation falls back to the next
available coverage source (TODO_test-coverage.md, coverage.xml, etc.).

Tests-first: this test should FAIL on master because no stale
detection exists today. The current ``ingest_coverage`` consumes
the v2 artifact unconditionally as long as the file exists,
regardless of how stale it is.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from mutationctl.coverage.ingest import ingest_coverage


def test_given_v2_artifact_older_than_threshold_when_ingested_then_v2_is_skipped(
    tmp_path: Path,
) -> None:
    """Open 3: a v2 artifact whose mtime is > 24h older than the repo's
    HEAD commit should be treated as stale. mutation must NOT consume
    it; instead it should fall back to the next priority source.
    """
    # Stale v2 artifact: file mtime set to 3 days ago
    v2_dir = tmp_path / "analysis-artifacts"
    v2_dir.mkdir(parents=True)
    v2_artifact = v2_dir / "risk_scores.json"
    v2_artifact.write_text(
        json.dumps([{"path": "src/stale.py", "line_coverage": 99.0}]),
        encoding="utf-8",
    )
    three_days_ago = time.time() - (3 * 24 * 60 * 60)
    import os
    os.utime(v2_artifact, (three_days_ago, three_days_ago))

    # TODO_test-coverage.md is the fallback we expect to be picked
    (tmp_path / "TODO_test-coverage.md").write_text(
        "| Source File | Line Coverage |\n| --- | ---: |\n| src/fallback.py | 50% |\n",
        encoding="utf-8",
    )

    # Set the repo mtime to NOW so the v2 artifact is 3 days older
    # than the repo.
    repo_now = time.time()
    os.utime(tmp_path, (repo_now, repo_now))

    result = ingest_coverage(tmp_path)

    # The v2 artifact must NOT be selected; the TODO must be
    assert result.evidence_path.endswith("TODO_test-coverage.md"), (
        f"Expected fallback to TODO_test-coverage.md for stale v2; "
        f"got evidence_path={result.evidence_path!r}"
    )


def test_given_fresh_v2_artifact_when_ingested_then_v2_is_consumed(
    tmp_path: Path,
) -> None:
    """Counterpart: a v2 artifact that is fresh (mtime within
    threshold of repo HEAD) should be consumed normally.
    """
    v2_dir = tmp_path / "analysis-artifacts"
    v2_dir.mkdir(parents=True)
    v2_artifact = v2_dir / "risk_scores.json"
    v2_artifact.write_text(
        json.dumps([{"path": "src/fresh.py", "line_coverage": 70.0}]),
        encoding="utf-8",
    )
    # Both v2 artifact and repo mtime = now (fresh)
    now = time.time()
    import os
    os.utime(v2_artifact, (now, now))
    os.utime(tmp_path, (now, now))

    result = ingest_coverage(tmp_path)
    assert result.evidence_path.endswith("risk_scores.json")
    assert result.files[0].source_file == "src/fresh.py"


def test_given_v2_artifact_just_under_threshold_when_ingested_then_v2_is_consumed(
    tmp_path: Path,
) -> None:
    """Boundary: a v2 artifact that is just under the 24h threshold
    must be considered fresh.
    """
    v2_dir = tmp_path / "analysis-artifacts"
    v2_dir.mkdir(parents=True)
    v2_artifact = v2_dir / "risk_scores.json"
    v2_artifact.write_text(
        json.dumps([{"path": "src/borderline.py", "line_coverage": 70.0}]),
        encoding="utf-8",
    )
    # 12h ago = within 24h threshold
    twelve_hours_ago = time.time() - (12 * 60 * 60)
    import os
    os.utime(v2_artifact, (twelve_hours_ago, twelve_hours_ago))

    now = time.time()
    os.utime(tmp_path, (now, now))

    result = ingest_coverage(tmp_path)
    assert result.evidence_path.endswith("risk_scores.json"), (
        f"v2 artifact within threshold should be consumed; "
        f"got evidence_path={result.evidence_path!r}"
    )
