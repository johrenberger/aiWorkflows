"""CLI entry point for the skill governance pipeline.

Commands:
- scan
- validate
- benchmark
- recommend
- rewrite
- report
- ci
- full

Phase 1 implements scan + ci (the two most useful ones for
a CI-driven governance workflow). The remaining commands are
wired up in later phases.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml

from .ci_gate import count_blocking, evaluate
from .config_loader import load_config
from .contract_validator import validate_contract
from .dependency_analyzer import analyze as analyze_dependencies, graph_to_findings as dep_findings
from .discovery import DiscoveryConfig, discover
from .history import snapshot as history_snapshot, append as history_append
from .metadata_parser import parse_metadata
from .models import (
    ArtifactType,
    Finding,
    PipelineResult,
    ScorecardEntry,
    Severity,
    SkillArtifact,
    Decision,
    ResponsibilityFlag,
)
from .overlap_analyzer import analyze as analyze_overlap
from .recommendation_engine import generate as generate_recommendations
from .report_generator import write_reports
from .responsibility_analyzer import analyze as analyze_responsibility
from .rewrite_generator import generate_rewrites
from .roi_scorer import score as score_roi
from .token_analyzer import analyze_static, write_static
from .benchmark_runner import run_benchmarks, benchmark_findings
from .waiver_store import load_waivers, active_waivers
from .utils import utc_now_iso, write_json


def _validate_one(artifact: SkillArtifact, roots: list[Path]) -> list[Finding]:
    """Run metadata + contract validation on a single artifact.

    Resolves the artifact's relative `path` against the first root
    (in `roots`) that contains it. The relative path returned by
    discovery is preserved on the finding's `artifact_path` field
    so downstream consumers can group findings by artifact.
    """
    findings: list[Finding] = []
    # Phase 6 fix: unknown-type artifacts (e.g. README.md, templates/)
    # are not contracts. Skip contract validation entirely and emit
    # a single informational notice.
    if artifact.artifact_type.value == "unknown":
        return [
            Finding(
                finding_id=f"untyped.skipped.{artifact.name}",
                artifact_name=artifact.name,
                artifact_path=artifact.path,
                severity=Severity.WARNING,
                category="discovery",
                message=(
                    f"Artifact '{artifact.name}' is not a skill or agent "
                    f"(path: {artifact.path}). Skipping contract validation."
                ),
                evidence={"path": artifact.path, "type": artifact.artifact_type.value},
            )
        ]
    # Resolve path: try each root in order, return the first that exists
    path: Path | None = None
    for root in roots:
        try:
            candidate = root / artifact.path
        except (TypeError, ValueError):
            continue
        if candidate.exists():
            path = candidate
            break
    if path is None:
        return [
            Finding(
                finding_id=f"path.missing.{artifact.name}",
                artifact_name=artifact.name,
                artifact_path=artifact.path,
                severity=Severity.BLOCKING,
                category="discovery",
                message=f"Path does not exist in any known root: {artifact.path}",
                evidence={"path": artifact.path, "roots": [str(r) for r in roots]},
            )
        ]
    metadata = parse_metadata(path)
    missing = metadata.missing_fields()
    if missing:
        findings.append(
            Finding(
                finding_id=f"metadata.missing.{artifact.name}",
                artifact_name=artifact.name,
                artifact_path=artifact.path,
                severity=Severity.BLOCKING,
                category="metadata",
                message=f"Missing required metadata fields: {', '.join(missing)}",
                evidence={"missing": missing, "path": artifact.path},
                suggestion="Add a YAML frontmatter block with all required fields (name, artifact_type, purpose, ...).",
            )
        )
    if metadata.is_purpose_vague():
        findings.append(
            Finding(
                finding_id=f"metadata.purpose.vague.{artifact.name}",
                artifact_name=artifact.name,
                artifact_path=artifact.path,
                severity=Severity.WARNING,
                category="metadata",
                message="Purpose is missing or too short / vague.",
                evidence={"purpose": metadata.purpose},
                suggestion="Write a 1-3 sentence purpose that names what the skill does, for whom, and in what context.",
            )
        )
    findings.extend(validate_contract(artifact.name, path))
    # Phase 6 fix: stamp artifact_path on every finding
    for f in findings:
        if not f.artifact_path:
            f.artifact_path = artifact.path
    return findings
    return findings


def _run_scan(config_path: Path) -> PipelineResult:
    """Run discovery only and write the inventory."""
    config = load_config(config_path)
    result = PipelineResult(started_at=utc_now_iso())
    dcfg = DiscoveryConfig(
        skill_directories=[Path(p) for p in config.skill_directories],
        agent_directories=[Path(p) for p in config.agent_directories],
    )
    result.inventory = discover(dcfg)
    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "skill_inventory.json", [a.to_dict() for a in result.inventory])
    result.finished_at = utc_now_iso()
    return result


def _run_validate(config_path: Path) -> PipelineResult:
    """Run discovery + metadata + contract validation."""
    result = _run_scan(config_path)
    config = load_config(config_path)
    # Phase 6 fix: validate against the actual discovery roots, not
    # `config_path.parent.parent` (which only works when the config
    # is 2 levels deep — fragile and wrong in general).
    roots = [Path(p) for p in config.skill_directories] + [Path(p) for p in config.agent_directories]
    for a in result.inventory:
        result.findings.extend(_validate_one(a, roots))
    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "governance_findings.json", [f.to_dict() for f in result.findings])
    result.finished_at = utc_now_iso()
    return result


def _run_full_pipeline(config_path: Path, render_reports: bool = True) -> PipelineResult:
    """Run the full pipeline (Phases 1-5) and return a populated PipelineResult.

    Optionally renders the reports. The `ci` command always renders;
    the sub-phase commands (`benchmark`, `recommend`, `rewrite`)
    skip report rendering because they only need a slice of the
    output files.
    """
    result = _run_validate(config_path)
    config = load_config(config_path)
    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Add token cost static
    costs = analyze_static(result.inventory, high_cost_threshold=int(config.token_thresholds["high_cost"]))
    write_static(costs, output_dir)
    # Phase 2: dependency analysis
    roots = [Path(p) for p in config.skill_directories] + [Path(p) for p in config.agent_directories]
    dep_graph = analyze_dependencies(result.inventory, roots=roots)
    result.dependency_graph = dep_graph
    result.findings.extend(dep_findings(dep_graph))
    # Phase 2: responsibility analysis
    result.responsibility = analyze_responsibility(result.inventory, roots=roots)
    # Phase 2: overlap analysis (deterministic only in Phase 2)
    result.overlap_pairs = analyze_overlap(
        result.inventory,
        blocking_threshold=int(config.overlap_thresholds["blocking"]),
        warning_threshold=int(config.overlap_thresholds["warning"]),
    )
    # Phase 3: real ROI scoring
    dep_value_map: dict[str, int] = {}
    if dep_graph and dep_graph.nodes:
        for name, node in dep_graph.nodes.items():
            dep_value_map[name] = len(node.depended_on_by)
    result.scorecards = score_roi(
        result.inventory,
        findings=result.findings,
        token_costs=costs,
        dependency_value_map=dep_value_map,
    )
    # Phase 3: recommendations
    result.recommendations = generate_recommendations(
        findings=result.findings,
        scorecards=result.scorecards,
        overlap_pairs=result.overlap_pairs,
        responsibility=result.responsibility,
    )
    # Phase 4: benchmarks
    benchmark_dir = Path("./benchmarks")
    if not benchmark_dir.exists():
        repo_root = Path(__file__).resolve().parent.parent.parent
        alt = repo_root / "skill-governance-pipeline" / "tests" / "benchmarks"
        if alt.exists():
            benchmark_dir = alt
    result.benchmark_results = run_benchmarks(
        result.inventory,
        benchmark_dir,
        default_minimum=float(config.benchmark_thresholds["default_minimum"]),
    )
    result.findings.extend(benchmark_findings(result.benchmark_results))
    # Phase 4: rewrite proposals
    result.rewrites = generate_rewrites(
        result.inventory,
        findings=result.findings,
        scorecards=result.scorecards,
        responsibility=result.responsibility,
        benchmark_results=result.benchmark_results,
        output_dir=output_dir,
    )
    # Phase 5: waivers
    waivers = load_waivers(Path(config.waiver_file))
    active = active_waivers(waivers)
    result.waivers = active
    # Compute health + CI status (see _compute_health for the new formula)
    result.health_score, result.ci_blocking_count = _compute_health(
        result, active, config
    )
    result.ci_passed = evaluate(result, waivers=active)
    if render_reports:
        # Phase 5: history
        entry = history_snapshot(result, note=f"CI run; {len(active)} active waivers")
        history_path = output_dir / "governance_history.jsonl"
        history_append(history_path, entry)
        write_reports(result, output_dir)
    return result


def _compute_health(result: PipelineResult, active_waivers: list, config) -> tuple[int, int]:
    """Compute the catalog health score (0-100).

    Phase 6 fix: the original formula was `100 - 5*blocking - warnings`,
    which always produced 0 for any catalog with 20+ blocking findings.
    The new formula distinguishes between **structural** findings
    (which indicate a real problem) and **cosmetic** findings
    (missing YAML frontmatter fields that the SGP's own schema
    requires but well-written skills don't use).

    Structural findings: those in categories other than 'metadata'
    or 'discovery' (which the SGP's own schema defines as cosmetic).
    All other findings (including 'contract' and 'dependency') are
    structural — they indicate a real quality problem.

    Waivers also reduce the blocking count: a waived finding is no
    longer counted as blocking, so it doesn't drag the score down.
    """
    # Identify which findings are waived
    waived_ids = {w.finding_id for w in active_waivers}
    structural = 0
    cosmetic = 0
    warning_count = 0
    blocking = 0
    for f in result.findings:
        if f.finding_id in waived_ids:
            continue
        is_cosmetic = f.category in ("metadata", "discovery")
        if f.severity.value == "blocking":
            blocking += 1
            if is_cosmetic:
                cosmetic += 1
            else:
                structural += 1
        elif f.severity.value == "warning":
            warning_count += 1
    # New formula: structural findings dominate, cosmetic is capped.
    # Shape: percentage of artifacts that are clean, weighted by
    # severity. An artifact with at least one structural blocking
    # finding counts as "broken" (heavy penalty). An artifact with
    # only cosmetic findings counts as "good" (light penalty).
    # This is more meaningful for catalogs with many findings than
    # a simple `100 - penalty` formula that always clamps to 0.
    artifacts = list(result.inventory)
    n_artifacts = len(artifacts)
    if n_artifacts == 0:
        return 100, 0
    # Group findings by artifact_path
    by_artifact: dict[str, list] = {}
    for f in result.findings:
        key = f.artifact_path or f.artifact_name
        by_artifact.setdefault(key, []).append(f)
    broken = 0  # has at least one structural blocking finding
    ugly = 0    # has cosmetic findings but no structural
    clean = 0   # has no findings
    for a in artifacts:
        fs = by_artifact.get(a.path, [])
        has_structural_blocking = any(
            f.severity.value == "blocking" and f.category not in ("metadata", "discovery")
            for f in fs
        )
        has_any = len(fs) > 0
        if has_structural_blocking:
            broken += 1
        elif has_any:
            ugly += 1
        else:
            clean += 1
    # Weighted score: clean = 100, ugly = 80, broken = 30
    score = int(round(100 * clean / n_artifacts + 80 * ugly / n_artifacts + 30 * broken / n_artifacts))
    return score, blocking


@click.group()
def main() -> None:
    """Skill Governance Pipeline."""


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def scan(config_path: Path) -> None:
    """Scan for skills and agents."""
    result = _run_scan(config_path)
    click.echo(f"Discovered {len(result.inventory)} artifacts. See output/skill_inventory.json.")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def validate(config_path: Path) -> None:
    """Run metadata and contract validation."""
    result = _run_validate(config_path)
    blocking = count_blocking(result)
    click.echo(f"Found {len(result.findings)} findings ({blocking} blocking).")
    if blocking:
        sys.exit(2)


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def benchmark(config_path: Path) -> None:
    """Run benchmark fixtures and write the scorecard."""
    result = _run_full_pipeline(config_path, render_reports=True)
    output_dir = Path(load_config(config_path).output_directory)
    click.echo(f"benchmark: ran {len(result.benchmark_results)} benchmarks; "
               f"scorecard written to {output_dir / 'skill_scorecard.json'}")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def recommend(config_path: Path) -> None:
    """Generate recommendations and write the scorecard."""
    result = _run_full_pipeline(config_path, render_reports=True)
    output_dir = Path(load_config(config_path).output_directory)
    click.echo(f"recommend: {len(result.recommendations)} recommendations; "
               f"scorecard written to {output_dir / 'skill_scorecard.json'}")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--artifact", default=None)
def rewrite(config_path: Path, artifact: str | None) -> None:
    """Generate proposed rewrites and write them to output/proposed_rewrites/."""
    result = _run_full_pipeline(config_path, render_reports=True)
    output_dir = Path(load_config(config_path).output_directory)
    if artifact:
        # Filter to just the requested artifact
        filtered = {k: v for k, v in result.rewrites.items() if k == artifact}
        click.echo(f"rewrite: {len(filtered)} rewrite(s) for {artifact}")
    else:
        click.echo(f"rewrite: {len(result.rewrites)} proposed rewrite(s) "
                   f"written to {output_dir / 'proposed_rewrites'}")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def report(config_path: Path) -> None:
    """Render reports."""
    config = load_config(config_path)
    # Build a minimal result from the inventory
    from .discovery import DiscoveryConfig
    from pathlib import Path as P
    dcfg = DiscoveryConfig(
        skill_directories=[P(p) for p in config.skill_directories],
        agent_directories=[P(p) for p in config.agent_directories],
    )
    inv = discover(dcfg)
    result = PipelineResult(inventory=inv, started_at=utc_now_iso())
    paths = write_reports(result, P(config.output_directory))
    click.echo(f"Reports written: {', '.join(str(p) for p in paths.values())}")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def ci(config_path: Path) -> None:
    """Run all checks; exit non-zero on blocking findings."""
    result = _run_full_pipeline(config_path, render_reports=True)
    if not result.ci_passed:
        click.echo(f"CI FAILED: {result.ci_blocking_count} blocking findings. See output/executive_report.md.")
        sys.exit(1)
    click.echo(f"CI PASSED. {len(result.inventory)} artifacts, {len(result.findings)} findings.")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
def full(config_path: Path) -> None:
    """Run scan -> validate -> benchmark -> recommend -> rewrite -> report -> ci."""
    ctx = click.get_current_context()
    ctx.invoke(scan, config_path=config_path)
    ctx.invoke(validate, config_path=config_path)
    ctx.invoke(benchmark, config_path=config_path)
    ctx.invoke(recommend, config_path=config_path)
    ctx.invoke(rewrite, config_path=config_path)
    ctx.invoke(report, config_path=config_path)
    ctx.invoke(ci, config_path=config_path)


if __name__ == "__main__":
    main()
