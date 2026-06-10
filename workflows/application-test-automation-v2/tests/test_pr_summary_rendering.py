from __future__ import annotations

import json

from test_factory.git.pr_summary import render_pr_summary


def test_pr_summary_rendering(tmp_path):
    (tmp_path / "risk_scores.json").write_text(json.dumps([{"line_coverage": 20.0}, {"line_coverage": 80.0}]), encoding="utf-8")
    (tmp_path / "test_gap_queue.json").write_text(json.dumps([{"source_path": "a.py"}]), encoding="utf-8")
    summary = render_pr_summary(tmp_path, branch_name="branch", module="module")
    assert "Branch" in summary
    assert "Coverage before" in summary
