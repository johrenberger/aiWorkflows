from __future__ import annotations

import json
from pathlib import Path


def render_pr_summary(artifacts_dir: str | Path, branch_name: str = "", module: str = "") -> str:
    artifacts_dir = Path(artifacts_dir)
    risk_path = artifacts_dir / "risk_scores.json"
    queue_path = artifacts_dir / "test_gap_queue.json"
    mutations_path = artifacts_dir / "mutation" / "mutation_results.json"
    risk_scores = json.loads(risk_path.read_text(encoding="utf-8")) if risk_path.exists() else []
    queue = json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.exists() else []
    mutation_results = json.loads(mutations_path.read_text(encoding="utf-8")) if mutations_path.exists() else []
    before = min((item.get("line_coverage", 0) for item in risk_scores), default=0)
    after = max((item.get("line_coverage", 0) for item in risk_scores), default=0)
    lines = [
        "# PR Summary",
        f"- Branch: `{branch_name or 'n/a'}`",
        f"- Module scope: `{module or 'n/a'}`",
        f"- Coverage before: `{before:.2f}%`",
        f"- Coverage after: `{after:.2f}%`",
        f"- Queue items: `{len(queue)}`",
        f"- Mutation results: `{len(mutation_results)}`",
    ]
    return "\n".join(lines) + "\n"

