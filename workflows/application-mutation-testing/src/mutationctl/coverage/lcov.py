from __future__ import annotations

from pathlib import Path

from mutationctl.models import CoverageFileSummary


def parse_lcov(path: Path) -> list[CoverageFileSummary]:
    summaries = []
    source_file = None
    covered = []
    uncovered = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("SF:"):
            source_file = raw_line[3:].replace("\\", "/")
        elif raw_line.startswith("DA:"):
            line_number, hits = raw_line[3:].split(",", 1)
            (covered if int(hits) > 0 else uncovered).append(int(line_number))
        elif raw_line == "end_of_record" and source_file:
            total = len(covered) + len(uncovered)
            summaries.append(
                CoverageFileSummary(
                    source_file,
                    round(len(covered) / total * 100, 2) if total else None,
                    None,
                    list(covered),
                    list(uncovered),
                    str(path),
                    "PASS",
                )
            )
            source_file, covered, uncovered = None, [], []
    return summaries
