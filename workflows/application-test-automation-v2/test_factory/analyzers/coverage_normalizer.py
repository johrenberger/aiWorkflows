from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ..models import CoverageRecord


def _pct(covered: int, total: int) -> float:
    return round((covered / total) * 100, 2) if total else 0.0


def parse_jacoco_xml(report_path: str | Path) -> list[CoverageRecord]:
    root = ET.parse(report_path).getroot()
    records: list[CoverageRecord] = []
    for pkg in root.findall(".//package"):
        pkg_name = pkg.get("name", "")
        for src in pkg.findall("sourcefile"):
            file_name = src.get("name", "")
            path = f"{pkg_name}/{file_name}" if pkg_name else file_name
            total_lines = 0
            covered_lines = 0
            uncovered_lines: list[int] = []
            branch_total = 0
            branch_covered = 0
            uncovered_branches: list[str] = []
            for line in src.findall("line"):
                total_lines += 1
                nr = int(line.get("nr", "0"))
                ci = int(line.get("ci", "0"))
                mb = int(line.get("mb", "0"))
                cb = int(line.get("cb", "0"))
                if ci > 0:
                    covered_lines += 1
                else:
                    uncovered_lines.append(nr)
                branch_total += mb + cb
                branch_covered += cb
                if mb > 0:
                    uncovered_branches.append(f"{nr}:{mb}")
            branch_pct = _pct(branch_covered, branch_total) if branch_total else None
            records.append(CoverageRecord(path=path, line_coverage=_pct(covered_lines, total_lines), branch_coverage=branch_pct, uncovered_lines=uncovered_lines, uncovered_branches=uncovered_branches, report_ref=str(report_path)))
    return records


def parse_python_coverage_xml(report_path: str | Path) -> list[CoverageRecord]:
    root = ET.parse(report_path).getroot()
    records: list[CoverageRecord] = []
    for cls in root.findall(".//class"):
        path = cls.get("filename", "")
        total_lines = 0
        covered_lines = 0
        uncovered_lines: list[int] = []
        branch_total = 0
        branch_covered = 0
        uncovered_branches: list[str] = []
        for line in cls.findall("./lines/line"):
            total_lines += 1
            nr = int(line.get("number", "0"))
            hits = int(line.get("hits", "0"))
            if hits > 0:
                covered_lines += 1
            else:
                uncovered_lines.append(nr)
            if line.get("branch", "false") == "true":
                cond = line.get("condition-coverage", "")
                if "/" in cond:
                    try:
                        taken = cond.split("(")[-1].split(")")[0]
                        hit, total = taken.split("/")
                        hit_i, total_i = int(hit), int(total)
                        branch_total += total_i
                        branch_covered += hit_i
                        if hit_i < total_i:
                            uncovered_branches.append(f"{nr}:{total_i-hit_i}")
                    except Exception:
                        pass
        branch_pct = _pct(branch_covered, branch_total) if branch_total else None
        records.append(CoverageRecord(path=path, line_coverage=_pct(covered_lines, total_lines), branch_coverage=branch_pct, uncovered_lines=uncovered_lines, uncovered_branches=uncovered_branches, report_ref=str(report_path)))
    return records


def parse_lcov_info(report_path: str | Path) -> list[CoverageRecord]:
    records: list[CoverageRecord] = []
    current: dict[str, object] = {}
    uncovered_lines: list[int] = []
    uncovered_branches: list[str] = []
    line_total = line_covered = 0
    branch_total = branch_covered = 0
    def flush() -> None:
        nonlocal current, uncovered_lines, uncovered_branches, line_total, line_covered, branch_total, branch_covered
        if not current.get("path"):
            return
        branch_pct = _pct(branch_covered, branch_total) if branch_total else None
        records.append(CoverageRecord(path=str(current["path"]), line_coverage=_pct(line_covered, line_total), branch_coverage=branch_pct, uncovered_lines=list(uncovered_lines), uncovered_branches=list(uncovered_branches), report_ref=str(report_path)))
        current = {}
        uncovered_lines = []
        uncovered_branches = []
        line_total = line_covered = 0
        branch_total = branch_covered = 0
    for raw in Path(report_path).read_text(encoding="utf-8", errors="ignore").splitlines():
        if raw.startswith("SF:"):
            flush()
            current["path"] = raw[3:].strip()
        elif raw.startswith("DA:"):
            line_total += 1
            line_no, hits = raw[3:].split(",", 1)
            if int(hits) > 0:
                line_covered += 1
            else:
                uncovered_lines.append(int(line_no))
        elif raw.startswith("BRDA:"):
            branch_total += 1
            line_no, block, branch, taken = raw[5:].split(",")
            if taken != "-" and int(taken) > 0:
                branch_covered += 1
            else:
                uncovered_branches.append(f"{line_no}:{block}:{branch}")
        elif raw == "end_of_record":
            flush()
    flush()
    return records


def parse_coverage_final_json(report_path: str | Path) -> list[CoverageRecord]:
    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    records: list[CoverageRecord] = []
    for path, payload in data.items():
        statements = payload.get("s", {})
        statement_map = payload.get("statementMap", {})
        branches = payload.get("b", {})
        branch_map = payload.get("branchMap", {})
        total_lines = len(statements)
        covered_lines = sum(1 for value in statements.values() if value > 0)
        uncovered_lines = [
            int(statement_map[key]["start"]["line"])
            for key, value in statements.items()
            if value <= 0 and key in statement_map and "start" in statement_map[key]
        ]
        branch_total = sum(len(value) for value in branches.values())
        branch_covered = sum(sum(1 for hit in value if hit > 0) for value in branches.values())
        uncovered_branches: list[str] = []
        for key, hits in branches.items():
            if key not in branch_map:
                continue
            loc = branch_map[key].get("loc", {}).get("start", {}).get("line", 0)
            for idx, hit in enumerate(hits):
                if hit <= 0:
                    uncovered_branches.append(f"{loc}:{idx}")
        branch_pct = _pct(branch_covered, branch_total) if branch_total else None
        records.append(CoverageRecord(path=path, line_coverage=_pct(covered_lines, total_lines), branch_coverage=branch_pct, uncovered_lines=uncovered_lines, uncovered_branches=uncovered_branches, report_ref=str(report_path)))
    return records


def parse_coverage_py_json(report_path: str | Path) -> list[CoverageRecord]:
    """Parse a `coverage.json` file produced by `coverage json` (the coverage.py
    tool, not istanbul/nyc). The schema is:

        {
          "meta": {"version": "...", "timestamp": "...", ...},
          "files": {
            "path/to/file.py": {
              "executed_lines": [1, 2, 5, ...],
              "missing_lines":  [3, 4, ...],
              "excluded_lines": [],
              "summary": {"covered_lines": N, "num_statements": M, "percent_covered": P, ...}
            }
          },
          "totals": {...}
        }

    Bug surfaced 2026-06-10 on v2's self-coverage run: the orchestrator was
    routing coverage.json to parse_coverage_final_json (the istanbul parser),
    which produced 0%-coverage records for every file because the schemas
    differ. See PR #22.
    """
    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    files = data.get("files", {})
    if not isinstance(files, dict):
        return []
    records: list[CoverageRecord] = []
    for path, payload in files.items():
        if not isinstance(payload, dict):
            continue
        summary = payload.get("summary", {}) or {}
        # Prefer summary.percent_covered; fall back to computing from lists.
        if "percent_covered" in summary:
            line_pct = float(summary["percent_covered"])
        else:
            executed = payload.get("executed_lines") or []
            missing = payload.get("missing_lines") or []
            total = len(executed) + len(missing)
            line_pct = _pct(len(executed), total) if total else 0.0
        branch_pct_val = summary.get("percent_covered_branches")
        branch_pct = float(branch_pct_val) if branch_pct_val is not None else None
        missing_lines = payload.get("missing_lines") or []
        records.append(
            CoverageRecord(
                path=path,
                line_coverage=line_pct,
                branch_coverage=branch_pct,
                uncovered_lines=[int(n) for n in missing_lines if isinstance(n, (int, float))],
                uncovered_branches=[],
                report_ref=str(report_path),
            )
        )
    return records
