from __future__ import annotations

import json
from pathlib import Path


def render_json_report(artifacts_dir: str | Path) -> str:
    artifacts_dir = Path(artifacts_dir)
    report = {}
    for name in ("repo_inventory.json", "coverage_baseline.json", "risk_scores.json", "test_gap_queue.json", "component_test_candidates.json", "exclusions.json"):
        path = artifacts_dir / name
        if path.exists():
            report[name] = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(report, indent=2, sort_keys=True)

