"""CLI entry point for the skill governance pipeline.

Commands:
- scan
- validate
- validate-files
- benchmark
- recommend
- recommend-task
- rewrite
- report
- ci
- install-hooks
- full

Phase 1 implements scan + ci (the two most useful ones for
a CI-driven governance workflow). The remaining commands are
wired up in later phases.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click

from .benchmark_runner import benchmark_findings, run_benchmarks
from .ci_gate import count_blocking, evaluate
from .config_loader import load_config
from .contract_validator import validate_contract
from .dependency_analyzer import analyze as analyze_dependencies
from .dependency_analyzer import graph_to_findings as dep_findings
from .discovery import DiscoveryConfig, discover
from .history import append as history_append
from .history import snapshot as history_snapshot
from .metadata_parser import parse_metadata
from .models import (
    Finding,
    PipelineResult,
    Severity,
    SkillArtifact,
)
from .overlap_analyzer import analyze as analyze_overlap
from .recommendation_engine import generate as generate_recommendations
from .report_generator import write_reports
from .responsibility_analyzer import analyze as analyze_responsibility
from .rewrite_generator import generate_rewrites
from .roi_scorer import score as score_roi
from .token_analyzer import analyze_static, write_static
from .utils import utc_now_iso, write_json
from .waiver_store import active_waivers, load_waivers


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
        overlap_pairs=result.overlap_pairs,
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
    from pathlib import Path as P

    from .discovery import DiscoveryConfig
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
    """Run all checks; exit non-zero on blocking findings.

    Phase 7 fix: output is now a multi-line summary (not a single
    line) plus a machine-readable JSON status block. The summary
    is for humans reading the CI log; the JSON block is for tools
    that parse CI output (e.g. dashboarding, alerting).
    """
    result = _run_full_pipeline(config_path, render_reports=True)
    config = load_config(config_path)
    output_dir = Path(config.output_directory)
    exec_report = output_dir / "executive_report.md"
    status = "PASS" if result.ci_passed else "FAIL"
    # Multi-line human summary
    click.echo(f"=== SGP CI {status} ===")
    click.echo(f"Artifacts scanned: {len(result.inventory)}")
    click.echo(f"Total findings: {len(result.findings)}")
    click.echo(f"Blocking findings: {result.ci_blocking_count}")
    click.echo(f"Health score: {result.health_score}/100")
    # Breakdown by category/severity for the top 3 categories
    from collections import Counter
    cats = Counter(f.category for f in result.findings if f.severity.value == "blocking")
    if cats:
        top3 = ", ".join(f"{c}={n}" for c, n in cats.most_common(3))
        click.echo(f"Top blocking categories: {top3}")
    click.echo(f"Report: {exec_report}")
    # Machine-readable JSON status block (sentinel-delimited)
    status_block = {
        "passed": result.ci_passed,
        "artifacts": len(result.inventory),
        "findings": len(result.findings),
        "blocking": result.ci_blocking_count,
        "health_score": result.health_score,
        "report": str(exec_report),
        "timestamp": utc_now_iso(),
    }
    click.echo("SGP-CI-STATUS-BEGIN")
    click.echo(json.dumps(status_block, indent=2))
    click.echo("SGP-CI-STATUS-END")
    if not result.ci_passed:
        sys.exit(1)


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


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.argument("files", nargs=-1, type=click.Path(exists=True, path_type=Path))
def validate_files(config_path: Path, files: tuple[Path, ...]) -> None:
    """Run validation scoped to specific files (staged in git, etc).

    Scans the configured directories, runs metadata + contract
    validation, then filters findings to those whose `artifact_path`
    matches one of the supplied files. Exits non-zero when any
    blocking finding remains after filtering.

    This is the surface the pre-commit hook uses: it passes the
    staged files (via `git diff --cached --name-only`) and gets
    back a pass/fail signal.

    Usage:
        python -m skill_governance.cli validate-files \\
            --config config/governance.yaml path/to/SKILL.md
    """
    if not files:
        click.echo("validate-files: no files specified, nothing to do.")
        return

    # Compute the set of relative paths that match each input file.
    # Finding.artifact_path values are relative to the
    # skill_directories / agent_directories root, so we need to
    # compute the relative path from each possible root and check
    # if any of them match.
    config = load_config(config_path)
    roots = [Path(p).resolve() for p in config.skill_directories] + [Path(p).resolve() for p in config.agent_directories]

    file_rel_strs: set[str] = set()
    for input_file in files:
        input_abs = input_file.resolve()
        for root in roots:
            try:
                rel = input_abs.relative_to(root)
                file_rel_strs.add(str(rel))
            except ValueError:
                continue

    result = _run_validate(config_path)
    findings_in_scope = [f for f in result.findings if f.artifact_path and f.artifact_path in file_rel_strs]
    blocking = [f for f in findings_in_scope if f.severity.value == "blocking"]
    warnings = [f for f in findings_in_scope if f.severity.value == "warning"]

    click.echo(f"validate-files: {len(files)} file(s) in scope")
    click.echo(f"  Total findings in scope: {len(findings_in_scope)}")
    click.echo(f"  Blocking: {len(blocking)}")
    click.echo(f"  Warnings: {len(warnings)}")

    if blocking:
        click.echo("")
        click.echo("Blocking findings:")
        for f in blocking:
            click.echo(f"  - {f.artifact_path}: [{f.category}] {f.message}")
        click.echo("")
        click.echo("Run `python -m skill_governance.cli rewrite --config <config>` "
                   "for proposed fixes, or fix manually.")
        sys.exit(2)
    elif warnings:
        click.echo("")
        click.echo("Warnings (non-blocking):")
        for f in warnings:
            click.echo(f"  - {f.artifact_path}: [{f.category}] {f.message}")


@main.command()
@click.argument("target_repo", type=click.Path(exists=True, path_type=Path))
def install_hooks(target_repo: Path) -> None:
    """Install the SGP pre-commit hook into a target repo.

    Copies the hook script (shipped with SGP at `hooks/pre-commit`)
    into the target repo's `.git/hooks/pre-commit` and marks it
    executable. The hook runs `sgp validate-files` on staged files
    when you commit, blocking commits that introduce blocking
    governance findings.

    Usage:
        cd path/to/your/skill-repo
        python -m skill_governance.cli install-hooks .

    The target repo must be a git repository (i.e. have a .git/
    directory). If `.git/` is missing, the command exits non-zero
    with an error.
    """
    git_dir = target_repo / ".git"
    if not git_dir.is_dir():
        click.echo(f"install-hooks: error: {target_repo} is not a git repository (no .git/ directory).", err=True)
        click.echo("  Initialize a repo with `git init` first, or run from a different directory.", err=True)
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_dest = hooks_dir / "pre-commit"

    # Locate the hook script shipped with SGP. It's at
    # <sgp-package>/hooks/pre-commit. We can find the package root
    # via the import location of `skill_governance`.
    import skill_governance
    sgp_root = Path(skill_governance.__file__).resolve().parent.parent.parent
    hook_src = sgp_root / "hooks" / "pre-commit"

    if not hook_src.exists():
        click.echo(f"install-hooks: error: hook script not found at {hook_src}.", err=True)
        click.echo("  This is an SGP installation issue. Try reinstalling.", err=True)
        sys.exit(1)

    # Copy the hook and make it executable.
    hook_dest.write_text(hook_src.read_text(encoding="utf-8"), encoding="utf-8")
    hook_dest.chmod(hook_dest.stat().st_mode | 0o111)

    click.echo(f"install-hooks: installed SGP pre-commit hook at {hook_dest}")
    click.echo("  The hook will run on every `git commit` in this repo.")
    click.echo("  Bypass with `git commit --no-verify` if needed (not recommended).")


@main.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--top-n", default=3, type=int, help="Number of recommendations to return (default 3).")
@click.argument("task", nargs=1, type=str)
def recommend_task(config_path: Path, top_n: int, task: str) -> None:
    """Recommend agents and skills for a natural-language task.

    Loads the catalog from the configured skill_directories and
    agent_directories, then matches the TASK string against each
    artifact's purpose and 'situation' text using a deterministic
    token-based Jaccard similarity. Returns the top N (default 3)
    results.

    This is the 'where do I start?' tool for users who don't yet
    know the catalog. It's deterministic (no LLM), fast, and
    inspectable. Pair with the CATALOG.md decision guide in
    test-repo for a complete navigation experience.

    Example:
        python -m skill_governance.cli recommend-task \\
            --config config/governance.yaml \\
            "deploy my app to production"
    """
    from .config_loader import load_config
    from .discovery import DiscoveryConfig, discover
    from .metadata_parser import parse_metadata
    from .recommend_task import Artifact
    from .recommend_task import recommend_task as _recommend_task

    config = load_config(config_path)
    dcfg = DiscoveryConfig(
        skill_directories=[Path(p) for p in config.skill_directories],
        agent_directories=[Path(p) for p in config.agent_directories],
    )
    inv = discover(dcfg)

    # Build artifacts with situation + purpose text
    artifacts: list[Artifact] = []
    for a in inv:
        for root in dcfg.skill_directories + dcfg.agent_directories:
            cand = root / a.path
            if cand.exists():
                meta = parse_metadata(cand)
                purpose = meta.purpose or ""
                # Pull situation text from the body (the first
                # meaningful prose paragraph after the frontmatter)
                body = cand.read_text(encoding="utf-8")
                # Strip the frontmatter
                m = re.match(r"^---\s*\n.*?\n---\s*\n", body, re.DOTALL)
                body_no_fm = body[m.end():] if m else body
                # First non-empty, non-heading paragraph
                situation_lines: list[str] = []
                for line in body_no_fm.splitlines():
                    s = line.strip()
                    if not s:
                        if situation_lines:
                            break
                        continue
                    if s.startswith("#"):
                        if situation_lines:
                            break
                        continue
                    if s.startswith("-") or s.startswith("*"):
                        if situation_lines:
                            break
                        continue
                    situation_lines.append(s)
                situation = " ".join(situation_lines)[:200]
                artifacts.append(Artifact(
                    name=a.name,
                    type=a.artifact_type.value,
                    situation=situation,
                    purpose=purpose,
                ))
                break

    results = _recommend_task(task, artifacts, top_n=top_n)
    if not results:
        click.echo(f"recommend-task: no matches for {task!r}")
        click.echo("  Try different wording, or check the catalog (agents/CATALOG.md).")
        return

    click.echo(f"recommend-task: top {len(results)} match(es) for {task!r}")
    click.echo("")
    for i, (name, atype, score) in enumerate(results, 1):
        click.echo(f"  {i}. [{atype}] {name} (score={score:.3f})")
    if not results:
        sys.exit(0)


if __name__ == "__main__":
    main()
