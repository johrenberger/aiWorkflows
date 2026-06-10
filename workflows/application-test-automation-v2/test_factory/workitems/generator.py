from __future__ import annotations

import hashlib
from pathlib import Path

from ..models import Config, CoverageRecord, RiskScoreRecord, SourceTestMapRecord, WorkItemRecord


def _language_from_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".java": "java",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "javascript",
        ".tsx": "javascript",
        ".py": "python",
    }.get(suffix, suffix.lstrip(".") or "unknown")


def generate_work_items(
    repo_root: str | Path,
    config: Config,
    coverage_records: list[CoverageRecord],
    risk_scores: list[RiskScoreRecord],
    source_maps: dict[str, SourceTestMapRecord],
    existing_tests: dict[str, list[str]] | None = None,
) -> list[WorkItemRecord]:
    repo_root = Path(repo_root)
    existing_tests = existing_tests or {}
    coverage_by_path = {item.path: item for item in coverage_records}
    items: list[WorkItemRecord] = []
    for score in sorted(risk_scores, key=lambda item: (-item.risk_score * item.coverage_gap, item.path)):
        if score.coverage_gap <= 0 and score.risk_score <= 0:
            continue
        map_record = source_maps.get(score.path)
        if not map_record:
            map_record = SourceTestMapRecord(source_path=score.path)
        work_item_id = f"wi-{hashlib.sha1(f'{score.module}:{score.path}'.encode('utf-8')).hexdigest()[:10]}"
        coverage = coverage_by_path.get(score.path)
        candidate_tests = map_record.candidate_tests or existing_tests.get(score.path, [])
        item = WorkItemRecord(
            work_item_id=work_item_id,
            source_path=score.path,
            language=_language_from_path(score.path),
            module=score.module,
            current_line_coverage=coverage.line_coverage if coverage else score.line_coverage,
            current_branch_coverage=coverage.branch_coverage if coverage else score.branch_coverage,
            uncovered_lines=coverage.uncovered_lines if coverage else [],
            uncovered_branches=coverage.uncovered_branches if coverage else [],
            risk_score=score.risk_score,
            risk_factors={
                "complexity": score.complexity,
                "churn": score.churn,
                "public_api_exposure": score.public_api_exposure,
                "dependency_fan_in": score.dependency_fan_in,
                "defect_history": score.defect_history,
                "data_or_security_sensitivity": score.data_or_security_sensitivity,
                "coverage_gap": score.coverage_gap,
            },
            existing_test_files=candidate_tests,
            recommended_test_type=map_record.recommended_test_type,
            supporting_files=map_record.supporting_files[: config.max_supporting_files_per_work_item],
            conventions_summary=map_record.conventions_summary,
            validation_command="",
            acceptance_criteria=[
                "tests are added or updated without modifying production code",
                "observable behavior is asserted",
                "no skipped, todo, or only tests are introduced",
                "validation command passes",
            ],
            status="pending",
            priority=score.risk_score * score.coverage_gap,
            content_path=str(repo_root / "analysis-artifacts" / "ai_work_items" / f"{work_item_id}.md"),
        )
        items.append(item)
    return items
