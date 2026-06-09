"""Tests for repo_discovery_analyzer.detectors.build_deploy.

Covers all artifact-type branches: Dockerfile, docker-compose, k8s/GitHub
workflows YAML, Terraform, Jenkins/GitLab CI, deployment scripts, env templates.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repo_discovery_analyzer.detectors.build_deploy import (
    _docker_ports,
    _runtime_from_docker,
    detect_build_deploy,
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


def _by_type(result: dict, artifact_type: str) -> dict | None:
    for item in result["build_deploy"]:
        if item["artifact_type"] == artifact_type:
            return item
    return None


class DockerfileDetectionTests(unittest.TestCase):
    def test_dockerfile_detected_with_runtime_and_ports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "Dockerfile", "FROM node:22-slim\nEXPOSE 3000 8080\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("Dockerfile")])
        df = _by_type(result, "Dockerfile")
        self.assertIsNotNone(df)
        self.assertEqual(df["detected_runtime"], "node:22-slim")
        self.assertEqual(df["commands_or_ports"], [3000, 8080])
        self.assertEqual(df["confidence"], "high")

    def test_containerfile_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "Containerfile", "FROM alpine:3.20\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("Containerfile")])
        cf = _by_type(result, "Dockerfile")
        self.assertIsNotNone(cf)
        self.assertEqual(cf["detected_runtime"], "alpine:3.20")

    def test_dockerfile_without_from_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "Dockerfile", "RUN apt-get update\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("Dockerfile")])
        self.assertIsNone(_by_type(result, "Dockerfile").get("detected_runtime"))

    def test_dockerfile_without_expose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "Dockerfile", "FROM node:22-slim\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("Dockerfile")])
        self.assertEqual(_by_type(result, "Dockerfile")["commands_or_ports"], [])


class DockerComposeDetectionTests(unittest.TestCase):
    def test_docker_compose_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "docker-compose.yml", "EXPOSE 5000\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("docker-compose.yml")])
        comp = _by_type(result, "docker-compose")
        self.assertIsNotNone(comp)
        self.assertEqual(comp["commands_or_ports"], [5000])

    def test_compose_in_subdir(self) -> None:
        # The "compose" substring match catches nested compose files.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "deploy/compose.yaml", "EXPOSE 8000\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("deploy/compose.yaml")])
        self.assertIsNotNone(_by_type(result, "docker-compose"))


class KubernetesAndGitHubActionsTests(unittest.TestCase):
    def test_k8s_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "k8s/deployment.yaml", "apiVersion: apps/v1\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("k8s/deployment.yaml")])
        self.assertIsNotNone(_by_type(result, "yaml-manifest"))

    def test_github_workflows_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, ".github/workflows/ci.yml", "name: CI\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record(".github/workflows/ci.yml")])
        self.assertIsNotNone(_by_type(result, "yaml-manifest"))


class TerraformDetectionTests(unittest.TestCase):
    def test_tf_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "main.tf", 'resource "aws_instance" "x" {}\n')
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("main.tf")])
        self.assertIsNotNone(_by_type(result, "terraform"))
        self.assertIsNone(_by_type(result, "terraform")["detected_runtime"])

    def test_tfvars_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "prod.tfvars", 'region = "us-east-1"\n')
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("prod.tfvars")])
        self.assertIsNotNone(_by_type(result, "terraform"))


class CIDetectionTests(unittest.TestCase):
    def test_jenkinsfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "Jenkinsfile", "pipeline { agent any }\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("Jenkinsfile")])
        self.assertIsNotNone(_by_type(result, "ci-config"))

    def test_gitlab_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, ".gitlab-ci.yml", "test: image: alpine\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record(".gitlab-ci.yml")])
        self.assertIsNotNone(_by_type(result, "ci-config"))


class DeploymentScriptTests(unittest.TestCase):
    def test_deploy_sh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "scripts/deploy.sh", "#!/bin/bash\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("scripts/deploy.sh")])
        self.assertIsNotNone(_by_type(result, "deployment-script"))

    def test_release_ps1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "release.ps1", "Write-Host 'release'\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("release.ps1")])
        self.assertIsNotNone(_by_type(result, "deployment-script"))


class EnvTemplateTests(unittest.TestCase):
    def test_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, ".env", "FOO=bar\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record(".env")])
        self.assertIsNotNone(_by_type(result, "env-template"))

    def test_env_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, ".env.example", "FOO=bar\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record(".env.example")])
        self.assertIsNotNone(_by_type(result, "env-template"))

    def test_env_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, ".env.sample", "FOO=bar\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record(".env.sample")])
        self.assertIsNotNone(_by_type(result, "env-template"))


class EdgeCaseTests(unittest.TestCase):
    def test_no_records_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_build_deploy(Path(tmp), "acme", "widget", "abc1234", [])
        self.assertEqual(result["build_deploy"], [])

    def test_unrelated_file_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "src/app.py", "print('hi')\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("src/app.py")])
        self.assertEqual(result["build_deploy"], [])

    def test_findings_sorted_by_type_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _write(repo, "b/Dockerfile", "FROM alpine\n")
            _write(repo, "a/Dockerfile", "FROM alpine\n")
            result = detect_build_deploy(repo, "acme", "widget", "abc1234", [_record("a/Dockerfile"), _record("b/Dockerfile")])
        paths = [item["path"] for item in result["build_deploy"]]
        self.assertEqual(paths, sorted(paths))


class HelperTests(unittest.TestCase):
    def test_runtime_from_docker_returns_none_for_missing(self) -> None:
        self.assertIsNone(_runtime_from_docker(Path("/nonexistent/Dockerfile")))

    def test_runtime_from_docker_returns_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Dockerfile"
            p.write_text("FROM python:3.13-slim\n", encoding="utf-8")
            self.assertEqual(_runtime_from_docker(p), "python:3.13-slim")

    def test_docker_ports_returns_empty_for_missing(self) -> None:
        self.assertEqual(_docker_ports(Path("/nonexistent/Dockerfile")), [])

    def test_docker_ports_parses_multiple(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "Dockerfile"
            p.write_text("FROM node:22\nEXPOSE 3000 8080\n", encoding="utf-8")
            self.assertEqual(_docker_ports(p), [3000, 8080])


if __name__ == "__main__":
    unittest.main()
