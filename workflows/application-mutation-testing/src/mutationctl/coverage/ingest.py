from __future__ import annotations

from pathlib import Path

from mutationctl.coverage.coverage_xml import parse_coverage_xml
from mutationctl.coverage.lcov import parse_lcov
from mutationctl.coverage.todo_coverage import parse_todo_coverage
from mutationctl.models import CoverageSummary


def ingest_coverage(repo_path: str | Path, coverage_path: str | Path | None = None, store=None) -> CoverageSummary:
    root = Path(repo_path)
    if coverage_path is not None:
        candidates = [Path(coverage_path)]
    else:
        candidates = [root / "TODO_test-coverage.md", root / "coverage.xml", root / "lcov.info", root / "jacoco.xml"]
    selected = next((path for path in candidates if path.is_file()), None)
    if selected is None:
        result = CoverageSummary(None, None, None, [], [], None, "NOT_RUN", [])
    else:
        if selected.name == "TODO_test-coverage.md":
            files = parse_todo_coverage(selected)
        elif selected.suffix.lower() == ".info":
            files = parse_lcov(selected)
        elif selected.name == "jacoco.xml":
            files = []
        else:
            files = parse_coverage_xml(selected)
        result = CoverageSummary(
            files[0].source_file if len(files) == 1 else None,
            files[0].line_coverage if len(files) == 1 else None,
            files[0].branch_coverage if len(files) == 1 else None,
            files[0].covered_lines if len(files) == 1 else [],
            files[0].uncovered_lines if len(files) == 1 else [],
            str(selected),
            "PASS" if files else "NOT_RUN",
            files,
        )
    if store is not None:
        store.record_coverage_summary(result)
    return result
