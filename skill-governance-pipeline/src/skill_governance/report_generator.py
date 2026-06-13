"""Report generator: executive + technical reports.

Implements Core Requirement 13.

Required outputs:
- output/executive_report.md
- output/technical_report.md
- output/remediation_backlog.md
- output/skill_scorecard.json
- output/governance_findings.json
- output/proposed_rewrites/

Executive report must include:
- total skills, total agents
- health score
- CI status
- top risks
- recommended actions
- estimated token savings
- quality risk
- merge candidates
- split candidates
- rewrite candidates
- deprecated candidates
"""
from __future__ import annotations

from pathlib import Path

from .models import PipelineResult
from .utils import write_json, write_text


def _executive_summary(result: PipelineResult) -> str:
    """Render the executive one-pager."""
    total_skills = sum(1 for a in result.inventory if a.artifact_type.value == "skill")
    total_agents = sum(1 for a in result.inventory if a.artifact_type.value == "agent")
    blocking = sum(1 for f in result.findings if f.severity.value == "blocking")
    warning = sum(1 for f in result.findings if f.severity.value == "warning")

    decisions = {}
    for s in result.scorecards:
        decisions[s.decision.value] = decisions.get(s.decision.value, 0) + 1

    lines: list[str] = []
    lines.append("# Executive Report — Skill Governance Pipeline")
    lines.append("")
    lines.append(f"- **Total skills:** {total_skills}")
    lines.append(f"- **Total agents:** {total_agents}")
    lines.append(f"- **Health score:** {result.health_score}/100")
    lines.append(f"- **CI status:** {'PASS' if result.ci_passed else 'FAIL'}")
    lines.append(f"- **Blocking findings:** {blocking}")
    lines.append(f"- **Warnings:** {warning}")
    lines.append(f"- **Active waivers:** {len(result.waivers)}")
    lines.append(f"- **Proposed rewrites:** {len(result.rewrites)}")
    lines.append(f"- **Benchmark results:** {len(result.benchmark_results)}")
    lines.append(f"- **Started:** {result.started_at}")
    lines.append(f"- **Finished:** {result.finished_at}")
    lines.append("")
    lines.append("## Decisions")
    if decisions:
        for d, c in sorted(decisions.items()):
            lines.append(f"- **{d}:** {c}")
    else:
        lines.append("- (no decisions yet — Phase 3 will populate)")
    lines.append("")
    lines.append("## Top risks")
    if result.findings:
        for f in result.findings[:5]:
            lines.append(f"- `{f.severity.value}` **{f.artifact_name}**: {f.message}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Recommended actions")
    if result.recommendations:
        for r in result.recommendations[:5]:
            lines.append(f"- **{r.decision.value}** ({', '.join(r.affected_artifacts)}): {r.rationale}")
    else:
        lines.append("- (no recommendations yet — Phase 3 will populate)")
    lines.append("")
    lines.append("## Merge / split / rewrite / deprecate candidates")
    lines.append("")
    lines.append("| Decision | Count |")
    lines.append("| --- | --- |")
    for d, c in sorted(decisions.items()):
        lines.append(f"| {d} | {c} |")
    if not decisions:
        lines.append("| (none) | 0 |")
    lines.append("")
    if result.waivers:
        lines.append("## Active waivers")
        lines.append("")
        for w in result.waivers:
            lines.append(f"- `{w.waiver_id}` -> finding `{w.finding_id}` (expires {w.expiration_date}, owner {w.owner})")
        lines.append("")
    return "\n".join(lines)


def _technical_report(result: PipelineResult) -> str:
    """Render the detailed technical report."""
    lines: list[str] = []
    lines.append("# Technical Report — Skill Governance Pipeline")
    lines.append("")
    lines.append(f"Started: {result.started_at}")
    lines.append(f"Finished: {result.finished_at}")
    lines.append(f"CI: {'PASS' if result.ci_passed else 'FAIL'}")
    lines.append("")
    lines.append("## Inventory")
    lines.append("")
    lines.append("| Name | Type | Tokens | Version | Owner |")
    lines.append("| --- | --- | --- | --- | --- |")
    for a in sorted(result.inventory, key=lambda x: x.name):
        lines.append(
            f"| {a.name} | {a.artifact_type.value} | {a.estimated_tokens} | "
            f"{a.declared_version or '-'} | {a.owner or '-'} |"
        )
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if result.findings:
        lines.append("| Severity | Artifact | Category | Message |")
        lines.append("| --- | --- | --- | --- |")
        for f in result.findings:
            lines.append(
                f"| {f.severity.value} | {f.artifact_name} | {f.category} | {f.message} |"
            )
    else:
        lines.append("(no findings)")
    lines.append("")
    lines.append("## Dependency graph")
    if result.dependency_graph:
        lines.append(f"- Nodes: {len(result.dependency_graph.nodes)}")
        lines.append(f"- Missing: {len(result.dependency_graph.missing_dependencies)}")
        lines.append(f"- Circular: {len(result.dependency_graph.circular_dependencies)}")
        lines.append(f"- Unused: {len(result.dependency_graph.unused_dependencies)}")
        # Show first 10 missing for visibility
        if result.dependency_graph.missing_dependencies:
            lines.append("")
            lines.append("### Missing dependencies (first 10)")
            for src, missing in result.dependency_graph.missing_dependencies[:10]:
                lines.append(f"- `{src}` -> `{missing}` (does not exist)")
    else:
        lines.append("- (Phase 2 will populate)")
    lines.append("")
    lines.append("## Responsibility")
    if result.responsibility:
        flag_counts: dict[str, int] = {}
        for r in result.responsibility:
            flag_counts[r.flag.value] = flag_counts.get(r.flag.value, 0) + 1
        lines.append("")
        lines.append("| Flag | Count |")
        lines.append("| --- | --- |")
        for flag, count in sorted(flag_counts.items()):
            lines.append(f"| {flag} | {count} |")
        # Show first 5 over-broad for visibility
        over_broad = [r for r in result.responsibility if r.flag.value == "over-broad"][:5]
        if over_broad:
            lines.append("")
            lines.append("### Over-broad skills (first 5)")
            for r in over_broad:
                lines.append(f"- `{r.artifact_name}` (score={r.responsibility_score}): {r.rationale}")
    else:
        lines.append("- (Phase 2 will populate)")
    lines.append("")
    lines.append("## Overlap (top 10 pairs)")
    if result.overlap_pairs:
        lines.append("")
        lines.append("| Artifact A | Artifact B | Score | Recommendation |")
        lines.append("| --- | --- | --- | --- |")
        for p in result.overlap_pairs[:10]:
            lines.append(f"| {p.artifact_a} | {p.artifact_b} | {p.overlap_score} | {p.recommendation.value} |")
    else:
        lines.append("- (Phase 2 will populate)")
    lines.append("")
    lines.append("## Scorecard")
    if result.scorecards:
        lines.append("| Name | ROI | Decision | Rationale |")
        lines.append("| --- | --- | --- | --- |")
        for s in result.scorecards:
            lines.append(f"| {s.artifact_name} | {s.roi_score} | {s.decision.value} | {s.rationale} |")
    else:
        lines.append("- (Phase 3 will populate)")
    lines.append("")
    return "\n".join(lines)


def _remediation_backlog(result: PipelineResult) -> str:
    """Render the prioritized remediation backlog."""
    lines: list[str] = []
    lines.append("# Remediation Backlog")
    lines.append("")
    if result.recommendations:
        for r in sorted(result.recommendations, key=lambda x: x.priority):
            lines.append(
                f"## {r.recommendation_id} — {r.decision.value} (priority {r.priority})"
            )
            lines.append("")
            lines.append(f"- **Affected:** {', '.join(r.affected_artifacts)}")
            lines.append(f"- **Rationale:** {r.rationale}")
            lines.append(f"- **Effort:** {r.implementation_effort}")
            lines.append(f"- **Risk:** {r.risk}")
            lines.append(f"- **CI impact:** {r.ci_impact}")
            lines.append(f"- **Next action:** {r.proposed_next_action}")
            lines.append("")
    else:
        lines.append("(no recommendations yet — Phase 3 will populate)")
    return "\n".join(lines)


def write_reports(result: PipelineResult, output_dir: Path) -> dict[str, Path]:
    """Write the executive, technical, and backlog reports.

    Returns a dict of report name -> file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    paths["executive"] = output_dir / "executive_report.md"
    paths["technical"] = output_dir / "technical_report.md"
    paths["backlog"] = output_dir / "remediation_backlog.md"
    write_text(paths["executive"], _executive_summary(result))
    write_text(paths["technical"], _technical_report(result))
    write_text(paths["backlog"], _remediation_backlog(result))
    paths["scorecard"] = output_dir / "skill_scorecard.json"
    write_json(paths["scorecard"], [s.to_dict() for s in result.scorecards])
    paths["findings"] = output_dir / "governance_findings.json"
    write_json(paths["findings"], [f.to_dict() for f in result.findings])
    return paths
