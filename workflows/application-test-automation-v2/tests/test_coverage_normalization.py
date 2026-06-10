from __future__ import annotations

from pathlib import Path

from test_factory.analyzers.coverage_normalizer import (
    parse_coverage_final_json,
    parse_jacoco_xml,
    parse_lcov_info,
    parse_python_coverage_xml,
)


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-repo"


def test_jacoco_xml_normalization():
    records = parse_jacoco_xml(FIXTURE / "target" / "site" / "jacoco" / "jacoco.xml")
    assert records[0].path == "com/example/Foo.java"
    assert records[0].line_coverage == 50.0


def test_js_coverage_normalization():
    final = parse_coverage_final_json(FIXTURE / "coverage" / "coverage-final.json")
    lcov = parse_lcov_info(FIXTURE / "coverage" / "lcov.info")
    assert final[0].line_coverage == 50.0
    assert lcov[0].branch_coverage == 50.0


def test_python_coverage_normalization():
    records = parse_python_coverage_xml(FIXTURE / "coverage.xml")
    assert records[0].path == "package/foo.py"
    assert records[0].line_coverage == 50.0
