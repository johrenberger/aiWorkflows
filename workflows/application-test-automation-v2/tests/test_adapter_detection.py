from __future__ import annotations

from pathlib import Path

from test_factory.adapters.java_junit import JavaJUnitAdapter
from test_factory.adapters.js_jest_vitest import JsJestVitestAdapter
from test_factory.adapters.python_pytest import PythonPytestAdapter


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-repo"


def test_adapter_detection_uses_fixture_signals():
    java = JavaJUnitAdapter().detect(FIXTURE)
    javascript = JsJestVitestAdapter().detect(FIXTURE)
    python = PythonPytestAdapter().detect(FIXTURE)
    assert java.confidence > 0
    assert "pom.xml" in java.evidence
    assert javascript.confidence > 0
    assert "package.json" in javascript.evidence
    assert python.confidence > 0
    assert "pyproject.toml" in python.evidence


def test_adapter_commands_match_fixture_tooling():
    assert JavaJUnitAdapter().discover_test_command(FIXTURE, "com/example").render() == "mvn test"
    assert JavaJUnitAdapter().discover_coverage_command(FIXTURE, "com/example").render() == "mvn test jacoco:report"
    assert JsJestVitestAdapter().discover_test_command(FIXTURE, "src").render() == "npm test"
    assert JsJestVitestAdapter().discover_coverage_command(FIXTURE, "src").render() == "npm run test:coverage"
    # Python pytest now uses `python -m pytest` so the command resolves to the
    # current interpreter's pytest, not a globally-installed pytest script in
    # a different venv. (Bug fix in PR #22; this test was updated to match.)
    import sys
    expected_pytest = f"{sys.executable} -m pytest"
    assert PythonPytestAdapter().discover_test_command(FIXTURE, "package").render() == expected_pytest
    assert PythonPytestAdapter().discover_coverage_command(FIXTURE, "package").render() == f"{expected_pytest} --cov --cov-report=json:coverage.json --cov-report=xml:coverage.xml"
