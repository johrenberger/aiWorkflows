"""Recommendation engine: evidence-backed governance decisions.

Implements Core Requirement 11.

Every recommendation must include:
- recommendation_id
- affected_artifacts
- decision
- priority
- rationale
- evidence
- estimated_token_impact
- estimated_quality_impact
- implementation_effort
- risk
- CI impact
- proposed next action

Output:
- output/governance_findings.json
- output/remediation_backlog.md
"""
from __future__ import annotations

import uuid
from collections import defaultdict

from .models import (
    Decision,
    Finding,
    OverlapPair,
    Recommendation,
    ResponsibilityReport,
    ScorecardEntry,
    Severity,
)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _priority_for_decision(decision: Decision, blocking: int) -> int:
    """Compute a 1-5 priority (1=highest)."""
    if decision == Decision.DEPRECATE or decision == Decision.RETIRE:
        return 1 if blocking else 2
    if decision == Decision.MERGE:
        return 2
    if decision == Decision.REWRITE:
        return 2 if blocking else 3
    if decision == Decision.SPLIT:
        return 3
    return 4  # keep


def _effort_for_decision(decision: Decision) -> str:
    return {
        Decision.KEEP: "XS",
        Decision.REWRITE: "M",
        Decision.MERGE: "L",
        Decision.SPLIT: "M",
        Decision.DEPRECATE: "S",
        Decision.RETIRE: "S",
    }.get(decision, "M")


def _risk_for_decision(decision: Decision, blocking: int) -> str:
    if decision in (Decision.DEPRECATE, Decision.RETIRE) and blocking > 0:
        return "high"
    if decision == Decision.MERGE:
        return "medium"
    return "low"


def _next_action(decision: Decision, affected: list[str]) -> str:
    if decision == Decision.KEEP:
        return "No action; monitor for changes."
    if decision == Decision.REWRITE:
        return f"Open a rewrite task for {', '.join(affected[:3])}."
    if decision == Decision.MERGE:
        return f"Schedule a merge review for {', '.join(affected[:3])}."
    if decision == Decision.SPLIT:
        return f"Identify split boundaries for {', '.join(affected[:3])}."
    if decision == Decision.DEPRECATE:
        return f"Mark {', '.join(affected[:3])} deprecated; document successor."
    if decision == Decision.RETIRE:
        return f"Remove {', '.join(affected[:3])} from catalog."
    return "Review."


def generate(
    findings: list[Finding],
    scorecards: list[ScorecardEntry] | None = None,
    overlap_pairs: list[OverlapPair] | None = None,
    responsibility: list[ResponsibilityReport] | None = None,
) -> list[Recommendation]:
    """Generate recommendations from findings.

    Strategy:
    1. Group findings by artifact.
    2. For each artifact, derive a primary recommendation from
       its highest-severity finding + the scorecard decision.
    3. For high-overlap pairs, emit a merge recommendation.
    4. For over-broad responsibility, emit a split recommendation.
    5. De-duplicate recommendations per (decision, tuple(artifacts)).
    """
    scorecards = scorecards or []
    overlap_pairs = overlap_pairs or []
    responsibility = responsibility or []
    scorecard_by_name = {s.artifact_name: s for s in scorecards}

    recs: list[Recommendation] = []
    # 1. Per-artifact findings -> recommendations
    by_artifact: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_artifact[f.artifact_name].append(f)
    for name, fs in by_artifact.items():
        blocking = sum(1 for f in fs if f.severity == Severity.BLOCKING)
        warnings = sum(1 for f in fs if f.severity == Severity.WARNING)
        # If we have a scorecard, use its decision. Otherwise,
        # derive a sensible decision from the findings themselves.
        sc = scorecard_by_name.get(name)
        if sc is not None:
            decision = sc.decision
        else:
            if blocking > 0:
                decision = Decision.REWRITE
            elif warnings > 0:
                decision = Decision.KEEP
            else:
                decision = Decision.KEEP
        recs.append(
            Recommendation(
                recommendation_id=_id("rec"),
                affected_artifacts=[name],
                decision=decision,
                priority=_priority_for_decision(decision, blocking),
                rationale=f"{blocking} blocking + {warnings} warnings on {name}.",
                evidence={
                    "findings": [f.to_dict() for f in fs[:5]],
                    "blocking": blocking,
                    "warnings": warnings,
                },
                estimated_token_impact=0,
                estimated_quality_impact=blocking * 10,
                implementation_effort=_effort_for_decision(decision),
                risk=_risk_for_decision(decision, blocking),
                ci_impact="blocking" if blocking else "warning",
                proposed_next_action=_next_action(decision, [name]),
            )
        )
    # 2. Merge candidates from overlap
    for p in overlap_pairs:
        if p.recommendation.value == "merge":
            recs.append(
                Recommendation(
                    recommendation_id=_id("merge"),
                    affected_artifacts=[p.artifact_a, p.artifact_b],
                    decision=Decision.MERGE,
                    priority=2,
                    rationale=f"Overlap score {p.overlap_score} suggests merging.",
                    evidence={
                        "overlap_score": p.overlap_score,
                        "rationale": p.rationale,
                    },
                    estimated_token_impact=500,  # rough estimate
                    estimated_quality_impact=20,
                    implementation_effort="L",
                    risk="medium",
                    ci_impact="blocking" if p.overlap_score >= 85 else "warning",
                    proposed_next_action=f"Schedule merge review for {p.artifact_a} + {p.artifact_b}.",
                )
            )
    # 3. Split candidates from responsibility
    for r in responsibility:
        if r.flag.value == "over-broad":
            recs.append(
                Recommendation(
                    recommendation_id=_id("split"),
                    affected_artifacts=[r.artifact_name],
                    decision=Decision.SPLIT,
                    priority=3,
                    rationale=f"Responsibility score {r.responsibility_score} indicates over-broad scope.",
                    evidence={
                        "responsibility_score": r.responsibility_score,
                        "responsibilities": r.responsibilities,
                    },
                    estimated_token_impact=200,
                    estimated_quality_impact=15,
                    implementation_effort="M",
                    risk="low",
                    ci_impact="warning",
                    proposed_next_action=f"Identify split boundaries for {r.artifact_name}.",
                )
            )
    # Sort by priority
    recs.sort(key=lambda r: (r.priority, r.recommendation_id))
    return recs
