"""Tests for repo_discovery_analyzer.detectors.integrations.

Covers all 9 integration categories: Sentry, OpenTelemetry, Prometheus, AWS,
Azure, GCP, OAuth/OIDC/SAML, JWT/session, Docker. Plus helpers.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.integrations import (
    _has_docker,
    _paths_for_dep,
    _paths_for_security,
    _security_text,
    detect_integrations,
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


def _by_tech(integrations: list[dict], technology: str) -> dict | None:
    for i in integrations:
        if i["technology"] == technology:
            return i
    return None


def _dep(records: list[FileRecord], name: str) -> dict:
    return {
        "name": name,
        "version": "1.0",
        "ecosystem": "npm",
        "dependency_type": "runtime",
        "source_file": records[0].path if records else "package.json",
        "github_url": records[0].github_url if records else None,
        "likely_role": None,
    }


class ObservabilityTests(unittest.TestCase):
    def test_sentry_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{"dependencies": {"sentry-sdk": "1.0"}}')
            records = [_record("package.json")]
            dependencies = {"dependencies": [_dep(records, "sentry-sdk")]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        sentry = _by_tech(result["integrations"], "Sentry")
        self.assertIsNotNone(sentry)
        self.assertEqual(sentry["category"], "observability")
        self.assertEqual(sentry["confidence"], "high")
        self.assertIn("package.json", sentry["evidence_paths"])

    def test_sentry_node_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{"dependencies": {"@sentry/node": "1.0"}}')
            records = [_record("package.json")]
            dependencies = {"dependencies": [_dep(records, "@sentry/node")]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "Sentry"))

    def test_opentelemetry_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "opentelemetry-api==1.0\n")
            records = [_record("requirements.txt")]
            dep = {
                "name": "opentelemetry-api",
                "version": "1.0",
                "ecosystem": "pip",
                "dependency_type": None,
                "source_file": "requirements.txt",
                "github_url": "https://x/requirements.txt",
                "likely_role": None,
            }
            dependencies = {"dependencies": [dep]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "OpenTelemetry"))

    def test_prometheus_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "prometheus-client==0.19\n")
            records = [_record("requirements.txt")]
            dep = {
                "name": "prometheus-client",
                "version": "0.19",
                "ecosystem": "pip",
                "dependency_type": None,
                "source_file": "requirements.txt",
                "github_url": "https://x/requirements.txt",
                "likely_role": None,
            }
            dependencies = {"dependencies": [dep]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "Prometheus"))


class CloudSdkTests(unittest.TestCase):
    def test_aws_sdk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "boto3==1.34\n")
            records = [_record("requirements.txt")]
            dep = {
                "name": "boto3",
                "version": "1.34",
                "ecosystem": "pip",
                "dependency_type": None,
                "source_file": "requirements.txt",
                "github_url": "https://x/requirements.txt",
                "likely_role": None,
            }
            dependencies = {"dependencies": [dep]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "AWS SDK"))

    def test_azure_sdk_substring(self) -> None:
        # Substring match: "azure-storage-blob" matches the "azure"
        # prefix in the new implementation.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "azure-storage-blob==12.0\n")
            records = [_record("requirements.txt")]
            dep = {
                "name": "azure-storage-blob",
                "version": "12.0",
                "ecosystem": "pip",
                "dependency_type": None,
                "source_file": "requirements.txt",
                "github_url": "https://x/requirements.txt",
                "likely_role": None,
            }
            dependencies = {"dependencies": [dep]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "Azure SDK"))

    def test_azure_exact_name(self) -> None:
        # The exact string "azure" also matches.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "azure==1.0\n")
            records = [_record("requirements.txt")]
            dep = {
                "name": "azure",
                "version": "1.0",
                "ecosystem": "pip",
                "dependency_type": None,
                "source_file": "requirements.txt",
                "github_url": "https://x/requirements.txt",
                "likely_role": None,
            }
            dependencies = {"dependencies": [dep]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "Azure SDK"))

    def test_gcp_sdk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "requirements.txt", "google-cloud-storage==2.0\n")
            records = [_record("requirements.txt")]
            dep = {
                "name": "google-cloud-storage",
                "version": "2.0",
                "ecosystem": "pip",
                "dependency_type": None,
                "source_file": "requirements.txt",
                "github_url": "https://x/requirements.txt",
                "likely_role": None,
            }
            dependencies = {"dependencies": [dep]}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "GCP SDK"))


class IdentityTests(unittest.TestCase):
    def test_oauth_oidc_saml(self) -> None:
        security = {"security_signals": [
            {"category": "auth", "signal": "oauth provider configured", "source_file": "src/auth.py"},
        ]}
        result = detect_integrations(Path("/nonexistent"), "acme", "widget", "abc1234", [], {"dependencies": []}, security, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "OAuth/OIDC/SAML"))

    def test_jwt_session(self) -> None:
        security = {"security_signals": [
            {"category": "auth", "signal": "JWT issued at login", "source_file": "src/auth.py"},
        ]}
        result = detect_integrations(Path("/nonexistent"), "acme", "widget", "abc1234", [], {"dependencies": []}, security, {"technologies": []})
        self.assertIsNotNone(_by_tech(result["integrations"], "JWT/session"))

    def test_no_auth_signals(self) -> None:
        security = {"security_signals": [
            {"category": "crypto", "signal": "uses HTTPS", "source_file": "README.md"},
        ]}
        result = detect_integrations(Path("/nonexistent"), "acme", "widget", "abc1234", [], {"dependencies": []}, security, {"technologies": []})
        self.assertIsNone(_by_tech(result["integrations"], "OAuth/OIDC/SAML"))
        self.assertIsNone(_by_tech(result["integrations"], "JWT/session"))


class DockerRuntimeTests(unittest.TestCase):
    def test_docker_detected(self) -> None:
        records = [_record("Dockerfile"), _record("docker-compose.yml")]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Dockerfile").write_text("FROM node:22\n", encoding="utf-8")
            (repo / "docker-compose.yml").write_text("services:\n", encoding="utf-8")
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, {"dependencies": []}, {"security_signals": []}, {"technologies": []})
        docker = _by_tech(result["integrations"], "Docker")
        self.assertIsNotNone(docker)
        self.assertEqual(docker["category"], "runtime")

    def test_no_docker_no_runtime_finding(self) -> None:
        result = detect_integrations(Path("/nonexistent"), "acme", "widget", "abc1234", [_record("README.md")], {"dependencies": []}, {"security_signals": []}, {"technologies": []})
        self.assertIsNone(_by_tech(result["integrations"], "Docker"))


class DeduplicationTests(unittest.TestCase):
    def test_no_duplicate_tech(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{"dependencies": {"sentry": "1.0", "sentry-sdk": "1.0"}}')
            records = [_record("package.json")]
            deps_list = [_dep(records, "sentry"), _dep(records, "sentry-sdk")]
            dependencies = {"dependencies": deps_list}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        sentries = [i for i in result["integrations"] if i["technology"] == "Sentry"]
        self.assertEqual(len(sentries), 1)


class SortingTests(unittest.TestCase):
    def test_results_sorted_by_category_technology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "package.json", '{"dependencies": {"sentry": "1.0", "boto3": "1.0"}}')
            records = [_record("package.json")]
            deps_list = [
                {"name": "sentry", "version": "1.0", "ecosystem": "npm", "dependency_type": "runtime",
                 "source_file": "package.json", "github_url": "x", "likely_role": None},
                {"name": "boto3", "version": "1.0", "ecosystem": "pip", "dependency_type": None,
                 "source_file": "package.json", "github_url": "x", "likely_role": None},
            ]
            dependencies = {"dependencies": deps_list}
            result = detect_integrations(repo, "acme", "widget", "abc1234", records, dependencies, {"security_signals": []}, {"technologies": []})
        categories_techs = [(i["category"], i["technology"]) for i in result["integrations"]]
        self.assertEqual(categories_techs, sorted(categories_techs))


class HelperTests(unittest.TestCase):
    def test_has_docker(self) -> None:
        self.assertTrue(_has_docker([_record("Dockerfile")]))
        self.assertTrue(_has_docker([_record("docker-compose.yml")]))
        self.assertFalse(_has_docker([_record("README.md")]))

    def test_paths_for_dep(self) -> None:
        records = [_record("package.json")]
        dep_names = {
            "sentry": _dep(records, "sentry"),
            "@sentry/node": _dep(records, "@sentry/node"),
        }
        paths = _paths_for_dep(records, dep_names, ("sentry", "@sentry/node"))
        self.assertEqual(paths, ["package.json"])

    def test_security_text_lowercase(self) -> None:
        security = {"security_signals": [
            {"category": "AUTH", "signal": "OAUTH", "source_file": "x.py"},
        ]}
        self.assertEqual(_security_text(security), "auth oauth x.py")

    def test_paths_for_security_match(self) -> None:
        security = {"security_signals": [
            {"category": "auth", "signal": "uses oauth2", "source_file": "src/auth.py"},
            {"category": "session", "signal": "jwt cookies", "source_file": "src/session.py"},
            {"category": "crypto", "signal": "uses sha256", "source_file": "src/util.py"},
        ]}
        paths = _paths_for_security(security, ("oauth",))
        self.assertEqual(paths, ["src/auth.py"])


if __name__ == "__main__":
    unittest.main()
