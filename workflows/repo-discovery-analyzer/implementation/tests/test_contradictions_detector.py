"""Tests for repo_discovery_analyzer.detectors.contradictions.

The contradictions detector looks for mismatches between different evidence
sources (README, package-lock files, routes vs. docs, tests vs. CI, port
configuration). Tests below cover each contradiction branch and the helper
functions.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.contradictions import (
    _api_docs_present,
    _app_ports,
    _ci_runs_tests,
    _docs_mentions,
    detect_contradictions,
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


def _by_summary(findings: list[dict], needle: str) -> dict | None:
    for f in findings:
        if needle in f["summary"]:
            return f
    return None


class DocsMentionContradictionTests(unittest.TestCase):
    def test_readme_mentions_postgres_but_no_pg_in_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "README.md", "This project uses Postgres and Django.\n")
            records = [_record("README.md")]
            stack = {"technologies": [{"technology": "Django"}]}
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, stack, {"routes": []}, {"testing": []}, {"build_deploy": []})
        c = _by_summary(result["contradiction_candidates"], "README mentions a database not found")
        self.assertIsNotNone(c)
        self.assertTrue(c["needs_ai_interpretation"])

    def test_readme_mentions_postgres_and_pg_in_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "README.md", "This project uses Postgres.\n")
            records = [_record("README.md")]
            stack = {"technologies": [{"technology": "Postgres"}]}
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, stack, {"routes": []}, {"testing": []}, {"build_deploy": []})
        self.assertIsNone(_by_summary(result["contradiction_candidates"], "README mentions a database not found"))

    def test_no_readme_no_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_contradictions(Path(tmp), "acme", "widget", "abc1234", [], {"technologies": []}, {"routes": []}, {"testing": []}, {"build_deploy": []})
        self.assertEqual(result["contradiction_candidates"], [])


class PackageManagerMismatchTests(unittest.TestCase):
    def test_multiple_lockfiles_detected(self) -> None:
        records = [_record("package-lock.json"), _record("yarn.lock"), _record("pnpm-lock.yaml")]
        result = detect_contradictions(Path("/nonexistent"), "acme", "widget", "abc1234", records, {"technologies": []}, {"routes": []}, {"testing": []}, {"build_deploy": []})
        c = _by_summary(result["contradiction_candidates"], "package manager mismatch")
        self.assertIsNotNone(c)
        self.assertFalse(c["needs_ai_interpretation"])

    def test_single_lockfile_no_finding(self) -> None:
        records = [_record("package-lock.json")]
        result = detect_contradictions(Path("/nonexistent"), "acme", "widget", "abc1234", records, {"technologies": []}, {"routes": []}, {"testing": []}, {"build_deploy": []})
        self.assertIsNone(_by_summary(result["contradiction_candidates"], "package manager mismatch"))


class RoutesButNoApiDocsTests(unittest.TestCase):
    def test_routes_without_api_docs(self) -> None:
        routes = {"routes": [{"method": "GET", "path": "/x"}]}
        records = [_record("server.js")]
        result = detect_contradictions(Path("/nonexistent"), "acme", "widget", "abc1234", records, {"technologies": []}, routes, {"testing": []}, {"build_deploy": []})
        c = _by_summary(result["contradiction_candidates"], "routes exist but no API documentation")
        self.assertIsNotNone(c)
        self.assertTrue(c["needs_ai_interpretation"])

    def test_routes_with_openapi_yaml(self) -> None:
        routes = {"routes": [{"method": "GET", "path": "/x"}]}
        records = [_record("openapi.yaml"), _record("server.js")]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "openapi.yaml").write_text("openapi: 3.0.0\n", encoding="utf-8")
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, {"technologies": []}, routes, {"testing": []}, {"build_deploy": []})
        self.assertIsNone(_by_summary(result["contradiction_candidates"], "routes exist but no API documentation"))

    def test_routes_with_swagger_json(self) -> None:
        routes = {"routes": [{"method": "GET", "path": "/x"}]}
        records = [_record("swagger.json"), _record("server.js")]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "swagger.json").write_text("{}", encoding="utf-8")
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, {"technologies": []}, routes, {"testing": []}, {"build_deploy": []})
        self.assertIsNone(_by_summary(result["contradiction_candidates"], "routes exist but no API documentation"))


class TestsWithoutCITestsTests(unittest.TestCase):
    def test_tests_without_ci(self) -> None:
        tests = {"testing": [{"type": "test-surface", "framework_tool": "pytest"}]}
        records = [_record("tests/test_x.py", role="test"), _record("README.md")]
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_contradictions(Path(tmp), "acme", "widget", "abc1234", records, {"technologies": []}, {"routes": []}, tests, {"build_deploy": []})
        c = _by_summary(result["contradiction_candidates"], "tests exist but CI does not appear to run them")
        self.assertIsNotNone(c)

    def test_tests_with_ci_workflow(self) -> None:
        tests = {"testing": [{"type": "test-surface", "framework_tool": "pytest"}]}
        records = [_record("tests/test_x.py", role="test"), _record(".github/workflows/ci.yml")]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tests").mkdir(parents=True)
            (repo / "tests" / "test_x.py").write_text("def test_x(): assert True\n", encoding="utf-8")
            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    steps:\n      - run: pytest\n", encoding="utf-8")
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, {"technologies": []}, {"routes": []}, tests, {"build_deploy": []})
        self.assertIsNone(_by_summary(result["contradiction_candidates"], "tests exist but CI does not appear to run them"))


class PortMismatchTests(unittest.TestCase):
    def test_docker_port_differs_from_app_port(self) -> None:
        # The detector compares docker ports (from build_deploy input) to
        # "app ports" (re-parsed from any dockerfile/containerfile in the
        # records). For the contradiction to fire, the build_deploy input
        # must disagree with what the dockerfiles actually say.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Dockerfile").write_text("FROM node:22\nEXPOSE 3000\n", encoding="utf-8")
            (repo / "Containerfile").write_text("FROM node:22\nEXPOSE 3000\n", encoding="utf-8")
            records = [_record("Dockerfile"), _record("Containerfile")]
            # build_deploy says 8080; the dockerfiles say 3000 → mismatch.
            build_deploy = {"build_deploy": [
                {"artifact_type": "Dockerfile", "path": "Dockerfile", "commands_or_ports": [8080]},
                {"artifact_type": "Dockerfile", "path": "Containerfile", "commands_or_ports": [8080]},
            ]}
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, {"technologies": []}, {"routes": []}, {"testing": []}, build_deploy)
        c = _by_summary(result["contradiction_candidates"], "Docker exposed port differs")
        self.assertIsNotNone(c)

    def test_docker_port_matches_app_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Dockerfile").write_text("FROM node:22\nEXPOSE 3000\n", encoding="utf-8")
            records = [_record("Dockerfile")]
            build_deploy = {"build_deploy": [
                {"artifact_type": "Dockerfile", "path": "Dockerfile", "commands_or_ports": [3000]},
            ]}
            result = detect_contradictions(repo, "acme", "widget", "abc1234", records, {"technologies": []}, {"routes": []}, {"testing": []}, build_deploy)
        self.assertIsNone(_by_summary(result["contradiction_candidates"], "Docker exposed port differs"))


class HelperTests(unittest.TestCase):
    def test_docs_mentions_joins_readme_texts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "README.md").write_text("Postgres is the database.\n", encoding="utf-8")
            (repo / "README.zh.md").write_text("Mongodb is also used.\n", encoding="utf-8")
            records = [_record("README.md"), _record("README.zh.md")]
            text = _docs_mentions(repo, records)
        self.assertIn("postgres", text)
        self.assertIn("mongodb", text)

    def test_docs_mentions_skips_non_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "LICENSE").write_text("Postgres mentioned here.\n", encoding="utf-8")
            records = [_record("LICENSE")]
            text = _docs_mentions(repo, records)
        self.assertEqual(text, "")

    def test_api_docs_present_match(self) -> None:
        records = [_record("docs/openapi.yaml"), _record("api/swagger.json"), _record("apidoc.md")]
        self.assertTrue(_api_docs_present(records))

    def test_api_docs_present_no_match(self) -> None:
        records = [_record("docs/index.html"), _record("README.md")]
        self.assertFalse(_api_docs_present(records))

    def test_ci_runs_tests_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".github/workflows/ci.yml").parent.mkdir(parents=True)
            (repo / ".github/workflows/ci.yml").write_text("steps:\n  - run: pytest\n", encoding="utf-8")
            records = [_record(".github/workflows/ci.yml")]
            self.assertTrue(_ci_runs_tests(repo, records))

    def test_ci_runs_tests_no_test_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".github/workflows/lint.yml").parent.mkdir(parents=True)
            (repo / ".github/workflows/lint.yml").write_text("steps:\n  - run: eslint\n", encoding="utf-8")
            records = [_record(".github/workflows/lint.yml")]
            self.assertFalse(_ci_runs_tests(repo, records))

    def test_app_ports_parses_dockerfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Dockerfile").write_text("FROM node:22\nEXPOSE 3000 8080\n", encoding="utf-8")
            records = [_record("Dockerfile")]
            self.assertEqual(_app_ports(repo, records), [3000, 8080])

    def test_app_ports_ignores_non_dockerfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir(parents=True)
            (repo / "src" / "app.py").write_text("EXPOSE 9999\n", encoding="utf-8")
            records = [_record("src/app.py")]
            self.assertEqual(_app_ports(repo, records), [])


if __name__ == "__main__":
    unittest.main()
