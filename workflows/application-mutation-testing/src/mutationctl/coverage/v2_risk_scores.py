"""Parse v2 (test-factory) risk_scores.json as a coverage source.

This module is part of mutationctl's coverage ingest pipeline
(see ``coverage/ingest.py``). It allows the mutation workflow to
consume the per-file risk scores produced by
``application-test-automation-v2`` (test-factory) as a first-class
coverage input.

Data contract: see ``spike/v2-coverage-spike/data_contract.md``.
"""
from __future__ import annotations

import json
from pathlib import Path

from mutationctl.models import CoverageFileSummary


V2_EVIDENCE_PREFIX = "v2://"


def _coerce_coverage(value: object) -> float | None:
    """v2 may emit null; mutation accepts None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def parse_v2_risk_scores(path: Path) -> list[CoverageFileSummary]:
    """Parse ``analysis-artifacts/risk_scores.json`` into per-file summaries.

    Schema (v2 emits one record per source file):

        {
          "path": str,                # relative to repo root
          "module": str,              # group identifier (optional in v2)
          "language": str,            # "python" | "javascript" | "java" | ...
          "line_coverage": float|null,
          "branch_coverage": float|null,
          "complexity": float,        # 0-100ish
          "churn": float,             # git churn, often 0 if no history
          "defect_history": float,    # not used by mutation's target_score
          "public_api_exposure": float,
          "data_or_security_sensitivity": float,
          "dependency_fan_in": float,
          "risk_score": float,        # v2's composite; not consumed by mutation
          "missing_evidence": list[str]
        }

    Coverage is "PASS" if line_coverage is present, "PARTIAL" if
    it's null but the record exists. covered_lines / uncovered_lines
    are empty because v2 doesn't expose per-line data; mutation's
    target_score formula does not require them. ``complexity`` is
    populated when v2 emits a non-null value; otherwise left as
    ``None`` so callers can fall back to
    ``mutationctl.targeting.scorer.complexity_score(source)``.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []

    module_hint = path.parent.name  # typically "analysis-artifacts"
    summaries: list[CoverageFileSummary] = []
    for record in raw:
        if not isinstance(record, dict):
            continue
        source_file = record.get("path")
        if not isinstance(source_file, str) or not source_file:
            continue
        line_cov = _coerce_coverage(record.get("line_coverage"))
        branch_cov = _coerce_coverage(record.get("branch_coverage"))
        complexity = _coerce_coverage(record.get("complexity"))
        record_module = record.get("module") or module_hint
        status = "PASS" if line_cov is not None else "PARTIAL"
        summaries.append(
            CoverageFileSummary(
                source_file=source_file,
                line_coverage=line_cov,
                branch_coverage=branch_cov,
                covered_lines=[],
                uncovered_lines=[],
                evidence_path=f"{V2_EVIDENCE_PREFIX}{record_module}/risk_scores.json",
                status=status,
                complexity=complexity,
            )
        )
    return summaries
