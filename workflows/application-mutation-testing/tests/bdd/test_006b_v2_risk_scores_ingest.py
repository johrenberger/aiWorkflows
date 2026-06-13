"""Story 006b (spike): v2 (test-factory) risk_scores.json as a coverage source.

This is a spike test, not a full BDD story. The full BDD story 019
will reference this file's structure.

Contract: spike/v2-coverage-spike/data_contract.md
"""
from __future__ import annotations

import json
from pathlib import Path

from mutationctl.coverage.ingest import ingest_coverage
from mutationctl.coverage.v2_risk_scores import (
    V2_EVIDENCE_PREFIX,
    parse_v2_risk_scores,
)
from mutationctl.models import CoverageFileSummary


# --- parser-level tests -------------------------------------------------------

def test_given_v2_risk_scores_json_when_parsed_then_one_summary_per_file(tmp_path: Path) -> None:
    artifact = tmp_path / "analysis-artifacts" / "risk_scores.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            [
                {"path": "src/a.py", "module": "src", "line_coverage": 80.0, "complexity": 5.0, "churn": 1.0},
                {"path": "src/b.py", "module": "src", "line_coverage": 70.0, "complexity": 3.0, "churn": 0.0},
            ]
        ),
        encoding="utf-8",
    )
    summaries = parse_v2_risk_scores(artifact)
    assert len(summaries) == 2
    assert [s.source_file for s in summaries] == ["src/a.py", "src/b.py"]


def test_given_v2_record_with_line_coverage_when_parsed_then_status_is_pass() -> None:
    fixture_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "v2_risk_scores_input"
    artifact = fixture_dir / "analysis-artifacts" / "risk_scores.json"
    summaries = parse_v2_risk_scores(artifact)
    covered = next(s for s in summaries if s.source_file == "src/covered.py")
    assert covered.status == "PASS"
    assert covered.line_coverage == 92.5
    assert covered.branch_coverage == 80.0
    assert covered.evidence_path.startswith(V2_EVIDENCE_PREFIX)


def test_given_v2_record_with_null_coverage_when_parsed_then_status_is_partial() -> None:
    fixture_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "v2_risk_scores_input"
    artifact = fixture_dir / "analysis-artifacts" / "risk_scores.json"
    summaries = parse_v2_risk_scores(artifact)
    partial = next(s for s in summaries if s.source_file == "src/partial.py")
    assert partial.status == "PARTIAL"
    assert partial.line_coverage is None
    assert partial.branch_coverage is None


def test_given_v2_record_when_parsed_then_covered_lines_is_empty() -> None:
    """v2 doesn't expose per-line data; mutation's target_score doesn't need it."""
    fixture_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "v2_risk_scores_input"
    artifact = fixture_dir / "analysis-artifacts" / "risk_scores.json"
    summaries = parse_v2_risk_scores(artifact)
    for summary in summaries:
        assert summary.covered_lines == []
        assert summary.uncovered_lines == []


def test_given_v2_record_when_parsed_then_returns_coverage_file_summary() -> None:
    fixture_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "v2_risk_scores_input"
    artifact = fixture_dir / "analysis-artifacts" / "risk_scores.json"
    summaries = parse_v2_risk_scores(artifact)
    for summary in summaries:
        assert isinstance(summary, CoverageFileSummary)


def test_given_malformed_v2_json_when_parsed_then_returns_empty() -> None:
    bad = Path("/tmp/bad_risk_scores.json")
    bad.write_text('{"not": "a list"}', encoding="utf-8")
    try:
        summaries = parse_v2_risk_scores(bad)
        assert summaries == []
    finally:
        bad.unlink(missing_ok=True)


def test_given_v2_record_missing_path_when_parsed_then_record_is_skipped(tmp_path: Path) -> None:
    artifact = tmp_path / "analysis-artifacts" / "risk_scores.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            [
                {"line_coverage": 50.0},  # no path
                {"path": "src/ok.py", "line_coverage": 80.0},
            ]
        ),
        encoding="utf-8",
    )
    summaries = parse_v2_risk_scores(artifact)
    assert len(summaries) == 1
    assert summaries[0].source_file == "src/ok.py"


# --- ingest-level tests (priority order) --------------------------------------

def test_given_v2_and_todo_coverage_when_ingested_then_v2_is_preferred(tmp_path: Path) -> None:
    """Priority 1 in the contract: v2 outranks TODO_test-coverage.md."""
    # v2 artifact
    v2_dir = tmp_path / "analysis-artifacts"
    v2_dir.mkdir()
    (v2_dir / "risk_scores.json").write_text(
        json.dumps([{"path": "src/from_v2.py", "line_coverage": 88.0}]),
        encoding="utf-8",
    )
    # TODO ledger
    (tmp_path / "TODO_test-coverage.md").write_text(
        "| Source File | Line Coverage |\n| --- | ---: |\n| src/from_todo.py | 42% |\n",
        encoding="utf-8",
    )

    result = ingest_coverage(tmp_path)
    assert result.evidence_path.endswith("risk_scores.json")
    assert result.files[0].source_file == "src/from_v2.py"
    assert result.files[0].line_coverage == 88.0


def test_given_only_todo_coverage_when_v2_absent_then_todo_is_used(tmp_path: Path) -> None:
    """Priority 2: TODO_test-coverage.md is the fallback when v2 is absent."""
    (tmp_path / "TODO_test-coverage.md").write_text(
        "| Source File | Line Coverage |\n| --- | ---: |\n| src/app.py | 91% |\n",
        encoding="utf-8",
    )
    result = ingest_coverage(tmp_path)
    assert result.evidence_path.endswith("TODO_test-coverage.md")
    assert result.files[0].source_file == "src/app.py"
    assert result.files[0].line_coverage == 91.0


def test_given_only_v2_when_other_sources_absent_then_v2_is_used(tmp_path: Path) -> None:
    v2_dir = tmp_path / "analysis-artifacts"
    v2_dir.mkdir()
    (v2_dir / "risk_scores.json").write_text(
        json.dumps([{"path": "src/lonely.py", "line_coverage": 60.0}]),
        encoding="utf-8",
    )
    result = ingest_coverage(tmp_path)
    assert result.evidence_path.endswith("risk_scores.json")
    assert result.files[0].source_file == "src/lonely.py"


def test_given_no_coverage_sources_when_ingested_then_status_is_not_run(tmp_path: Path) -> None:
    result = ingest_coverage(tmp_path)
    assert result.status == "NOT_RUN"
    assert result.files == []


def test_given_external_v2_artifact_path_when_ingested_then_v2_is_consumed(tmp_path: Path) -> None:
    """v2 may write its output to a separate --out dir; mutation must
    accept that path explicitly rather than requiring it inside the
    target repo."""
    external = tmp_path / "v2-output"
    external.mkdir()
    (external / "risk_scores.json").write_text(
        json.dumps([{"path": "src/external.py", "line_coverage": 75.0}]),
        encoding="utf-8",
    )
    target = tmp_path / "target-repo"
    target.mkdir()

    result = ingest_coverage(target, v2_artifact_path=external / "risk_scores.json")
    assert result.evidence_path.endswith("risk_scores.json")
    assert result.files[0].source_file == "src/external.py"
    assert result.files[0].line_coverage == 75.0


def test_given_external_v2_artifact_path_and_in_repo_v2_when_ingested_then_external_wins(tmp_path: Path) -> None:
    """When both an explicit v2 path and an in-repo analysis-artifacts
    exist, the explicit one wins (it's the more recent / user-specified
    choice)."""
    target = tmp_path / "target-repo"
    target.mkdir()
    in_repo = target / "analysis-artifacts"
    in_repo.mkdir(parents=True)
    (in_repo / "risk_scores.json").write_text(
        json.dumps([{"path": "src/in_repo.py", "line_coverage": 10.0}]),
        encoding="utf-8",
    )
    external = tmp_path / "external"
    external.mkdir()
    (external / "risk_scores.json").write_text(
        json.dumps([{"path": "src/explicit.py", "line_coverage": 99.0}]),
        encoding="utf-8",
    )

    result = ingest_coverage(target, v2_artifact_path=external / "risk_scores.json")
    assert result.files[0].source_file == "src/explicit.py"


# --- complexity plumbing tests (story 019 §6 + §7) ---------------------------

def test_given_v2_record_with_complexity_when_parsed_then_summary_carries_it() -> None:
    """Spike story 019 §6: v2 emits a per-file complexity value; mutation
    must surface it on the CoverageFileSummary so target_score can use it.
    """
    fixture_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "v2_risk_scores_input"
    artifact = fixture_dir / "analysis-artifacts" / "risk_scores.json"
    summaries = parse_v2_risk_scores(artifact)
    covered = next(s for s in summaries if s.source_file == "src/covered.py")
    # The fixture records complexity=5.0 for src/covered.py
    assert covered.complexity == 5.0


def test_given_v2_record_with_null_complexity_when_parsed_then_summary_complexity_is_none() -> None:
    """Spike story 019 §7: v2 may emit null complexity; mutation must
    leave CoverageFileSummary.complexity as None and let the caller
    fall back to complexity_score(source).
    """
    fixture_dir = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "v2_risk_scores_input"
    artifact = fixture_dir / "analysis-artifacts" / "risk_scores.json"
    # Build a record with explicit null complexity, append to the fixture,
    # parse, and assert the resulting summary has complexity=None.
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload.append(
        {
            "path": "src/no_complexity.py",
            "module": "src",
            "language": "python",
            "line_coverage": 50.0,
            "branch_coverage": 0.0,
            "complexity": None,
            "churn": 0.0,
            "defect_history": 0.0,
            "public_api_exposure": 0.0,
            "data_or_security_sensitivity": 0.0,
            "dependency_fan_in": 0.0,
            "risk_score": 0.0,
            "missing_evidence": ["complexity"],
        }
    )
    scratch = artifact.parent / "scratch_risk_scores.json"
    scratch.write_text(json.dumps(payload), encoding="utf-8")
    try:
        summaries = parse_v2_risk_scores(scratch)
        no_cx = next(s for s in summaries if s.source_file == "src/no_complexity.py")
        assert no_cx.complexity is None
        assert no_cx.line_coverage == 50.0  # other fields still work
    finally:
        scratch.unlink(missing_ok=True)


def test_given_summary_with_complexity_when_target_score_runs_then_v2_value_is_used(tmp_path: Path) -> None:
    """End-to-end: a CoverageFileSummary with complexity=80.0 should
    produce a higher target_score than the same coverage with the
    default fallback complexity (typically much lower for trivial files).
    """
    from mutationctl.targeting.scorer import target_score

    high_complexity = CoverageFileSummary(
        source_file="a.py",
        line_coverage=80.0,
        branch_coverage=None,
        covered_lines=[],
        uncovered_lines=[],
        evidence_path="v2://test/risk_scores.json",
        status="PASS",
        complexity=80.0,
    )
    low_complexity = CoverageFileSummary(
        source_file="a.py",
        line_coverage=80.0,
        branch_coverage=None,
        covered_lines=[],
        uncovered_lines=[],
        evidence_path="v2://test/risk_scores.json",
        status="PASS",
        complexity=5.0,
    )
    # coverage_readiness for 80% line_coverage is 80.0
    high_score = target_score(coverage=80.0, complexity=high_complexity.complexity)
    low_score = target_score(coverage=80.0, complexity=low_complexity.complexity)
    assert high_score > low_score
    # And the difference is exactly 0.25 * (80 - 5) = 18.75 per the formula
    assert abs(high_score - low_score - 18.75) < 0.01
