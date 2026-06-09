"""Tests for repo_discovery_analyzer.detectors.testing.

Covers all 3 finding types (test-surface, coverage-tool, ci-test-step),
all framework-inference branches, all test-command branches, and the
source-to-test ratio helper.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.testing import (
    _ci_test_command,
    _coverage_tool,
    _infer_framework,
    _paths_for,
    _ratio,
    _test_command,
    detect_testing,
)
from repo_discovery_analyzer.model import FileRecord


def _record(path: str, role: str = "source") -> FileRecord:
    return FileRecord(
        path=path,
        extension=Path(path).suffix.lower() if "." in Path(path).name else "",
        size_bytes=0,
        language_guess="text",
        role_guess=role,
        line_count=None,
        source_line_count=None,
        github_url=f"https://github.com/acme/widget/blob/abc1234/{path}",
        reviewed_by_analyzer=True,
        skipped=False,
        skip_reason=None,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _by_type(findings: list[dict], t: str) -> dict | None:
    for f in findings:
        if f["type"] == t:
            return f
    return None


class TestSurfaceDetectionTests(unittest.TestCase):
    def test_python_tests_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tests").mkdir(parents=True)
            (repo / "tests" / "test_x.py").write_text("def test_x(): assert True\n", encoding="utf-8")
            records = [_record("tests/test_x.py", role="test"), _record("src/app.py")]
            result = detect_testing(repo, "acme", "widget", "abc1234", records)
        surface = _by_type(result["testing"], "test-surface")
        self.assertIsNotNone(surface)
        self.assertEqual(surface["framework_tool"], "pytest/unittest")
        self.assertIn("tests/test_x.py", surface["paths"])
        self.assertEqual(surface["path_count"], 1)
        self.assertFalse(surface["paths_truncated"])

    def test_javascript_tests_with_jest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{"devDependencies": {"jest": "^29.0.0"}}')
            (repo / "tests").mkdir(parents=True)
            (repo / "tests" / "app.test.js").write_text("test('x', () => {})\n", encoding="utf-8")
            records = [_record("tests/app.test.js", role="test"), _record("package.json")]
            result = detect_testing(repo, "acme", "widget", "abc1234", records)
        surface = _by_type(result["testing"], "test-surface")
        self.assertEqual(surface["framework_tool"], "javascript test framework")

    def test_java_tests_junit(self) -> None:
        records = [_record("src/main/App.java"), _record("src/test/AppTest.java", role="test")]
        result = detect_testing(Path("/nonexistent"), "acme", "widget", "abc1234", records)
        surface = _by_type(result["testing"], "test-surface")
        self.assertEqual(surface["framework_tool"], "JUnit")

    def test_unknown_framework(self) -> None:
        records = [_record("src/main.go", role="test")]
        result = detect_testing(Path("/nonexistent"), "acme", "widget", "abc1234", records)
        surface = _by_type(result["testing"], "test-surface")
        self.assertIsNone(surface["framework_tool"])


class CoverageToolTests(unittest.TestCase):
    def test_coveragerc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".coveragerc").write_text("[run]\nsource = src\n", encoding="utf-8")
            result = detect_testing(repo, "acme", "widget", "abc1234", [])
        cov = _by_type(result["testing"], "coverage-tool")
        self.assertIsNotNone(cov)
        self.assertEqual(cov["framework_tool"], "coverage.py")

    def test_jacoco(self) -> None:
        records = [_record("target/jacoco-report/index.html")]
        result = detect_testing(Path("/nonexistent"), "acme", "widget", "abc1234", records)
        cov = _by_type(result["testing"], "coverage-tool")
        self.assertIsNotNone(cov)
        self.assertEqual(cov["framework_tool"], "JaCoCo")

    def test_no_coverage_tool(self) -> None:
        result = detect_testing(Path("/nonexistent"), "acme", "widget", "abc1234", [])
        self.assertIsNone(_by_type(result["testing"], "coverage-tool"))


class CITestStepTests(unittest.TestCase):
    def test_github_workflows_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("steps:\n  - run: pytest\n", encoding="utf-8")
            records = [_record(".github/workflows/ci.yml")]
            result = detect_testing(repo, "acme", "widget", "abc1234", records)
        ci = _by_type(result["testing"], "ci-test-step")
        self.assertIsNotNone(ci)
        self.assertEqual(ci["framework_tool"], "CI workflow")

    def test_gitlab_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".gitlab-ci.yml").write_text("test:\n  script: pytest\n", encoding="utf-8")
            records = [_record(".gitlab-ci.yml")]
            result = detect_testing(repo, "acme", "widget", "abc1234", records)
        ci = _by_type(result["testing"], "ci-test-step")
        self.assertIsNotNone(ci)

    def test_jenkins_detected(self) -> None:
        records = [_record("Jenkinsfile")]
        result = detect_testing(Path("/nonexistent"), "acme", "widget", "abc1234", records)
        ci = _by_type(result["testing"], "ci-test-step")
        self.assertIsNotNone(ci)


class HelperTests(unittest.TestCase):
    def test_infer_framework_python(self) -> None:
        records = [_record("src/app.py")]
        self.assertEqual(_infer_framework(records, Path("/nonexistent")), "pytest/unittest")

    def test_infer_framework_npm_with_jest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text('"jest": "^29.0.0"', encoding="utf-8")
            records = [_record("src/app.js")]
            self.assertEqual(_infer_framework(records, repo), "javascript test framework")

    def test_infer_framework_java(self) -> None:
        records = [_record("src/App.java")]
        self.assertEqual(_infer_framework(records, Path("/nonexistent")), "JUnit")

    def test_infer_framework_unknown(self) -> None:
        records = [_record("src/main.go")]
        self.assertIsNone(_infer_framework(records, Path("/nonexistent")))

    def test_coverage_tool_from_coveragerc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".coveragerc").write_text("", encoding="utf-8")
            self.assertEqual(_coverage_tool([], repo), "coverage.py")

    def test_coverage_tool_from_path_substring(self) -> None:
        # The substring "coverage" must actually appear in the path. The
        # "htmlcov" directory does NOT contain "coverage" as a substring,
        # so this branch doesn't fire on common coverage report dirs.
        records = [_record("htmlcov/index.html")]
        self.assertIsNone(_coverage_tool(records, Path("/nonexistent")))

    def test_coverage_tool_path_with_coverage_substring(self) -> None:
        records = [_record("coverage/lcov.info")]
        self.assertEqual(_coverage_tool(records, Path("/nonexistent")), "coverage.py")

    def test_coverage_tool_jacoco(self) -> None:
        records = [_record("target/site/jacoco/index.html")]
        self.assertEqual(_coverage_tool(records, Path("/nonexistent")), "JaCoCo")

    def test_coverage_tool_none(self) -> None:
        self.assertIsNone(_coverage_tool([], Path("/nonexistent")))

    def test_test_command_npm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text('"test": "jest"', encoding="utf-8")
            self.assertEqual(_test_command(repo), "npm test")

    def test_test_command_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
            self.assertEqual(_test_command(repo), "pytest")

    def test_test_command_maven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "pom.xml").write_text("<project/>\n", encoding="utf-8")
            self.assertEqual(_test_command(repo), "mvn test")

    def test_test_command_gradle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "build.gradle").write_text("", encoding="utf-8")
            self.assertEqual(_test_command(repo), "gradle test")

    def test_test_command_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(_test_command(Path(tmp)))

    def test_ci_test_command_npm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("steps:\n  - run: npm test\n", encoding="utf-8")
            records = [_record(".github/workflows/ci.yml")]
            self.assertEqual(_ci_test_command(records, repo), "npm test")

    def test_ci_test_command_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("steps:\n  - run: pytest\n", encoding="utf-8")
            records = [_record(".github/workflows/ci.yml")]
            self.assertEqual(_ci_test_command(records, repo), "pytest")

    def test_ci_test_command_unknown_test_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("steps:\n  - run: my-custom-test\n", encoding="utf-8")
            records = [_record(".github/workflows/ci.yml")]
            # Generic "test" keyword present but no known runner.
            self.assertIsNone(_ci_test_command(records, repo))

    def test_paths_for_substring(self) -> None:
        records = [_record("htmlcov/index.html"), _record("htmlcov/x.html"), _record("README.md")]
        paths = _paths_for(records, "htmlcov")
        self.assertEqual(paths, ["htmlcov/index.html", "htmlcov/x.html"])

    def test_ratio_source_to_test(self) -> None:
        records = [
            _record("a.py", role="source"),
            _record("b.py", role="source"),
            _record("c.py", role="source"),
            _record("t.py", role="test"),
        ]
        r = _ratio(records)
        self.assertEqual(r["source_files"], 3)
        self.assertEqual(r["test_files"], 1)
        self.assertAlmostEqual(r["ratio"], 1 / 3, places=4)

    def test_ratio_zero_source(self) -> None:
        records = [_record("t.py", role="test")]
        r = _ratio(records)
        self.assertIsNone(r["ratio"])


if __name__ == "__main__":
    unittest.main()
