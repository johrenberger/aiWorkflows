from __future__ import annotations

from pathlib import Path

from ..io_utils import safe_read_text
from ..model import FileRecord


def detect_build_deploy(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    for record in records:
        path = record.path.lower()
        if "dockerfile" in path or "containerfile" in path:
            findings.append(_artifact("Dockerfile", record, _runtime_from_docker(repo_path / record.path), _docker_ports(repo_path / record.path), "high"))
        elif "docker-compose" in path or "compose" in path:
            findings.append(_artifact("docker-compose", record, None, _docker_ports(repo_path / record.path), "high"))
        elif path.endswith((".yaml", ".yml")) and ("k8s" in path or "kubernetes" in path or ".github/workflows" in path):
            findings.append(_artifact("yaml-manifest", record, None, _docker_ports(repo_path / record.path), "medium"))
        elif path.endswith((".tf", ".tfvars")):
            findings.append(_artifact("terraform", record, None, None, "high"))
        elif "jenkinsfile" in path or "gitlab-ci" in path:
            findings.append(_artifact("ci-config", record, None, None, "high"))
        elif path.endswith((".sh", ".ps1")) and any(word in path for word in ("deploy", "release", "release", "publish")):
            findings.append(_artifact("deployment-script", record, None, None, "medium"))
        elif path.endswith((".env", ".env.example", ".env.sample")):
            findings.append(_artifact("env-template", record, None, None, "high"))
    return {"build_deploy": sorted(findings, key=lambda x: (x["artifact_type"], x["path"]))}


def _artifact(artifact_type: str, record: FileRecord, runtime: str | None, ports: list[int] | None, confidence: str) -> dict:
    payload = {
        "artifact_type": artifact_type,
        "path": record.path,
        "github_url": record.github_url,
        "detected_runtime": runtime,
        "commands_or_ports": ports or [],
        "confidence": confidence,
    }
    return payload


def _runtime_from_docker(path: Path) -> str | None:
    text, _ = safe_read_text(path)
    if not text:
        return None
    for line in text.splitlines():
        if line.strip().startswith("FROM "):
            return line.split()[1]
    return None


def _docker_ports(path: Path) -> list[int]:
    text, _ = safe_read_text(path)
    if not text:
        return []
    ports: list[int] = []
    for line in text.splitlines():
        if "EXPOSE" in line.upper():
            for token in line.split():
                if token.isdigit():
                    ports.append(int(token))
    return ports

