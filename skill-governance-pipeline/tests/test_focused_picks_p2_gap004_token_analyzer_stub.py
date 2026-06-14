"""BDD-TDD coverage tests for CTA-GAP-004: token_analyzer.analyze_runtime stub.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-GAP-004 is a P2 gap (T3 risk):

    "token_analyzer.analyze_runtime is a stub ('pragma: no cover').
    The CLI's `runtime_metrics.ingest()` is the real implementation but
    the analyzer module is what users see in the docs. Either implement
    analyze_runtime or deprecate it and remove from docs."

The gap gives two options:
1. Implement analyze_runtime properly
2. Deprecate it and remove from docs

The chosen approach is **option 2: delegation + deprecation warning**:
- analyze_runtime() now delegates to runtime_metrics.ingest() (the real
  implementation), so users get real results
- It also emits a DeprecationWarning pointing to the canonical API
- The `# pragma: no cover` is removed (since we now exercise it)
- The docstring notes the deprecation and points to runtime_metrics.ingest

This locks the contract:
- analyze_runtime(path) emits a DeprecationWarning
- analyze_runtime(path) returns the same result as runtime_metrics.ingest(path)
- The deprecation message names the canonical replacement

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

from skill_governance.models import ArtifactType, SkillArtifact
from skill_governance.runtime_metrics import ingest as runtime_ingest
from skill_governance.token_analyzer import analyze_runtime, analyze_static


def _write_log(tmp_path: Path, lines: list[dict]) -> Path:
    """Write a JSONL log file with the given entries."""
    p = tmp_path / "log.jsonl"
    p.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    return p


# ===========================================================================
# SCENARIO 1: analyze_runtime emits a DeprecationWarning
#
# Given: a JSONL log file with 1 valid runtime metrics entry
# When:  analyze_runtime is called
# Then:  a DeprecationWarning is emitted
# ===========================================================================
def test_analyze_runtime_emits_deprecation_warning(tmp_path: Path):
    """analyze_runtime() emits DeprecationWarning (it's the deprecated wrapper)."""
    log = _write_log(tmp_path, [{"artifact_name": "x", "total_tokens": 100, "retries": 0}])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        analyze_runtime([log])
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w), (
            f"expected DeprecationWarning; got: {[(warning.category.__name__, str(warning.message)) for warning in w]}"
        )


# ===========================================================================
# SCENARIO 2: analyze_runtime's result matches runtime_metrics.ingest
#
# Given: a JSONL log file with 2 valid entries
# When:  analyze_runtime([log]) is called
# Then:  the returned list equals runtime_metrics.ingest([log]) (it delegates)
# ===========================================================================
def test_analyze_runtime_delegates_to_runtime_metrics_ingest(tmp_path: Path):
    """analyze_runtime() returns the same list as runtime_metrics.ingest()."""
    log = _write_log(tmp_path, [
        {"artifact_name": "a", "total_tokens": 100, "retries": 0},
        {"artifact_name": "b", "total_tokens": 200, "retries": 1},
    ])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # suppress the deprecation
        via_analyzer = analyze_runtime([log])
    via_runtime = runtime_ingest([log])
    assert via_analyzer == via_runtime, (
        f"analyze_runtime should delegate to runtime_metrics.ingest; "
        f"got {via_analyzer} vs {via_runtime}"
    )


# ===========================================================================
# SCENARIO 3: deprecation message names the canonical replacement
#
# Given: a JSONL log file
# When:  analyze_runtime is called
# Then:  the DeprecationWarning's message mentions runtime_metrics.ingest
#        (the canonical replacement)
# ===========================================================================
def test_deprecation_message_names_canonical_replacement(tmp_path: Path):
    """The DeprecationWarning's message names the canonical replacement (runtime_metrics.ingest)."""
    log = _write_log(tmp_path, [{"artifact_name": "x", "total_tokens": 100}])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        analyze_runtime([log])
        deprecations = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecations) >= 1
        msg = str(deprecations[0].message).lower()
        assert "runtime_metrics" in msg or "ingest" in msg, (
            f"deprecation message should mention runtime_metrics.ingest; got: {msg!r}"
        )


# ===========================================================================
# SCENARIO 4: analyze_runtime handles an empty log file
#
# Given: an empty log file
# When:  analyze_runtime is called
# Then:  returns an empty list
# ===========================================================================
def test_analyze_runtime_handles_empty_log(tmp_path: Path):
    """analyze_runtime() on an empty log file returns an empty list."""
    log = tmp_path / "empty.jsonl"
    log.write_text("")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = analyze_runtime([log])
    assert result == []


# ===========================================================================
# SCENARIO 5: analyze_static still works (regression for the non-stub path)
#
# Given: a list of artifacts
# When:  analyze_static is called
# Then:  returns a TokenCostStatic per artifact, with high_cost set correctly
# ===========================================================================
def test_analyze_static_flags_high_cost_artifacts():
    """analyze_static() flags artifacts with estimated_tokens >= 8000 as high_cost."""
    artifacts = [
        SkillArtifact(
            name="small", path="small.md", artifact_type=ArtifactType.SKILL,
            size_bytes=1000, estimated_tokens=250, content_hash="x" * 64,
            modified_timestamp="2026-06-13T00:00:00Z", body_excerpt="",
        ),
        SkillArtifact(
            name="huge", path="huge.md", artifact_type=ArtifactType.SKILL,
            size_bytes=100000, estimated_tokens=25000, content_hash="x" * 64,
            modified_timestamp="2026-06-13T00:00:00Z", body_excerpt="",
        ),
    ]
    costs = analyze_static(artifacts, high_cost_threshold=8000)
    by_name = {c.artifact_name: c for c in costs}
    assert by_name["small"].high_cost is False
    assert by_name["huge"].high_cost is True
