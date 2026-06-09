from __future__ import annotations

from collections import Counter
from pathlib import Path

from .model import FileRecord


def compute_loc_metrics(records: list[FileRecord]) -> dict:
    total_files = len(records)
    total_lines = sum((r.line_count or 0) for r in records)
    by_language = Counter()
    for record in records:
        if record.source_line_count is not None:
            by_language[record.language_guess] += record.source_line_count
    largest_files = sorted(
        (
            {"path": r.path, "size_bytes": r.size_bytes, "line_count": r.line_count}
            for r in records
        ),
        key=lambda item: (-item["size_bytes"], item["path"]),
    )[:25]
    dir_sizes: dict[str, int] = {}
    for record in records:
        parent = str(Path(record.path).parent).replace("\\", "/")
        dir_sizes[parent] = dir_sizes.get(parent, 0) + (record.line_count or 0)
    largest_dirs = sorted(
        ({"path": path, "line_count": count} for path, count in dir_sizes.items()),
        key=lambda item: (-item["line_count"], item["path"]),
    )[:25]
    large_files = [r.path for r in records if r.line_count and r.line_count > 1000]
    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "lines_by_language": dict(sorted(by_language.items())),
        "largest_files": largest_files,
        "largest_directories": largest_dirs,
        "large_files_over_threshold": sorted(large_files),
        "source_to_test_ratio": _source_to_test_ratio(records),
    }


def _source_to_test_ratio(records: list[FileRecord]) -> dict:
    source = 0
    tests = 0
    for record in records:
        if record.role_guess == "test":
            tests += 1
        elif record.role_guess == "source":
            source += 1
    ratio = round(tests / source, 4) if source else None
    return {"source_files": source, "test_files": tests, "ratio": ratio}

