from __future__ import annotations

import json
from pathlib import Path


def _load_json(artifacts_dir: Path, name: str, default):
    path = artifacts_dir / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _item_path(item: dict) -> str:
    return str(item.get("source_path") or item.get("path") or "")


def _format_top_items(items: list[dict], limit: int = 10) -> list[str]:
    lines: list[str] = []
    for item in items[:limit]:
        path = _item_path(item) or "unknown"
        priority = item.get("priority", item.get("risk_score", 0))
        line_coverage = item.get("line_coverage", item.get("current_line_coverage", 0))
        branch_coverage = item.get("branch_coverage", item.get("current_branch_coverage"))
        lines.append(f"- {path} | line={line_coverage} | branch={branch_coverage} | priority={priority}")
    return lines


def render_final_report(artifacts_dir: str | Path) -> str:
    artifacts_dir = Path(artifacts_dir)
    inventory = _load_json(artifacts_dir, "repo_inventory.json", [])
    coverage = _load_json(artifacts_dir, "coverage_baseline.json", [])
    risk = _load_json(artifacts_dir, "risk_scores.json", [])
    queue = _load_json(artifacts_dir, "test_gap_queue.json", [])
    exclusions = _load_json(artifacts_dir, "exclusions.json", [])
    language_stack = _load_json(artifacts_dir, "language_stack.json", {})
    module_graph = _load_json(artifacts_dir, "module_graph.json", {})
    weighted = _load_json(artifacts_dir, "risk_weighted_coverage.json", {})
    component_candidates = _load_json(artifacts_dir, "component_test_candidates.json", [])
    mutation_dir = artifacts_dir / "mutation"
    mutation_candidates = _load_json(mutation_dir, "mutation_candidates.json", [])
    mutation_results = _load_json(mutation_dir, "mutation_results.json", [])
    mutation_detection = _load_json(mutation_dir, "mutation_tool_detection.json", {})
    coverage_files = [
        row
        for row in coverage
        if row.get("line_coverage", 0) < 90 or (row.get("branch_coverage") is not None and row.get("branch_coverage", 0) < 90)
    ]
    missing_evidence = sorted({item for row in risk for item in row.get("missing_evidence", [])})

    parts = [
        "# Final Report",
        f"- Files discovered: `{len(inventory)}`",
        f"- Coverage records: `{len(coverage)}`",
        f"- Risk records: `{len(risk)}`",
        f"- Queue items: `{len(queue)}`",
        f"- Exclusions: `{len(exclusions)}`",
        "",
        "## Language Stack",
    ]
    if language_stack:
        for language, count in language_stack.items():
            parts.append(f"- `{language}`: `{count}`")
    else:
        parts.append("- no language evidence recorded")

    parts.extend(
        [
            "",
            "## Module Graph Summary",
        ]
    )
    if module_graph:
        for module, langs in list(module_graph.items())[:10]:
            parts.append(f"- `{module}`: {langs}")
    else:
        parts.append("- no module graph recorded")

    parts.extend(
        [
            "",
            "## Coverage Baseline",
        ]
    )
    if coverage:
        parts.append(f"- Line-weighted index: `{weighted.get('line_index', 0)}`")
        parts.append(f"- Branch-weighted index: `{weighted.get('branch_index', 0)}`")
        parts.append(f"- Files below threshold: `{len(coverage_files)}`")
        for row in coverage_files[:10]:
            parts.append(f"- {_item_path(row)} | line={row.get('line_coverage', 0)} | branch={row.get('branch_coverage')}")
    else:
        parts.append("- no coverage reports were found")

    parts.extend(
        [
            "",
            "## Highest Risk Gaps",
        ]
    )
    if queue:
        parts.extend(_format_top_items(queue, 10))
    else:
        parts.append("- no queue items were generated")

    parts.extend(
        [
            "",
            "## Recommended Next Work Items",
        ]
    )
    if queue:
        parts.extend(_format_top_items(queue, 10))
    else:
        parts.append("- no recommendations available")

    parts.extend(
        [
            "",
            "## Component or Integration Candidates",
        ]
    )
    if component_candidates:
        parts.extend(_format_top_items(component_candidates, 10))
    else:
        parts.append("- none recorded")

    parts.extend(
        [
            "",
            "## Mutation Candidates",
        ]
    )
    if mutation_candidates:
        for item in mutation_candidates[:10]:
            parts.append(f"- {_item_path(item)} | score={item.get('score', 0)}")
    else:
        parts.append("- none recorded")

    parts.extend(
        [
            "",
            "## Mutation Results",
        ]
    )
    if mutation_results:
        for item in mutation_results[:10]:
            parts.append(f"- {_item_path(item)} | tool={item.get('tool', '')} | exit_code={item.get('exit_code', '')}")
    else:
        parts.append("- no mutation run results recorded")

    parts.extend(
        [
            "",
            "## Mutation Detection",
        ]
    )
    if mutation_detection:
        parts.append(f"- tool: `{mutation_detection.get('tool', '')}`")
        parts.append(f"- available: `{mutation_detection.get('available', False)}`")
    else:
        parts.append("- no mutation tool detection recorded")

    parts.extend(
        [
            "",
            "## Exclusions",
        ]
    )
    if exclusions:
        for row in exclusions[:10]:
            parts.append(f"- {row.get('path', 'unknown')} | {row.get('reason', '')} | {row.get('rule', '')}")
    else:
        parts.append("- none recorded")

    parts.extend(
        [
            "",
            "## Missing Evidence",
        ]
    )
    if missing_evidence:
        for item in missing_evidence:
            parts.append(f"- {item}")
    else:
        parts.append("- none recorded")

    parts.extend(
        [
            "",
            "## Adapter Confidence",
            "- adapter confidence is derived from detected stack evidence during scan; this workflow currently records the evidence, not a numeric confidence summary, in the final report",
            "",
            "## Limitations",
            "- coverage reports were not discovered in this run",
            "- branch coverage is only available where the underlying tool reports it",
            "- queue priorities are deterministic but depend on available file-level evidence",
        ]
    )
    return "\n".join(parts) + "\n"

