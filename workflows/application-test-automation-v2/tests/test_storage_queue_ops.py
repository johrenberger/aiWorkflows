from __future__ import annotations

from test_factory.models import RiskScoreRecord, WorkItemRecord
from test_factory.storage import Storage


def test_storage_round_trip(tmp_path):
    db = Storage(tmp_path / "state.sqlite")
    db.upsert_risk_score(RiskScoreRecord(path="a.py", module="m", line_coverage=50.0, branch_coverage=None, coverage_gap=40.0, risk_score=10.0))
    rows = db.fetch_all("risk_scores")
    assert rows[0]["path"] == "a.py"
    db.close()


def test_work_item_status_and_validation_metadata_survive_regeneration(tmp_path):
    db = Storage(tmp_path / "state.sqlite")
    db.upsert_work_item(
        WorkItemRecord(
            work_item_id="wi-1",
            source_path="package/foo.py",
            language="python",
            module="package",
            current_line_coverage=50.0,
            current_branch_coverage=50.0,
            status="passed",
            validated_files=["tests/test_generated.py"],
            validation_repo_sha="abc123",
            validation_reason="",
        )
    )
    db.upsert_work_item(
        WorkItemRecord(
            work_item_id="wi-1",
            source_path="package/foo.py",
            language="python",
            module="package",
            current_line_coverage=60.0,
            current_branch_coverage=60.0,
        )
    )
    row = db.get_work_item("wi-1")
    assert row["status"] == "passed"
    assert "tests/test_generated.py" in row["validated_files"]
    assert row["validation_repo_sha"] == "abc123"
    db.close()
