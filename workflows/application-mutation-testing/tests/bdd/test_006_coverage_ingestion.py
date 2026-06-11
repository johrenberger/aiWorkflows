from __future__ import annotations

from pathlib import Path

from mutationctl.coverage.ingest import ingest_coverage
from mutationctl.state.store import StateStore


def test_given_todo_coverage_and_xml_when_ingested_then_todo_coverage_is_preferred(tmp_path: Path) -> None:
    (tmp_path / "TODO_test-coverage.md").write_text(
        "| Source File | Line Coverage |\n| --- | ---: |\n| src/app.py | 91% |\n",
        encoding="utf-8",
    )
    (tmp_path / "coverage.xml").write_text(
        '<coverage><class filename="src/app.py" line-rate="0.20"/></coverage>',
        encoding="utf-8",
    )
    result = ingest_coverage(tmp_path)
    assert result.evidence_path.endswith("TODO_test-coverage.md")
    assert result.files[0].line_coverage == 91.0


def test_given_coverage_xml_when_ingested_then_file_level_coverage_is_extracted(project_root: Path) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "coverage" / "coverage.xml"
    result = ingest_coverage(project_root, coverage_path=report)
    assert result.files[0].source_file == "src/sample.py"
    assert result.files[0].line_coverage == 85.0
    assert result.files[0].uncovered_lines == [5]


def test_given_lcov_when_ingested_then_file_level_coverage_is_extracted(project_root: Path) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "coverage" / "lcov.info"
    result = ingest_coverage(project_root, coverage_path=report)
    assert result.files[0].source_file == "src/math.js"
    assert result.files[0].line_coverage == 50.0


def test_given_no_coverage_artifacts_when_ingested_then_missing_coverage_is_explicit(tmp_path: Path) -> None:
    result = ingest_coverage(tmp_path)
    assert result.status == "NOT_RUN"
    assert result.files == []


def test_given_coverage_when_store_supplied_then_file_summaries_are_persisted(
    project_root: Path, tmp_path: Path
) -> None:
    report = project_root / "tests" / "fixtures" / "reports" / "coverage" / "coverage.xml"
    store = StateStore(tmp_path)
    store.initialize()
    ingest_coverage(project_root, coverage_path=report, store=store)
    persisted = store.get_latest_coverage_summary()
    assert persisted is not None
    assert len(persisted.files) == 2
