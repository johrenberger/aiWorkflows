"""Tests for the benchmark runner (CR 9)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from skill_governance.benchmark_runner import (
    benchmark_findings,
    run_benchmarks,
)
from skill_governance.models import ArtifactType, SkillArtifact

FIXTURES = Path(__file__).parent / "fixtures"
BENCHMARKS = Path(__file__).parent / "benchmarks"


def _artifact(name: str, body: str) -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=name + ".md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=len(body),
        estimated_tokens=max(1, len(body) // 4),
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt=body,
    )


def test_benchmark_loads_yaml_fixtures():
    """The sample benchmark fixture is loaded and returned."""
    artifact = _artifact(
        "skills/valid",
        "name: valid-skill\nartifact_type: skill\npurpose: validate coverage\noutputs: format: json, fields: result",
    )
    results = run_benchmarks([artifact], BENCHMARKS)
    assert len(results) == 1
    r = results[0]
    assert r.artifact_name == "skills/valid"
    assert r.benchmark_name == "valid-skill-must-have-metadata"
    # All rules should pass for a body that has the right tokens
    assert r.score >= 0.7
    assert r.passed is True


def test_benchmark_fails_for_missing_content():
    """A body missing the expected content fails the benchmark."""
    artifact = _artifact("skills/valid", "totally unrelated content about something else")
    results = run_benchmarks([artifact], BENCHMARKS)
    assert len(results) == 1
    assert results[0].passed is False
    # And surfaces as a blocking finding
    findings = benchmark_findings(results)
    assert any(f.severity.value == "blocking" for f in findings)
    assert any("benchmark" in f.category for f in findings)


def test_benchmark_for_missing_artifact_fails():
    """A fixture for a non-existent artifact fails the benchmark."""
    results = run_benchmarks([], BENCHMARKS)
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].score == 0.0


def test_empty_benchmark_dir_yields_no_results():
    """No fixtures = no results."""
    with tempfile.TemporaryDirectory() as tmp:
        results = run_benchmarks([], Path(tmp))
        assert results == []


def test_multiple_fixtures_each_get_a_result():
    """Two fixtures produce two results."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "a.yaml").write_text(
            "artifact_name: a\nbenchmark_name: bench-a\nscoring_rules: []\nminimum_score: 0.5\n"
        )
        (d / "b.yaml").write_text(
            "artifact_name: b\nbenchmark_name: bench-b\nscoring_rules: []\nminimum_score: 0.5\n"
        )
        a = _artifact("a", "anything")
        b = _artifact("b", "anything")
        results = run_benchmarks([a, b], d)
        assert len(results) == 2
        names = {r.artifact_name for r in results}
        assert names == {"a", "b"}
        # Empty rules => score 1.0, both pass
        assert all(r.passed for r in results)
