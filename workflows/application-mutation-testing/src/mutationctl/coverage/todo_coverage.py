from __future__ import annotations

import re
from pathlib import Path

from mutationctl.models import CoverageFileSummary

TABLE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)%\s*\|$")


def parse_todo_coverage(path: Path) -> list[CoverageFileSummary]:
    summaries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TABLE_ROW.match(line.strip())
        if match and match.group(1).strip().lower() != "source file":
            summaries.append(
                CoverageFileSummary(
                    match.group(1).strip(),
                    float(match.group(2)),
                    None,
                    [],
                    [],
                    str(path),
                    "PASS",
                )
            )
    return summaries
