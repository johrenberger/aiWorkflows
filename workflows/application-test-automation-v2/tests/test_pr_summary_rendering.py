from __future__ import annotations

import json

from test_factory.git.pr_summary import render_pr_summary
from test_factory.models import ValidationRunRecord, WorkItemRecord
from test_factory.storage import Storage


def test_pr_summary_rendering_uses_deterministic_artifacts(tmp_path):
    (tmp_path / "risk_scores.json").write_text(
        json.dumps([{"path": "package/foo.py", "risk_score": 10.0, "line_coverage": 50.0}]),
        encoding="utf-8",
    )
    (tmp_path / "test_gap_queue.json").write_text(json.dumps([{"source_path": "package/foo.py"}]), encoding="utf-8")
    coverage_deltas = tmp_path / "coverage_deltas"
    coverage_deltas.mkdir()
    (coverage_deltas / "wi-1.json").write_text(
        json.dumps(
            {
                "work_item_id": "wi-1",
                "source_path": "package/foo.py",
                "before_line_coverage": 50.0,
                "after_line_coverage": 100.0,
            }
        ),
        encoding="utf-8",
    )
    mutation_dir = tmp_path / "mutation"
    mutation_dir.mkdir()
    (mutation_dir / "mutation_results.json").write_text(json.dumps([{"tool": "mutmut", "exit_code": 0, "status": "completed"}]), encoding="utf-8")
    (tmp_path / "exclusions.json").write_text(json.dumps([{"path": "coverage.xml"}]), encoding="utf-8")
    db = Storage(tmp_path / "test_factory.sqlite")
    db.upsert_work_item(
        WorkItemRecord(
            work_item_id="wi-1",
            source_path="package/foo.py",
            language="python",
            module="package",
            current_line_coverage=50.0,
            current_branch_coverage=50.0,
            validated_files=["tests/test_generated.py"],
            validation_repo_sha="abc123",
            status="passed",
        )
    )
    db.insert_validation_run(
        ValidationRunRecord(
            work_item_id="wi-1",
            command="pytest",
            exit_code=0,
            phase="targeted",
        )
    )
    db.close()

    summary = render_pr_summary(tmp_path, branch_name="branch", module="package")

    assert "Risk-weighted coverage delta" in summary
    assert "tests/test_generated.py" in summary
    assert "`pytest`" in summary
    assert "mutmut" in summary
