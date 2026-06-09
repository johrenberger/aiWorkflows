from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


REPORT_NAME = "analysis_report.md"
MAX_REPORT_ROWS = 50


def generate_markdown_report(output_dir: Path) -> Path:
    data = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(output_dir.glob("*.json"), key=lambda item: item.name)
    }
    report_path = output_dir / REPORT_NAME
    report_path.write_text(render_markdown_report(data), encoding="utf-8", newline="\n")
    return report_path


def render_markdown_report(data: dict[str, Any]) -> str:
    manifest = _mapping(data.get("analysis_manifest"))
    links = _mapping(data.get("github_links"))
    loc = _mapping(data.get("loc_metrics"))
    validation = _mapping(data.get("validation_report"))
    tests = _mapping(data.get("tests"))
    ratio = _mapping(tests.get("source_to_test_ratio"))
    repo_url = str(links.get("repo_url") or "")
    repo_name = repo_url.rstrip("/").rsplit("/", 1)[-1] or Path(str(manifest.get("repo_path") or "repository")).name

    lines = [
        f"# Repository Analysis: {_text(repo_name)}",
        "",
        f"> Deterministic analysis of [{_text(repo_url or repo_name)}]({repo_url}) at commit `{_text(manifest.get('commit'))}`.",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Validation | {_text(validation.get('status', 'unknown'))} |",
        f"| Files analyzed | {_number(loc.get('total_files'))} |",
        f"| Lines | {_number(loc.get('total_lines'))} |",
        f"| Source files | {_number(ratio.get('source_files'))} |",
        f"| Test files | {_number(ratio.get('test_files'))} |",
        f"| Test/source ratio | {_text(ratio.get('ratio'))} |",
        f"| Skipped files | {_number(len(_list(manifest.get('skipped_files'))))} |",
        f"| Analyzer elapsed time | {_number(manifest.get('elapsed_ms'))} ms |",
        "",
    ]

    _technology_section(lines, data)
    _structure_section(lines, data)
    _entry_point_section(lines, data)
    _route_section(lines, data)
    _data_section(lines, data)
    _dependency_section(lines, data)
    _integration_section(lines, data)
    _testing_section(lines, data)
    _security_section(lines, data)
    _reliability_section(lines, data)
    _build_section(lines, data)
    _hygiene_section(lines, data)
    _contradiction_section(lines, data)
    _warning_section(lines, manifest, validation)
    _evidence_section(lines, data)

    return "\n".join(lines).rstrip() + "\n"


def _technology_section(lines: list[str], data: dict[str, Any]) -> None:
    items = _list(_mapping(data.get("tech_stack")).get("technologies"))
    rows = [
        [
            item.get("technology"),
            item.get("category"),
            item.get("version") or "",
            item.get("confidence"),
            _linked_path(item),
        ]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(lines, "Technology Stack", ["Technology", "Category", "Version", "Confidence", "Evidence"], rows, len(items))


def _structure_section(lines: list[str], data: dict[str, Any]) -> None:
    structure = _mapping(data.get("project_structure"))
    lines.extend(["## Project Structure", ""])
    top_level = _list(structure.get("top_level_entries"))
    lines.append("**Top-level entries:** " + (", ".join(f"`{_text(item)}`" for item in top_level) or "None detected."))
    lines.extend(["", "| Directory | Files |", "| --- | ---: |"])
    notable = _list(structure.get("notable_directories"))
    if notable:
        for item in notable[:MAX_REPORT_ROWS]:
            lines.append(f"| `{_cell(item.get('path'))}` | {_number(item.get('file_count'))} |")
    else:
        lines.append("| None detected | 0 |")
    lines.append("")
    reading_order = _list(structure.get("reading_order"))
    if reading_order:
        lines.extend(["**Suggested reading order:**", ""])
        lines.extend(f"1. `{_text(path)}`" for path in reading_order)
        lines.append("")


def _entry_point_section(lines: list[str], data: dict[str, Any]) -> None:
    items = _list(_mapping(data.get("entry_points")).get("entry_points"))
    rows = [
        [item.get("type"), item.get("framework"), item.get("handler"), _linked_path(item), item.get("confidence")]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(lines, "Entry Points", ["Type", "Framework", "Handler", "Source", "Confidence"], rows, len(items))


def _route_section(lines: list[str], data: dict[str, Any]) -> None:
    payload = _mapping(data.get("routes"))
    items = _list(payload.get("routes"))
    rows = [
        [item.get("method"), item.get("path"), item.get("framework"), item.get("handler"), _linked_path(item)]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(
        lines,
        "API Routes",
        ["Method", "Path", "Framework", "Handler", "Source"],
        rows,
        int(payload.get("routes_total", len(items)) or 0),
        bool(payload.get("routes_truncated")),
    )


def _data_section(lines: list[str], data: dict[str, Any]) -> None:
    payload = _mapping(data.get("db_schema"))
    items = _list(payload.get("entities"))
    rows = [
        [
            item.get("name"),
            item.get("migration_source_type"),
            len(_list(item.get("fields"))),
            ", ".join(str(value) for value in _list(item.get("relationships"))),
            _linked_path(item),
        ]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(
        lines,
        "Data Model",
        ["Entity", "Source Type", "Fields", "Relationships", "Source"],
        rows,
        int(payload.get("entities_total", len(items)) or 0),
        bool(payload.get("entities_truncated")),
    )


def _dependency_section(lines: list[str], data: dict[str, Any]) -> None:
    items = _list(_mapping(data.get("dependencies")).get("dependencies"))
    rows = [
        [item.get("name"), item.get("version"), item.get("ecosystem"), item.get("likely_role"), _linked_path(item)]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(lines, "Dependencies", ["Name", "Version", "Ecosystem", "Role", "Source"], rows, len(items))


def _integration_section(lines: list[str], data: dict[str, Any]) -> None:
    items = _list(_mapping(data.get("integrations")).get("integrations"))
    rows = [
        [item.get("technology"), item.get("category"), item.get("confidence"), _linked_path(item)]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(lines, "Integrations", ["Technology", "Category", "Confidence", "Evidence"], rows, len(items))


def _testing_section(lines: list[str], data: dict[str, Any]) -> None:
    payload = _mapping(data.get("tests"))
    ratio = _mapping(payload.get("source_to_test_ratio"))
    lines.extend(
        [
            "## Testing",
            "",
            f"- Source files: {_number(ratio.get('source_files'))}",
            f"- Test files: {_number(ratio.get('test_files'))}",
            f"- Test/source ratio: {_text(ratio.get('ratio'))}",
            "",
        ]
    )
    items = _list(payload.get("testing"))
    rows = [
        [
            item.get("type"),
            item.get("framework_tool"),
            item.get("command"),
            item.get("confidence"),
            int(item.get("path_count", len(_list(item.get("paths")))) or 0),
        ]
        for item in items
        if isinstance(item, dict)
    ]
    _table(lines, ["Signal", "Framework/Tool", "Command", "Confidence", "Paths"], rows)


def _security_section(lines: list[str], data: dict[str, Any]) -> None:
    payload = _mapping(data.get("security_signals"))
    items = _list(payload.get("security_signals"))
    rows = [
        [item.get("severity"), item.get("category"), item.get("signal"), _linked_path(item), item.get("confidence")]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(
        lines,
        "Security Signals",
        ["Severity", "Category", "Signal", "Source", "Confidence"],
        rows,
        int(payload.get("security_signals_total", len(items)) or 0),
        bool(payload.get("security_signals_truncated")),
    )


def _reliability_section(lines: list[str], data: dict[str, Any]) -> None:
    payload = _mapping(data.get("error_logging"))
    items = _list(payload.get("error_logging"))
    rows = [
        [item.get("category"), item.get("technology"), _linked_path(item), item.get("confidence")]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(
        lines,
        "Error Handling and Observability",
        ["Category", "Technology", "Source", "Confidence"],
        rows,
        int(payload.get("error_logging_total", len(items)) or 0),
        bool(payload.get("error_logging_truncated")),
    )


def _build_section(lines: list[str], data: dict[str, Any]) -> None:
    items = _list(_mapping(data.get("build_deploy")).get("build_deploy"))
    rows = [
        [
            item.get("artifact_type"),
            item.get("detected_runtime"),
            ", ".join(str(value) for value in _list(item.get("commands_or_ports"))),
            _linked_path(item),
            item.get("confidence"),
        ]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(lines, "Build and Deployment", ["Artifact", "Runtime", "Commands/Ports", "Source", "Confidence"], rows, len(items))


def _hygiene_section(lines: list[str], data: dict[str, Any]) -> None:
    payload = _mapping(data.get("hygiene_findings"))
    items = _list(payload.get("hygiene_findings"))
    total = int(payload.get("hygiene_findings_total", len(items)) or 0)
    counts = Counter(str(item.get("type", "unknown")) for item in items if isinstance(item, dict))
    lines.extend(["## Hygiene and Technical Debt", "", f"Total findings: **{_number(total)}**", ""])
    if counts:
        lines.extend(["| Type | Findings in rendered JSON set |", "| --- | ---: |"])
        for name, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
            lines.append(f"| {_cell(name)} | {_number(count)} |")
        lines.append("")
    rows = [
        [item.get("type"), _linked_path(item), item.get("line_number"), item.get("impact_hint"), item.get("confidence")]
        for item in items
        if isinstance(item, dict)
    ]
    _table(lines, ["Type", "Source", "Line", "Impact", "Confidence"], rows)
    _truncation_note(lines, total, min(len(rows), MAX_REPORT_ROWS), bool(payload.get("hygiene_findings_truncated")) or len(rows) > MAX_REPORT_ROWS)


def _contradiction_section(lines: list[str], data: dict[str, Any]) -> None:
    items = _list(_mapping(data.get("contradiction_candidates")).get("contradiction_candidates"))
    rows = [
        [item.get("summary"), item.get("confidence"), item.get("impact_hint"), item.get("needs_ai_interpretation")]
        for item in items
        if isinstance(item, dict)
    ]
    _table_section(lines, "Contradiction Candidates", ["Summary", "Confidence", "Impact", "Needs Interpretation"], rows, len(items))


def _warning_section(lines: list[str], manifest: dict[str, Any], validation: dict[str, Any]) -> None:
    warnings = [str(item) for item in _list(manifest.get("warnings")) + _list(validation.get("warnings"))]
    warnings = list(dict.fromkeys(warnings))
    lines.extend(["## Warnings", ""])
    if warnings:
        lines.extend(f"- {_text(item)}" for item in warnings[:MAX_REPORT_ROWS])
        _truncation_note(lines, len(warnings), min(len(warnings), MAX_REPORT_ROWS), len(warnings) > MAX_REPORT_ROWS)
    else:
        lines.append("No warnings were recorded.")
    lines.append("")


def _evidence_section(lines: list[str], data: dict[str, Any]) -> None:
    names = sorted(f"{name}.json" for name in data)
    lines.extend(["## Evidence Files", ""])
    lines.extend(f"- `{_text(name)}`" for name in names)
    lines.append("")


def _table_section(
    lines: list[str],
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    total: int,
    truncated: bool = False,
) -> None:
    lines.extend([f"## {title}", ""])
    _table(lines, headers, rows)
    _truncation_note(lines, total, min(len(rows), MAX_REPORT_ROWS), truncated or len(rows) > MAX_REPORT_ROWS)


def _table(lines: list[str], headers: list[str], rows: list[list[Any]]) -> None:
    lines.append("| " + " | ".join(_cell(value) for value in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    if not rows:
        lines.append("| " + " | ".join(["None detected"] + [""] * (len(headers) - 1)) + " |")
    else:
        for row in rows[:MAX_REPORT_ROWS]:
            lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    lines.append("")


def _truncation_note(lines: list[str], total: int, shown: int, truncated: bool) -> None:
    if truncated or total > shown:
        lines.extend([f"_Showing {_number(shown)} of {_number(total)} items. See the JSON evidence for the complete bounded dataset._", ""])


def _linked_path(item: dict[str, Any]) -> str:
    paths = _list(item.get("evidence_paths"))
    urls = _list(item.get("evidence_urls"))
    path = item.get("source_file") or item.get("path") or (paths[0] if paths else "")
    url = item.get("github_url") or (urls[0] if urls else "")
    if path and url:
        return f"[`{_text(path)}`]({_text(url)})"
    return f"`{_text(path)}`" if path else ""


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number(value: Any) -> str:
    return f"{value:,}" if isinstance(value, int) else _text(value)


def _cell(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", " ")


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)
