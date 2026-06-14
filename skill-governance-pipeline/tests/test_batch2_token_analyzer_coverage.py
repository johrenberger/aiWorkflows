"""BDD-TDD coverage tests for token_analyzer.py (Batch 2).

Triggered by application-test-coverage assessment: token_analyzer.py
was 83% line coverage. 3 statements uncovered are in write_runtime()
(L62-64). It also has a stub `analyze_runtime` marked `pragma: no cover`.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import json
from pathlib import Path

from skill_governance.models import ArtifactType, RuntimeTokenMetrics, SkillArtifact
from skill_governance.token_analyzer import write_runtime, write_static, analyze_static


def _artifact(name: str, tokens: int) -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=name + ".md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=tokens * 4,
        estimated_tokens=tokens,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt="x",
    )


# ===========================================================================
# SCENARIO 1: write_static writes the static token costs to a JSON file
#
# Given: a list of static token costs and a tmp directory
# When:  write_static is called
# Then:  output/token_cost_static.json is created with the data
# ===========================================================================
def test_write_static_writes_token_cost_json(tmp_path: Path):
    """write_static writes output/token_cost_static.json with the data."""
    from skill_governance.models import TokenCostStatic
    costs = [TokenCostStatic(artifact_name="x", estimated_tokens=100, size_bytes=400, high_cost=False)]
    p = write_static(costs, tmp_path)
    assert p.exists()
    data = json.loads(p.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["artifact_name"] == "x"


# ===========================================================================
# SCENARIO 2: write_runtime writes the runtime metrics to a JSON file
#
# Given: a list of RuntimeTokenMetrics and a tmp directory
# When:  write_runtime is called
# Then:  output/runtime_token_metrics.json is created
# ===========================================================================
def test_write_runtime_writes_metrics_json(tmp_path: Path):
    """write_runtime writes output/runtime_token_metrics.json with the data."""
    metrics = [
        RuntimeTokenMetrics(
            artifact_name="x",
            invocations=5,
            total_input_tokens=200,
            total_output_tokens=300,
            total_tokens=500,
        )
    ]
    p = write_runtime(metrics, tmp_path)
    assert p.exists()
    data = json.loads(p.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["artifact_name"] == "x"
    assert data[0]["invocations"] == 5


# ===========================================================================
# SCENARIO 3: analyze_static computes token costs for each artifact
# ===========================================================================
def test_analyze_static_uses_4_char_per_token_heuristic():
    """analyze_static sets high_cost=True when tokens exceed threshold."""
    artifacts = [_artifact("small", 50), _artifact("large", 10000)]
    costs = analyze_static(artifacts, high_cost_threshold=8000)
    assert len(costs) == 2
    by_name = {c.artifact_name: c for c in costs}
    assert by_name["small"].high_cost is False
    assert by_name["large"].high_cost is True
