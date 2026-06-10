from __future__ import annotations

from test_factory.models import RiskScoreRecord
from test_factory.storage import Storage


def test_storage_round_trip(tmp_path):
    db = Storage(tmp_path / "state.sqlite")
    db.upsert_risk_score(RiskScoreRecord(path="a.py", module="m", line_coverage=50.0, branch_coverage=None, coverage_gap=40.0, risk_score=10.0))
    rows = db.fetch_all("risk_scores")
    assert rows[0]["path"] == "a.py"
    db.close()
