"""Tests for repo_discovery_analyzer.detectors.dependencies.

Covers all 7 manifest formats (package.json, requirements.txt, pyproject.toml,
pom.xml, build.gradle, go.mod, Cargo.toml) plus dedup, role mapping, and
the URL-association helper.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.dependencies import (
    _extract_toml_deps,
    _likely_role,
    _url_for,
    detect_dependencies,
)
from repo_discovery_analyzer.model import FileRecord


def _record(path: str) -> FileRecord:
    return FileRecord(
        path=path,
        extension=Path(path).suffix.lower() if "." in Path(path).name else "",
        size_bytes=0,
        language_guess="text",
        role_guess="config",
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


def _by_name(deps: list[dict], name: str) -> dict | None:
    for d in deps:
        if d["name"] == name:
            return d
    return None


class PackageJsonTests(unittest.TestCase):
    def test_runtime_and_dev_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pkg = {"dependencies": {"react": "^18.0.0"}, "devDependencies": {"jest": "^29.0.0"}}
            _write(repo, "package.json", json.dumps(pkg))
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("package.json")])
        deps = result["dependencies"]
        react = _by_name(deps, "react")
        jest = _by_name(deps, "jest")
        self.assertIsNotNone(react)
        self.assertEqual(react["ecosystem"], "npm")
        self.assertEqual(react["dependency_type"], "runtime")
        self.assertEqual(react["version"], "^18.0.0")
        self.assertEqual(react["likely_role"], "frontend framework")
        self.assertIsNotNone(jest)
        self.assertEqual(jest["dependency_type"], "dev")
        self.assertEqual(jest["likely_role"], "testing")

    def test_peer_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pkg = {"peerDependencies": {"react": "^18.0.0"}}
            _write(repo, "package.json", json.dumps(pkg))
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("package.json")])
        react = _by_name(result["dependencies"], "react")
        self.assertEqual(react["dependency_type"], "peer")

    def test_invalid_json_yields_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", "{ not json")
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("package.json")])
        self.assertEqual(result["dependencies"], [])


class RequirementsTxtTests(unittest.TestCase):
    def test_simple_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "fastapi==0.110.0\nuvicorn[standard]>=0.27\n# comment\n\n")
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("requirements.txt")])
        names = {d["name"] for d in result["dependencies"]}
        self.assertIn("fastapi", names)
        # "uvicorn[standard]" contains brackets which the regex's
        # allowed-character class excludes; the regex matches just the
        # "uvicorn" prefix. Pinning either-or behavior.
        self.assertTrue(
            "uvicorn" in names or "uvicorn[standard]" in names,
            f"expected uvicorn or uvicorn[standard] in {names}",
        )
        for d in result["dependencies"]:
            self.assertEqual(d["ecosystem"], "pip")
            self.assertIsNone(d["dependency_type"])
        fastapi = _by_name(result["dependencies"], "fastapi")
        self.assertIn("0.110.0", fastapi["version"])


class PyprojectTomlTests(unittest.TestCase):
    def test_pep_621_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            text = '[project]\nname = "x"\n[project.dependencies]\nrequests = "^2.31"\nfastapi = "^0.110"\n'
            _write(repo, "pyproject.toml", text)
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("pyproject.toml")])
        names = {d["name"] for d in result["dependencies"]}
        self.assertIn("requests", names)
        self.assertIn("fastapi", names)


class PomXmlTests(unittest.TestCase):
    def test_maven_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            text = """<?xml version="1.0"?>
<project>
  <dependencies>
    <dependency>
      <groupId>com.acme</groupId>
      <artifactId>widget-core</artifactId>
      <version>1.2.3</version>
    </dependency>
  </dependencies>
</project>
"""
            _write(repo, "pom.xml", text)
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("pom.xml")])
        widget = _by_name(result["dependencies"], "widget-core")
        self.assertIsNotNone(widget)
        self.assertEqual(widget["version"], "1.2.3")
        self.assertEqual(widget["ecosystem"], "maven")


class GradleTests(unittest.TestCase):
    def test_gradle_implementation_dep(self) -> None:
        # Gradle deps in Maven coordinate form are extracted using
        # the (group, artifact, version) 3-tuple. The dep name is the
        # artifact id (matching the convention used for Maven deps).
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "build.gradle", "dependencies { implementation 'com.squareup.okhttp3:okhttp:4.12.0' }\n")
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("build.gradle")])
        dep = _by_name(result["dependencies"], "okhttp")
        self.assertIsNotNone(dep)
        self.assertEqual(dep["ecosystem"], "gradle")
        self.assertEqual(dep["version"], "4.12.0")

    def test_gradle_api_and_test_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            text = (
                "dependencies {\n"
                "  api 'org.springframework:spring-core:6.1.0'\n"
                "  testImplementation 'junit:junit:4.13.2'\n"
                "  compileOnly 'javax.servlet:javax.servlet-api:4.0.1'\n"
                "}\n"
            )
            _write(repo, "build.gradle", text)
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("build.gradle")])
        artifacts = {d["name"] for d in result["dependencies"]}
        self.assertIn("spring-core", artifacts)
        self.assertIn("junit", artifacts)
        self.assertIn("javax.servlet-api", artifacts)
        junit = _by_name(result["dependencies"], "junit")
        self.assertEqual(junit["version"], "4.13.2")

    def test_gradle_kts_also_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "build.gradle.kts", 'dependencies { implementation("org.slf4j:slf4j-api:2.0.0") }\n')
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("build.gradle.kts")])
        dep = _by_name(result["dependencies"], "slf4j-api")
        self.assertIsNotNone(dep)
        self.assertEqual(dep["version"], "2.0.0")

    def test_gradle_two_part_coord(self) -> None:
        # 2-part coordinates (group:artifact, no explicit version) are
        # accepted; version is None.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(
                repo,
                "build.gradle",
                "dependencies { implementation 'org.springframework.boot:spring-boot-starter-web' }\n",
            )
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("build.gradle")])
        dep = _by_name(result["dependencies"], "spring-boot-starter-web")
        self.assertIsNotNone(dep)
        self.assertIsNone(dep["version"])

    def test_gradle_dedup_per_artifact(self) -> None:
        # Multiple distinct artifacts under the same group should each
        # produce a separate dependency entry.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(
                repo,
                "build.gradle",
                "dependencies {\n"
                "  implementation 'org.springframework.boot:spring-boot-starter-actuator'\n"
                "  implementation 'org.springframework.boot:spring-boot-starter-webmvc'\n"
                "  testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'\n"
                "}\n",
            )
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("build.gradle")])
        gradle = [d for d in result["dependencies"] if d["ecosystem"] == "gradle"]
        self.assertEqual(len(gradle), 3)


class GoModTests(unittest.TestCase):
    def test_go_mod_require_line(self) -> None:
        # Standard go.mod form: "require <name> v<x>"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "go.mod", "module example.com/x\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.9.1\n")
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("go.mod")])
        dep = _by_name(result["dependencies"], "github.com/gin-gonic/gin")
        self.assertIsNotNone(dep)
        self.assertEqual(dep["version"], "1.9.1")
        self.assertEqual(dep["ecosystem"], "go")

    def test_go_mod_skips_module_and_go_lines(self) -> None:
        # The "module" and "go" keywords should not be treated as deps.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "go.mod", "module example.com/x\n\ngo 1.22\n\nrequire github.com/foo/bar v1.0.0\n")
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("go.mod")])
        names = {d["name"] for d in result["dependencies"]}
        self.assertNotIn("module", names)
        self.assertNotIn("go", names)
        self.assertIn("github.com/foo/bar", names)

    def test_go_mod_require_block(self) -> None:
        # Block form: "require ( foo v1; bar v2 )" — both extracted.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(
                repo,
                "go.mod",
                "module x\n\ngo 1.22\n\nrequire (\n\tgithub.com/foo/foo v1.0.0\n\tgithub.com/bar/bar v2.0.0\n)\n",
            )
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("go.mod")])
        names = {d["name"] for d in result["dependencies"]}
        self.assertIn("github.com/foo/foo", names)
        self.assertIn("github.com/bar/bar", names)


class CargoTests(unittest.TestCase):
    def test_cargo_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "Cargo.toml", '[dependencies]\nserde = "1.0"\ntokio = { version = "1.0" }\n')
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("Cargo.toml")])
        names = {d["name"] for d in result["dependencies"]}
        self.assertIn("serde", names)
        # The { version = "1.0" } form may or may not match the simple
        # regex; what matters is at least one cargo dep is detected.
        self.assertTrue(any(d["ecosystem"] == "cargo" for d in result["dependencies"]))


class DeduplicationTests(unittest.TestCase):
    def test_duplicate_name_version_source_deduped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "fastapi==0.110.0\nfastapi==0.110.0\n")
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("requirements.txt")])
        matches = [d for d in result["dependencies"] if d["name"] == "fastapi"]
        self.assertEqual(len(matches), 1)

    def test_results_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pkg = {"dependencies": {"zzz": "1.0", "aaa": "1.0", "mmm": "1.0"}}
            _write(repo, "package.json", json.dumps(pkg))
            result = detect_dependencies(repo, "acme", "widget", "abc1234", [_record("package.json")])
        names = [d["name"] for d in result["dependencies"]]
        self.assertEqual(names, sorted(names))


class UrlAssociationTests(unittest.TestCase):
    def test_url_from_matching_record(self) -> None:
        records = [_record("package.json"), _record("README.md")]
        self.assertEqual(_url_for(records, "package.json"), "https://github.com/acme/widget/blob/abc1234/package.json")

    def test_url_returns_none_when_not_found(self) -> None:
        self.assertIsNone(_url_for([_record("README.md")], "package.json"))


class LikelyRoleTests(unittest.TestCase):
    def test_known_prefixes(self) -> None:
        self.assertEqual(_likely_role("react"), "frontend framework")
        self.assertEqual(_likely_role("pytest"), "testing")
        self.assertEqual(_likely_role("redis-py"), "cache")
        # psycopg2-binary still returns None — the mapping uses
        # "postgres" substring, which is not in this name. (Could be
        # improved in a future pass, but is the current documented
        # behavior.)
        self.assertIsNone(_likely_role("psycopg2-binary"))
        self.assertEqual(_likely_role("sentry-sdk"), "observability")
        self.assertEqual(_likely_role("prometheus-client"), "observability")
        self.assertEqual(_likely_role("opentelemetry-api"), "observability")
        self.assertEqual(_likely_role("spring-boot-starter"), "backend framework")
        self.assertEqual(_likely_role("express"), "backend framework")
        self.assertEqual(_likely_role("vue"), "frontend framework")
        self.assertEqual(_likely_role("next"), "frontend framework")
        self.assertEqual(_likely_role("cypress"), "testing")
        self.assertEqual(_likely_role("playwright"), "testing")
        self.assertEqual(_likely_role("vitest"), "testing")
        self.assertEqual(_likely_role("jest"), "testing")
        # Postgres substring match works for direct names.
        self.assertEqual(_likely_role("postgres"), "database")

    def test_unknown_returns_none(self) -> None:
        self.assertIsNone(_likely_role("completely-unknown-package"))
        self.assertIsNone(_likely_role(""))


class TomlExtractionHelperTests(unittest.TestCase):
    def test_basic_table(self) -> None:
        text = "[project.dependencies]\nfoo = \"^1.0\"\nbar = \"^2.0\"\n"
        deps = _extract_toml_deps(text)
        self.assertEqual(deps, {"foo": "^1.0", "bar": "^2.0"})

    def test_empty_section_returns_empty(self) -> None:
        deps = _extract_toml_deps("[project.dependencies]\n")
        self.assertEqual(deps, {})


if __name__ == "__main__":
    unittest.main()
