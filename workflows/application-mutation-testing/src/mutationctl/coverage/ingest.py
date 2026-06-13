from __future__ import annotations

import os
import time
from pathlib import Path

from mutationctl.coverage.coverage_xml import parse_coverage_xml
from mutationctl.coverage.lcov import parse_lcov
from mutationctl.coverage.todo_coverage import parse_todo_coverage
from mutationctl.coverage.v2_risk_scores import parse_v2_risk_scores
from mutationctl.models import CoverageSummary


# Default threshold for considering a v2 (test-factory) artifact stale.
# If the artifact's mtime is more than this many seconds older than
# the repo root's mtime (used as a proxy for the most recent change
# in the working tree), mutation treats it as stale and falls back
# to the next available coverage source.
DEFAULT_V2_MAX_AGE_HOURS = 24
DEFAULT_V2_MAX_AGE_SECONDS = DEFAULT_V2_MAX_AGE_HOURS * 60 * 60


def _candidate_paths(root: Path, v2_artifact_path: str | Path | None = None) -> list[Path]:
    """Return coverage-source candidates in priority order.

    Priority 1: v2 (test-factory) ``risk_scores.json`` —
        machine-authored, per-file coverage + complexity + churn.
        See ``spike/v2-coverage-spike/data_contract.md`` for the contract.
        Resolved from ``v2_artifact_path`` if given, else from the
        in-repo default ``<root>/analysis-artifacts/risk_scores.json``.
        Subject to ``v2_max_age_seconds`` staleness check (story 019 open 3).
    Priority 2: human-authored ``TODO_test-coverage.md`` ledger.
    Priority 3: standard coverage reports (Cobertura XML, LCOV, JaCoCo).
    """
    v2_default = root / "analysis-artifacts" / "risk_scores.json"
    v2_path = Path(v2_artifact_path) if v2_artifact_path is not None else v2_default
    return [
        v2_path,
        root / "TODO_test-coverage.md",
        root / "coverage.xml",
        root / "lcov.info",
        root / "jacoco.xml",
    ]


def _is_v2_artifact_stale(
    v2_artifact: Path,
    repo_root: Path,
    max_age_seconds: int = DEFAULT_V2_MAX_AGE_SECONDS,
) -> bool:
    """Return True if ``v2_artifact`` is older than ``max_age_seconds``
    relative to the repo root's mtime.

    The repo root's mtime is a stand-in for the most recent change in
    the working tree. We deliberately do not use git commit time here
    because the workflow may run against an uncommitted working tree
    (e.g. mid-fix), and we want the staleness check to reflect
    reality of the files on disk.
    """
    if not v2_artifact.is_file():
        return False
    artifact_mtime = v2_artifact.stat().st_mtime
    try:
        repo_mtime = repo_root.stat().st_mtime
    except FileNotFoundError:
        return False
    return (repo_mtime - artifact_mtime) > max_age_seconds


def ingest_coverage(
    repo_path: str | Path,
    coverage_path: str | Path | None = None,
    store=None,
    v2_artifact_path: str | Path | None = None,
    v2_max_age_seconds: int = DEFAULT_V2_MAX_AGE_SECONDS,
) -> CoverageSummary:
    root = Path(repo_path)
    if coverage_path is not None:
        candidates = [Path(coverage_path)]
    else:
        candidates = _candidate_paths(root, v2_artifact_path=v2_artifact_path)
    # If the v2 candidate (priority 1) exists but is stale relative to
    # the repo root, drop it from the candidate list so the next
    # priority source wins. (story 019 open 3)
    if coverage_path is None and v2_max_age_seconds > 0:
        v2_candidate = candidates[0]
        if v2_candidate.is_file() and _is_v2_artifact_stale(
            v2_candidate, root, v2_max_age_seconds
        ):
            candidates = candidates[1:]
    selected = next((path for path in candidates if path.is_file()), None)
    if selected is None:
        result = CoverageSummary(None, None, None, [], [], None, "NOT_RUN", [])
    else:
        if selected.name == "risk_scores.json":
            # v2's risk_scores.json may live in either an in-repo
            # ``analysis-artifacts/`` dir (default) or a user-supplied
            # external --out dir. Both are valid; detect by filename
            # alone to keep the contract simple.
            files = parse_v2_risk_scores(selected)
        elif selected.name == "TODO_test-coverage.md":
            files = parse_todo_coverage(selected)
        elif selected.suffix.lower() == ".info":
            files = parse_lcov(selected)
        elif selected.name == "jacoco.xml":
            files = []
        else:
            files = parse_coverage_xml(selected)
        result = CoverageSummary(
            files[0].source_file if len(files) == 1 else None,
            files[0].line_coverage if len(files) == 1 else None,
            files[0].branch_coverage if len(files) == 1 else None,
            files[0].covered_lines if len(files) == 1 else [],
            files[0].uncovered_lines if len(files) == 1 else [],
            str(selected),
            "PASS" if files else "NOT_RUN",
            files,
        )
    if store is not None:
        store.record_coverage_summary(result)
    return result
