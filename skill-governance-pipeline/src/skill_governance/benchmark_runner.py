"""Benchmark framework: validate skills against fixtures.

Implements Core Requirement 9.

Each benchmark fixture defines:
- artifact_name: which skill this fixture targets
- input_context: a JSON-serializable input dict
- expected_outputs: a list of expected output shapes
- scoring_rules: a list of {field, expected, weight} rules
- minimum_score: 0.0-1.0 pass threshold
- edge_cases: optional list of additional contexts

The runner:
1. Loads every YAML fixture in `benchmark_dir/`.
2. For each fixture, "invokes" the skill (Phase 4: by reading
   the body and checking the scoring rules; Phase 5: by calling
   the skill with the input context).
3. Computes a score = sum(weight * pass) / sum(weight).
4. Returns a BenchmarkResult per fixture.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import BenchmarkResult, Finding, Severity, SkillArtifact


def _load_fixtures(benchmark_dir: Path) -> list[dict[str, Any]]:
    """Load every YAML fixture from benchmark_dir."""
    if not benchmark_dir.exists():
        return []
    out: list[dict[str, Any]] = []
    for f in sorted(benchmark_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(data, list):
            out.extend(e for e in data if isinstance(e, dict))
        elif isinstance(data, dict):
            # If it has 'artifact_name', it's a single fixture
            if "artifact_name" in data:
                out.append(data)
            # Otherwise, it may be a map of name -> fixture
            else:
                for v in data.values():
                    if isinstance(v, dict) and "artifact_name" in v:
                        out.append(v)
    return out


def _score_fixture(
    fixture: dict[str, Any], artifact: SkillArtifact | None
) -> tuple[float, dict[str, Any]]:
    """Score a single fixture against an artifact.

    Phase 4 scoring:
    - For each rule in scoring_rules:
      - If artifact is None, rule fails (0)
      - If expected is a string, check the artifact's body_excerpt
        contains it (case-insensitive)
      - If expected is a list, check all items appear in the body
      - Otherwise, fail
    - score = sum(passing_weight) / sum(total_weight)
    """
    if artifact is None:
        return 0.0, {"reason": "artifact not found"}
    rules = fixture.get("scoring_rules", [])
    if not rules:
        return 1.0, {"reason": "no rules"}
    body = (artifact.body_excerpt or "").lower()
    total_weight = 0.0
    earned = 0.0
    rule_results: list[dict[str, Any]] = []
    for rule in rules:
        weight = float(rule.get("weight", 1.0))
        total_weight += weight
        expected = rule.get("expected")
        field = rule.get("field", "")
        passed = False
        if isinstance(expected, str):
            passed = expected.lower() in body
        elif isinstance(expected, list):
            passed = all(str(e).lower() in body for e in expected)
        elif expected is None and field:
            # Just check the field name appears in the body
            passed = field.lower() in body
        if passed:
            earned += weight
        rule_results.append({"field": field, "expected": expected, "weight": weight, "passed": passed})
    score = (earned / total_weight) if total_weight > 0 else 0.0
    return score, {"rule_results": rule_results}


def run_benchmarks(
    artifacts: list[SkillArtifact],
    benchmark_dir: Path,
    default_minimum: float = 0.7,
) -> list[BenchmarkResult]:
    """Run every benchmark fixture and return one result per fixture.

    Args:
        artifacts: The discovered artifacts.
        benchmark_dir: Directory of `*.yaml` benchmark fixtures.
        default_minimum: Default pass threshold if a fixture
            does not specify `minimum_score`.
    """
    fixtures = _load_fixtures(benchmark_dir)
    if not fixtures:
        return []
    by_name: dict[str, SkillArtifact] = {a.name: a for a in artifacts}
    # Also map by stem (last component of name)
    for a in artifacts:
        by_name.setdefault(a.name.split("/")[-1], a)
    results: list[BenchmarkResult] = []
    for fx in fixtures:
        target = fx.get("artifact_name", "")
        minimum = float(fx.get("minimum_score", default_minimum))
        benchmark_name = fx.get("benchmark_name", f"{target}-benchmark")
        artifact = by_name.get(target)
        score, evidence = _score_fixture(fx, artifact)
        passed = score >= minimum
        results.append(
            BenchmarkResult(
                artifact_name=target,
                benchmark_name=benchmark_name,
                passed=passed,
                score=score,
                minimum_score=minimum,
                evidence={"fixture": fx, "scoring": evidence, "found": artifact is not None},
            )
        )
    return results


def benchmark_findings(results: list[BenchmarkResult]) -> list[Finding]:
    """Convert benchmark results to governance findings."""
    findings: list[Finding] = []
    for r in results:
        if not r.passed:
            findings.append(
                Finding(
                    finding_id=f"benchmark.failed.{r.artifact_name}.{r.benchmark_name}",
                    artifact_name=r.artifact_name,
                    severity=Severity.BLOCKING,
                    category="benchmark",
                    message=(
                        f"Benchmark '{r.benchmark_name}' failed: "
                        f"score {r.score:.2f} < minimum {r.minimum_score:.2f}."
                    ),
                    evidence=r.evidence,
                    suggestion="Add the expected content/fields to the artifact or update the benchmark.",
                )
            )
    return findings
