"""ROI scorer: per-skill return-on-investment.

Implements Core Requirement 8.

Inputs (per the source spec):
- reuse frequency
- token cost
- output structure quality
- downstream dependency value
- failure rate
- semantic uniqueness
- benchmark pass rate
- business criticality

We compute a 0-100 score by normalizing each input to 0-1 and
taking a weighted sum. The weights are deterministic defaults
that can be overridden via the `weights` argument.

The decision (keep / rewrite / merge / split / deprecate / retire)
is derived from the ROI score plus the governance findings:
- score >= 70 + no blocking findings => keep
- score 50-69 OR has rewrite triggers => rewrite
- score 30-49 OR has merge candidates => merge
- score 10-29 OR has split candidates => split
- score < 10 => deprecate or retire
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import (
    Decision,
    Finding,
    ScorecardEntry,
    Severity,
    SkillArtifact,
    TokenCostStatic,
)


@dataclass
class ROIWeights:
    """Configurable weights for the ROI formula.

    All values should sum to ~1.0; the scorer will normalize
    whatever it receives.
    """

    reuse: float = 0.20
    token_cost: float = 0.10  # lower token cost = higher contribution
    output_quality: float = 0.20
    dependency_value: float = 0.15
    failure_rate: float = 0.10  # higher failure = lower contribution
    semantic_uniqueness: float = 0.10
    benchmark_pass_rate: float = 0.05
    business_criticality: float = 0.10


def _normalize(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value to [0, 1]."""
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _token_cost_score(estimated_tokens: int, high_cost: int) -> float:
    """Lower tokens = higher score (1.0 for small, 0.0 for huge)."""
    if high_cost <= 0:
        return 1.0
    if estimated_tokens <= 0:
        return 1.0
    # 0 tokens => 1.0; high_cost tokens => 0.0; more => 0.0
    return 1.0 - _normalize(estimated_tokens, 0, high_cost)


def _failure_score(failure_rate: float) -> float:
    """Lower failure rate = higher score (1.0 for 0%, 0.0 for 100%)."""
    return 1.0 - _normalize(failure_rate, 0.0, 1.0)


def _benchmark_score(rate: float) -> float:
    """Higher benchmark pass rate = higher score."""
    return _normalize(rate, 0.0, 1.0)


def _reuse_score(uses: int) -> float:
    """Map raw reuse count to a 0-1 score (log-scaled)."""
    import math
    if uses <= 0:
        return 0.0
    # 1 use = 0.2, 10 uses = ~0.6, 100 uses = ~1.0
    return _normalize(math.log10(uses + 1), 0.0, 2.0)


def _score_one(
    artifact: SkillArtifact,
    *,
    reuse_count: int,
    token_costs: list[TokenCostStatic],
    findings: list[Finding],
    dependency_value: int,
    semantic_uniqueness: int,
    benchmark_pass_rate: float,
    business_criticality: int,
    weights: ROIWeights,
    overlap_pairs: list | None = None,
) -> ScorecardEntry:
    """Compute a ScorecardEntry for a single artifact."""
    # Output quality: -50 if any blocking contract finding, -25 if warning, else 100
    own_findings = [f for f in findings if f.artifact_name == artifact.name]
    blocking = sum(1 for f in own_findings if f.severity == Severity.BLOCKING)
    warnings = sum(1 for f in own_findings if f.severity == Severity.WARNING)
    output_quality = max(0, 100 - blocking * 50 - warnings * 25)
    # Token cost contribution
    tc = next((t for t in token_costs if t.artifact_name == artifact.name), None)
    tokens = tc.estimated_tokens if tc else artifact.estimated_tokens
    high_cost_threshold = tc.high_cost_threshold if tc and hasattr(tc, "high_cost_threshold") else 8000
    cost_score = _token_cost_score(tokens, high_cost_threshold)
    # Failure rate: from findings
    failure_rate = blocking / max(1, len(findings))
    # Build the score (weighted, normalized)
    parts = {
        "reuse": _reuse_score(reuse_count),
        "token_cost": cost_score,
        "output_quality": _normalize(output_quality),
        "dependency_value": _normalize(dependency_value),
        "failure_rate": _failure_score(failure_rate),
        "semantic_uniqueness": _normalize(semantic_uniqueness),
        "benchmark_pass_rate": _benchmark_score(benchmark_pass_rate),
        "business_criticality": _normalize(business_criticality),
    }
    raw = (
        weights.reuse * parts["reuse"]
        + weights.token_cost * parts["token_cost"]
        + weights.output_quality * parts["output_quality"]
        + weights.dependency_value * parts["dependency_value"]
        + weights.failure_rate * parts["failure_rate"]
        + weights.semantic_uniqueness * parts["semantic_uniqueness"]
        + weights.benchmark_pass_rate * parts["benchmark_pass_rate"]
        + weights.business_criticality * parts["business_criticality"]
    )
    score = int(round(raw * 100))
    # Decision
    # Phase 7 fix: `has_merge_candidate` used to read from
    # `f.category == "overlap"` findings, but overlap produces
    # `OverlapPair` objects (not `Finding`s), so the check was
    # always False. Combined with `score >= 30 or has_merge_candidate`,
    # this meant *every* low-scoring skill (score 30-49) was
    # tagged as a merge candidate regardless of actual overlap.
    # Now: look at real OverlapPair data. The merge decision fires
    # ONLY if at least one overlap pair (involving this artifact)
    # has recommendation == "merge".
    has_merge_candidate = False
    merge_partner: str | None = None
    if overlap_pairs:
        for p in overlap_pairs:
            recommendation_value = (
                p.recommendation.value
                if hasattr(p.recommendation, "value")
                else p.recommendation
            )
            if recommendation_value == "merge" and (
                p.artifact_a == artifact.name or p.artifact_b == artifact.name
            ):
                has_merge_candidate = True
                merge_partner = (
                    p.artifact_b if p.artifact_a == artifact.name else p.artifact_a
                )
                break
    has_rewrite_trigger = blocking > 0 or warnings >= 2
    if score >= 70 and not has_rewrite_trigger:
        decision = Decision.KEEP
        rationale = f"Score {score} with no rewrite triggers."
    elif has_merge_candidate:
        decision = Decision.MERGE
        rationale = f"Score {score}; merge with '{merge_partner}' (overlap threshold met)."
    elif score >= 50 or has_rewrite_trigger:
        decision = Decision.REWRITE
        rationale = f"Score {score}; rewrite triggered by {blocking} blocking + {warnings} warnings."
    elif score >= 30:
        decision = Decision.REWRITE
        rationale = f"Score {score}; rewrite (low score, no merge candidate)."
    elif score >= 10:
        decision = Decision.SPLIT
        rationale = f"Score {score}; consider splitting into narrower skills."
    else:
        decision = Decision.DEPRECATE
        rationale = f"Score {score}; deprecate and document successor."
    return ScorecardEntry(
        artifact_name=artifact.name,
        roi_score=score,
        decision=decision,
        rationale=rationale,
        reuse_frequency=reuse_count,
        estimated_tokens=tokens,
        output_structure_quality=output_quality,
        failure_rate=failure_rate,
        semantic_uniqueness=semantic_uniqueness,
        benchmark_pass_rate=benchmark_pass_rate,
        business_criticality=business_criticality,
    )


def score(
    artifacts: list[SkillArtifact],
    findings: list[Finding],
    token_costs: list[TokenCostStatic],
    reuse_map: dict[str, int] | None = None,
    dependency_value_map: dict[str, int] | None = None,
    uniqueness_map: dict[str, int] | None = None,
    benchmark_map: dict[str, float] | None = None,
    criticality_map: dict[str, int] | None = None,
    weights: ROIWeights | None = None,
    overlap_pairs: list | None = None,
) -> list[ScorecardEntry]:
    """Compute ROI scores for every artifact.

    Args:
        artifacts: The discovered artifacts.
        findings: All findings (used for output quality + failure rate).
        token_costs: Static token costs (Phase 1 produced these).
        reuse_map: Optional map of artifact name -> reuse count.
        dependency_value_map: Optional map of artifact name -> how many
            other artifacts depend on it.
        uniqueness_map: Optional map of artifact name -> semantic
            uniqueness score 0-100 (Phase 5 will populate from MiniMax).
        benchmark_map: Optional map of artifact name -> benchmark
            pass rate 0-1.
        criticality_map: Optional map of artifact name -> business
            criticality 0-100.
        weights: ROIWeights (default: ROIWeights()).
    """
    reuse_map = reuse_map or {}
    dependency_value_map = dependency_value_map or {}
    uniqueness_map = uniqueness_map or {}
    benchmark_map = benchmark_map or {}
    criticality_map = criticality_map or {}
    weights = weights or ROIWeights()
    return [
        _score_one(
            a,
            reuse_count=reuse_map.get(a.name, 0),
            token_costs=token_costs,
            findings=findings,
            dependency_value=dependency_value_map.get(a.name, 0),
            semantic_uniqueness=uniqueness_map.get(a.name, 50),
            benchmark_pass_rate=benchmark_map.get(a.name, 1.0),
            business_criticality=criticality_map.get(a.name, 50),
            weights=weights,
            overlap_pairs=overlap_pairs,
        )
        for a in artifacts
    ]


# ---------------------------------------------------------------------------
# MiniMax semantic scoring interface (CR 6 layer 2)
# ---------------------------------------------------------------------------


@dataclass
class SemanticScore:
    """A semantic score from MiniMax (or a mock)."""

    artifact_name: str
    coherence: int  # 0-100; how semantically coherent the skill is
    uniqueness: int  # 0-100; how unique vs other skills
    rationale: str = ""
    provenance: str = "mock"  # 'minimax' or 'mock'


class SemanticScoringInterface:
    """Pluggable interface for MiniMax-style semantic scoring.

    The default implementation is a deterministic mock that
    returns middle-of-the-road scores. Phase 5 will provide a
    real client that calls the MiniMax API.
    """

    def score(self, artifact_name: str, body: str) -> SemanticScore:
        """Return a SemanticScore for a single artifact."""
        # Mock: count tokens, return scores proportional to size
        n = max(1, len(body.split()))
        coherence = min(100, 40 + n // 10)
        uniqueness = 50  # placeholder
        return SemanticScore(
            artifact_name=artifact_name,
            coherence=coherence,
            uniqueness=uniqueness,
            rationale="Mock scoring; Phase 5 will replace with MiniMax.",
            provenance="mock",
        )


_default_scorer: SemanticScoringInterface = SemanticScoringInterface()


def get_scorer() -> SemanticScoringInterface:
    """Return the active semantic scorer (default: mock)."""
    return _default_scorer


def set_scorer(scorer: SemanticScoringInterface) -> None:
    """Install a custom semantic scorer (e.g. a MiniMax client)."""
    global _default_scorer
    _default_scorer = scorer
