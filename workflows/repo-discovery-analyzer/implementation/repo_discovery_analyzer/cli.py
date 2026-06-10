from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from . import __version__
from .detectors.build_deploy import detect_build_deploy
from .detectors.contradictions import detect_contradictions
from .detectors.database import detect_database_schema
from .detectors.dependencies import detect_dependencies
from .detectors.entry_points import detect_entry_points
from .detectors.error_logging import detect_error_logging
from .github_links import build_links_by_path, commit_pinned_prefix, detect_default_branch, parse_github_url
from .detectors.hygiene import detect_hygiene
from .integrations import detect_integrations
from .inventory import build_project_structure, scan_repo
from .io_utils import DEFAULT_MAX_SUMMARY_ITEMS, clear_safe_read_text_cache, json_dump
from .detectors.java_spring import detect_java_spring_routes
from .detectors.javascript import detect_javascript_routes
from .loc_metrics import compute_loc_metrics
from .markdown_report import REPORT_NAME, generate_markdown_report
from .model import AnalysisConfig, AnalysisManifest, TOOL_NAME, dataclass_to_json
from .detectors.security import detect_security
from .detectors.stack import detect_stack
from .detectors.testing import detect_testing
from .validation import validate_outputs


REQUIRED_OUTPUTS = [
    "analysis_manifest.json",
    "repo_inventory.json",
    "loc_metrics.json",
    "tech_stack.json",
    "entry_points.json",
    "project_structure.json",
    "routes.json",
    "db_schema.json",
    "dependencies.json",
    "integrations.json",
    "tests.json",
    "error_logging.json",
    "security_signals.json",
    "build_deploy.json",
    "hygiene_findings.json",
    "contradiction_candidates.json",
    "github_links.json",
    "validation_report.json",
    REPORT_NAME,
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-discovery-analyzer")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--github-url", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--include-large-files", action="store_true")
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    parser.add_argument("--json-indent", type=int, default=2)
    parser.add_argument("--fail-on-validation-error", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    clear_safe_read_text_cache()
    args = build_parser().parse_args(argv)
    cfg = AnalysisConfig(
        repo_path=Path(args.repo_path).resolve(),
        github_url=args.github_url,
        commit=args.commit,
        output_dir=Path(args.output_dir).resolve(),
        include_large_files=args.include_large_files,
        max_file_bytes=args.max_file_bytes,
        json_indent=args.json_indent,
        fail_on_validation_error=args.fail_on_validation_error,
        verbose=args.verbose,
    )
    start = perf_counter()
    start_time = datetime.now(timezone.utc).isoformat()
    warnings: list[str] = []

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    if not cfg.repo_path.exists():
        raise SystemExit(f"repo path does not exist: {cfg.repo_path}")

    try:
        owner, repo = parse_github_url(cfg.github_url)
    except ValueError as exc:
        raise SystemExit(str(exc))

    default_branch = detect_default_branch(cfg.repo_path)

    records = scan_repo(cfg.repo_path, owner, repo, cfg.commit, cfg.include_large_files, cfg.max_file_bytes)
    skipped = [record.path for record in records if record.skipped]
    if skipped:
        warnings.extend([f"skipped {path}" for path in skipped[:200]])
    if not records:
        warnings.append("no files were analyzed")

    inventory = {"repo_path": str(cfg.repo_path), "files": [dataclass_to_json(r) for r in records]}
    structure = build_project_structure(cfg.repo_path, records)
    loc_metrics = compute_loc_metrics(records)
    stack = detect_stack(cfg.repo_path, owner, repo, cfg.commit, records)
    entry_points = detect_entry_points(cfg.repo_path, owner, repo, cfg.commit, records)
    java_routes = detect_java_spring_routes(cfg.repo_path, owner, repo, cfg.commit, records)
    js_routes = detect_javascript_routes(cfg.repo_path, owner, repo, cfg.commit, records)
    database_schema = detect_database_schema(cfg.repo_path, owner, repo, cfg.commit, records)
    all_merged_routes = _merge_sorted(
        java_routes.get("routes", []) + js_routes.get("routes", []),
        key_fields=["source_file", "method", "path"],
    )
    route_source_truncated = java_routes.get("routes_truncated", False) or js_routes.get("routes_truncated", False)
    merged_routes = all_merged_routes[:DEFAULT_MAX_SUMMARY_ITEMS]
    routes_total = (
        java_routes.get("routes_total", len(java_routes.get("routes", [])))
        + js_routes.get("routes_total", len(js_routes.get("routes", [])))
        if route_source_truncated
        else len(all_merged_routes)
    )
    routes = {
        "routes": merged_routes,
        "routes_total": routes_total,
        "routes_truncated": route_source_truncated or len(all_merged_routes) > len(merged_routes),
    }
    all_merged_entities = _merge_sorted(
        java_routes.get("entities", []) + js_routes.get("entities", []) + database_schema.get("entities", []),
        key_fields=["source_file", "name"],
    )
    entity_source_truncated = (
        java_routes.get("entities_truncated", False)
        or js_routes.get("entities_truncated", False)
        or database_schema.get("entities_truncated", False)
    )
    merged_entities = all_merged_entities[:DEFAULT_MAX_SUMMARY_ITEMS]
    entities_total = (
        (
            java_routes.get("entities_total", len(java_routes.get("entities", [])))
            + js_routes.get("entities_total", len(js_routes.get("entities", [])))
            + database_schema.get("entities_total", len(database_schema.get("entities", [])))
        )
        if entity_source_truncated
        else len(all_merged_entities)
    )
    db_schema = {
        "entities": merged_entities,
        "entities_total": entities_total,
        "entities_truncated": entity_source_truncated or len(all_merged_entities) > len(merged_entities),
    }
    dependencies = detect_dependencies(cfg.repo_path, owner, repo, cfg.commit, records)
    testing = detect_testing(cfg.repo_path, owner, repo, cfg.commit, records)
    security = detect_security(cfg.repo_path, owner, repo, cfg.commit, records)
    error_logging = detect_error_logging(cfg.repo_path, owner, repo, cfg.commit, records)
    build_deploy = detect_build_deploy(cfg.repo_path, owner, repo, cfg.commit, records)
    hygiene = detect_hygiene(cfg.repo_path, owner, repo, cfg.commit, records)
    integrations = detect_integrations(cfg.repo_path, owner, repo, cfg.commit, records, dependencies, security, stack)
    contradictions = detect_contradictions(cfg.repo_path, owner, repo, cfg.commit, records, stack, routes, testing, build_deploy)

    links_by_path = build_links_by_path(owner, repo, cfg.commit, [record.path for record in records])
    github_links = {
        "repo_url": cfg.github_url,
        "commit": cfg.commit,
        "default_branch": default_branch,
        "source_url_prefix": commit_pinned_prefix(owner, repo, cfg.commit),
        "links_by_path": links_by_path,
    }

    outputs = {
        "analysis_manifest.json": dataclass_to_json(
            AnalysisManifest(
                tool_name=TOOL_NAME,
                tool_version=__version__,
                repo_path=str(cfg.repo_path),
                source_url_prefix=commit_pinned_prefix(owner, repo, cfg.commit),
                commit=cfg.commit,
                output_dir=str(cfg.output_dir),
                start_time_utc=start_time,
                end_time_utc=datetime.now(timezone.utc).isoformat(),
                elapsed_ms=int((perf_counter() - start) * 1000),
                warnings=warnings,
                skipped_files=skipped,
            )
        ),
        "repo_inventory.json": inventory,
        "loc_metrics.json": loc_metrics,
        "tech_stack.json": stack,
        "entry_points.json": entry_points,
        "project_structure.json": structure,
        "routes.json": routes,
        "db_schema.json": db_schema,
        "dependencies.json": dependencies,
        "integrations.json": integrations,
        "tests.json": testing,
        "error_logging.json": error_logging,
        "security_signals.json": security,
        "build_deploy.json": build_deploy,
        "hygiene_findings.json": hygiene,
        "contradiction_candidates.json": contradictions,
        "github_links.json": github_links,
    }

    for name, payload in outputs.items():
        json_dump(cfg.output_dir / name, payload, indent=cfg.json_indent)

    required_evidence = [name for name in REQUIRED_OUTPUTS if name.endswith(".json") and name != "validation_report.json"]
    validation = validate_outputs(cfg.output_dir, required_evidence, warnings, repo_path=cfg.repo_path, commit=cfg.commit)
    json_dump(cfg.output_dir / "validation_report.json", validation, indent=cfg.json_indent)
    generate_markdown_report(cfg.output_dir)

    if cfg.fail_on_validation_error and validation["status"] == "failed":
        return 1
    return 0


def _merge_sorted(
    items: list[dict],
    key_fields: list[str] | None = None,
) -> list[dict]:
    """Merge items from multiple detector outputs, deduping by a chosen key.

    When `key_fields` is None, the function falls back to the previous
    behaviour of deduping by the full JSON of the entry (which means two
    records that differ in any field — including derived fields like
    `relationships` — are NOT considered duplicates). That was the bug we
    hit on johrenberger/BroadleafCommerce: 109 files produced two
    `db_schema.json` entries because the `database` and `java_spring`
    detectors both extracted the same `@Entity`, but with different
    `relationships` arrays derived from different lines of the same file.

    When `key_fields` is provided, dedup uses a tuple of the named fields
    instead, so the two records collapse into one regardless of any other
    variation. Callers should pick key fields that uniquely identify the
    discovery across detectors — e.g. `["source_file", "name"]` for
    entities and `["source_file", "method", "path"]` for routes.

    The order of `items` is preserved on first occurrence; the merged
    result is then sorted by JSON for deterministic output (matching the
    previous behaviour).
    """
    seen: set = set()
    merged: list[dict] = []
    if key_fields is None:
        for item in items:
            k = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if k in seen:
                continue
            seen.add(k)
            merged.append(item)
    else:
        for item in items:
            k = tuple(item.get(f) for f in key_fields)
            if k in seen:
                continue
            seen.add(k)
            merged.append(item)
    return sorted(merged, key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
