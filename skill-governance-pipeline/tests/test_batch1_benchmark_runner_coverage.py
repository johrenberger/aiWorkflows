"""BDD-TDD coverage tests for benchmark_runner.py (Batch 1).

Triggered by application-test-coverage assessment: benchmark_runner.py
was 86% line coverage. 10 statements uncovered in:
- `_load_fixtures`: YAML error skip, dict vs list, nested dict
- `_score_fixture`: str expected, list expected, no expected

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from pathlib import Path

import yaml

from skill_governance.benchmark_runner import _load_fixtures, _score_fixture
from skill_governance.models import ArtifactType, SkillArtifact


def _artifact(body: str) -> SkillArtifact:
    return SkillArtifact(
        name="x",
        path="x.md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=100,
        estimated_tokens=25,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt=body,
    )


# ===========================================================================
# SCENARIO 1: _load_fixtures handles a single-dict YAML file
#
# Given: a YAML file with a single dict (not a list) that has
#        "artifact_name" key
# When:  _load_fixtures is called
# Then:  the result contains one entry (the dict)
# ===========================================================================
def test_load_fixtures_handles_single_dict_with_artifact_name(tmp_path: Path):
    """A YAML file with a single dict (and artifact_name) is loaded as 1 entry."""
    bench_dir = tmp_path / "bench"
    bench_dir.mkdir()
    (bench_dir / "single.yaml").write_text(
        yaml.dump({"artifact_name": "x", "field": "value"})
    )
    result = _load_fixtures(bench_dir)
    assert len(result) == 1, f"expected 1 entry, got {len(result)}"
    assert result[0]["artifact_name"] == "x"


# ===========================================================================
# SCENARIO 2: _load_fixtures handles a list YAML file
# ===========================================================================
def test_load_fixtures_handles_list_of_dicts(tmp_path: Path):
    """A YAML list of dicts is loaded as multiple entries."""
    bench_dir = tmp_path / "bench"
    bench_dir.mkdir()
    (bench_dir / "list.yaml").write_text(
        yaml.dump([{"artifact_name": "a"}, {"artifact_name": "b"}])
    )
    result = _load_fixtures(bench_dir)
    assert len(result) == 2, f"expected 2 entries, got {len(result)}"


# ===========================================================================
# SCENARIO 3: _load_fixtures handles a nested-dict YAML file
# ===========================================================================
def test_load_fixtures_handles_nested_dict(tmp_path: Path):
    """A YAML dict-of-dicts is loaded as multiple entries (inner dicts)."""
    bench_dir = tmp_path / "bench"
    bench_dir.mkdir()
    (bench_dir / "nested.yaml").write_text(
        yaml.dump({"a": {"artifact_name": "x"}, "b": {"artifact_name": "y"}, "c": "skip"})
    )
    result = _load_fixtures(bench_dir)
    assert len(result) == 2, f"expected 2 entries (x, y), got {len(result)}"
    names = {r["artifact_name"] for r in result}
    assert names == {"x", "y"}, f"unexpected names: {names}"


# ===========================================================================
# SCENARIO 4: _load_fixtures skips YAML files with errors
# ===========================================================================
def test_load_fixtures_skips_malformed_yaml(tmp_path: Path):
    """A YAML file with a parse error is silently skipped."""
    bench_dir = tmp_path / "bench"
    bench_dir.mkdir()
    (bench_dir / "bad.yaml").write_text("this is: not valid: yaml: at: all")
    result = _load_fixtures(bench_dir)
    assert result == [], f"expected empty list, got {result}"


# ===========================================================================
# SCENARIO 5: _score_fixture with str expected matches if str in body
# ===========================================================================
def test_score_fixture_str_expected_matches_in_body():
    """A rule with str expected passes if the string appears in the body."""
    fixture = {
        "artifact_name": "x",
        "scoring_rules": [{"field": "purpose", "expected": "error", "weight": 1.0}],
    }
    score, detail = _score_fixture(fixture, _artifact("this body has an error message"))
    assert score == 1.0, f"expected 1.0 (match), got {score}"
    assert detail["rule_results"][0]["passed"] is True


# ===========================================================================
# SCENARIO 6: _score_fixture with list expected matches if all in body
# ===========================================================================
def test_score_fixture_list_expected_matches_all_in_body():
    """A rule with list expected passes if all strings appear in body."""
    fixture = {
        "artifact_name": "x",
        "scoring_rules": [{"field": "purpose", "expected": ["error", "report"], "weight": 1.0}],
    }
    score, detail = _score_fixture(fixture, _artifact("this body has an error and a report"))
    assert score == 1.0, f"expected 1.0 (match), got {score}"


# ===========================================================================
# SCENARIO 7: _score_fixture with no expected just checks field name in body
# ===========================================================================
def test_score_fixture_none_expected_checks_field_name_in_body():
    """A rule with no expected passes if the field name appears in body."""
    fixture = {
        "artifact_name": "x",
        "scoring_rules": [{"field": "purpose", "expected": None, "weight": 1.0}],
    }
    score, detail = _score_fixture(fixture, _artifact("this body mentions the purpose"))
    assert score == 1.0, f"expected 1.0 (field-name match), got {score}"
