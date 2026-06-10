from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def _load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _load_work_items(db_path: Path) -> list[dict]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM work_items")]
    finally:
        conn.close()


def _load_validation_commands(db_path: Path) -> list[str]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    try:
        commands = [row[0] for row in conn.execute("SELECT DISTINCT command FROM validation_runs ORDER BY command ASC")]
        return [command for command in commands if command]
    finally:
        conn.close()


def _test_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(("tests/", "test/", "src/test/", "src/integrationTest/")) or ".test." in normalized or ".spec." in normalized


def render_pr_summary(artifacts_dir: str | Path, branch_name: str = "", module: str = "") -> str:
    artifacts_dir = Path(artifacts_dir)
    risk_scores = _load_json(artifacts_dir / "risk_scores.json", [])
    queue = _load_json(artifacts_dir / "test_gap_queue.json", [])
    mutation_results = _load_json(artifacts_dir / "mutation" / "mutation_results.json", [])
    exclusions = _load_json(artifacts_dir / "exclusions.json", [])
    db_path = artifacts_dir / "test_factory.sqlite"
    work_items = _load_work_items(db_path)
    validation_commands = _load_validation_commands(db_path)
    coverage_delta_paths = sorted(
        path
        for path in (artifacts_dir / "coverage_deltas").glob("*.json")
        if path.name != "baseline.json"
    )
    deltas = [_load_json(path, {}) for path in coverage_delta_paths]
    baseline_by_path = {item.get("path"): item for item in risk_scores}
    files_changed = sorted(
        {
            changed
            for item in work_items
            for changed in json.loads(item.get("validated_files", "[]"))
            if changed
        }
    )
    tests_changed = [path for path in files_changed if _test_file(path)]
    before_values = [float(delta["before_line_coverage"]) for delta in deltas if delta.get("before_line_coverage") is not None]
    after_values = [float(delta["after_line_coverage"]) for delta in deltas if delta.get("after_line_coverage") is not None]
    before = sum(before_values) / len(before_values) if before_values else 0.0
    after = sum(after_values) / len(after_values) if after_values else before
    weighted_delta = 0.0
    weighted_total = 0.0
    for delta in deltas:
        source_path = delta.get("source_path")
        score = float(baseline_by_path.get(source_path, {}).get("risk_score", 0.0))
        if score <= 0 or delta.get("after_line_coverage") is None or delta.get("before_line_coverage") is None:
            continue
        weighted_delta += (float(delta["after_line_coverage"]) - float(delta["before_line_coverage"])) * score
        weighted_total += score
    risk_weighted_delta = weighted_delta / weighted_total if weighted_total else 0.0
    remaining_exceptions = len(exclusions)
    limitations = []
    if not deltas:
        limitations.append("no validated coverage delta artifacts recorded yet")
    if not files_changed:
        limitations.append("no validated file set has been recorded yet")
    if not mutation_results:
        limitations.append("no mutation executions were recorded")
    lines = [
        "# PR Summary",
        f"- Branch: `{branch_name or 'n/a'}`",
        f"- Module scope: `{module or 'n/a'}`",
        f"- Coverage before: `{before:.2f}%`",
        f"- Coverage after: `{after:.2f}%`",
        f"- Risk-weighted coverage delta: `{risk_weighted_delta:.2f}`",
        f"- Queue items: `{len(queue)}`",
        "",
        "## Files Changed",
    ]
    lines.extend([f"- {path}" for path in files_changed] or ["- none recorded"])
    lines.extend(["", "## Tests Added or Updated"])
    lines.extend([f"- {path}" for path in tests_changed] or ["- none recorded"])
    lines.extend(["", "## Validation Commands Run"])
    lines.extend([f"- `{command}`" for command in validation_commands] or ["- none recorded"])
    lines.extend(["", "## Mutation Results"])
    if mutation_results:
        for item in mutation_results:
            lines.append(f"- {item.get('tool', '')} | exit_code={item.get('exit_code', '')} | status={item.get('status', 'completed')}")
    else:
        lines.append("- none recorded")
    lines.extend(["", "## Remaining Exceptions", f"- `{remaining_exceptions}` recorded exclusions or exceptions"])
    lines.extend(["", "## Known Limitations"])
    lines.extend([f"- {item}" for item in limitations] or ["- none recorded"])
    return "\n".join(lines) + "\n"
