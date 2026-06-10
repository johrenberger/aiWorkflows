from __future__ import annotations

import json

from test_factory.reports.markdown_report import render_final_report


def test_final_report_renders_queue_items_with_path_fallback(tmp_path):
    (tmp_path / "repo_inventory.json").write_text(json.dumps([{"path": "src/Foo.java"}]), encoding="utf-8")
    (tmp_path / "coverage_baseline.json").write_text(json.dumps([]), encoding="utf-8")
    (tmp_path / "risk_scores.json").write_text(json.dumps([{"path": "src/Foo.java", "missing_evidence": ["coverage"]}]), encoding="utf-8")
    (tmp_path / "test_gap_queue.json").write_text(json.dumps([{"path": "src/Foo.java", "priority": 123.0, "line_coverage": 10, "branch_coverage": None}]), encoding="utf-8")
    (tmp_path / "exclusions.json").write_text(json.dumps([]), encoding="utf-8")
    (tmp_path / "language_stack.json").write_text(json.dumps({"java": 1}), encoding="utf-8")
    (tmp_path / "module_graph.json").write_text(json.dumps({"src": {"java": 1}}), encoding="utf-8")
    (tmp_path / "risk_weighted_coverage.json").write_text(json.dumps({"line_index": 0.0, "branch_index": 0.0}), encoding="utf-8")
    (tmp_path / "component_test_candidates.json").write_text(json.dumps([]), encoding="utf-8")
    mutation_dir = tmp_path / "mutation"
    mutation_dir.mkdir()
    (mutation_dir / "mutation_candidates.json").write_text(json.dumps([]), encoding="utf-8")
    (mutation_dir / "mutation_results.json").write_text(json.dumps([]), encoding="utf-8")
    (mutation_dir / "mutation_tool_detection.json").write_text(json.dumps({"tool": "pitest", "available": True}), encoding="utf-8")

    report = render_final_report(tmp_path)

    assert "## Highest Risk Gaps" in report
    assert "src/Foo.java" in report
    assert "## Missing Evidence" in report
    assert "coverage" in report
