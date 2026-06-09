from __future__ import annotations

from pathlib import Path

from .io_utils import safe_read_text
from .model import FileRecord


def detect_integrations(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord], dependencies: dict, security: dict, stack: dict) -> dict:
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(category: str, technology: str, paths: list[str], confidence: str = "medium"):
        key = (category, technology)
        if key in seen or not paths:
            return
        seen.add(key)
        findings.append(
            {
                "category": category,
                "technology": technology,
                "evidence_paths": sorted(set(paths)),
                "evidence_urls": _urls(records, paths),
                "confidence": confidence,
            }
        )

    dep_names = {item["name"].lower(): item for item in dependencies.get("dependencies", [])}
    if any(name in dep_names for name in ("sentry", "@sentry/node", "sentry-sdk")):
        add("observability", "Sentry", _paths_for_dep(records, dep_names, ("sentry", "@sentry/node", "sentry-sdk")), "high")
    if any(name in dep_names for name in ("opentelemetry-api", "@opentelemetry/api", "opentelemetry")):
        add("observability", "OpenTelemetry", _paths_for_dep(records, dep_names, ("opentelemetry-api", "@opentelemetry/api", "opentelemetry")), "high")
    if any(name in dep_names for name in ("prometheus-client", "prom-client")):
        add("observability", "Prometheus", _paths_for_dep(records, dep_names, ("prometheus-client", "prom-client")), "high")
    if any(name in dep_names for name in ("aws-sdk", "@aws-sdk/*", "boto3")):
        add("cloud", "AWS SDK", _paths_for_dep(records, dep_names, ("aws-sdk", "@aws-sdk", "boto3")), "medium")
    if any(name in dep_names for name in ("@azure/*", "azure", "azure-storage")):
        add("cloud", "Azure SDK", _paths_for_dep(records, dep_names, ("azure", "azure-storage", "@azure")), "medium")
    if any(name in dep_names for name in ("google-cloud", "@google-cloud", "google-cloud-storage")):
        add("cloud", "GCP SDK", _paths_for_dep(records, dep_names, ("google-cloud", "@google-cloud")), "medium")
    if any(term in _security_text(security) for term in ("oauth", "oidc", "saml")):
        add("identity", "OAuth/OIDC/SAML", _paths_for_security(security, ("oauth", "oidc", "saml")), "high")
    if any(term in _security_text(security) for term in ("jwt", "session")):
        add("identity", "JWT/session", _paths_for_security(security, ("jwt", "session")), "high")
    if _has_docker(records):
        add("runtime", "Docker", [r.path for r in records if "dockerfile" in r.path.lower() or "docker-compose" in r.path.lower()], "high")
    return {"integrations": sorted(findings, key=lambda x: (x["category"], x["technology"]))}


def _urls(records: list[FileRecord], paths: list[str]) -> list[str]:
    urls = []
    for path in paths:
        for record in records:
            if record.path == path:
                urls.append(record.github_url)
    return sorted(set(urls))


def _paths_for_dep(records: list[FileRecord], dep_names: dict[str, dict], needles: tuple[str, ...]) -> list[str]:
    paths = []
    for needle in needles:
        for name, item in dep_names.items():
            if needle in name:
                paths.append(item["source_file"])
    return sorted(set(paths))


def _security_text(security: dict) -> str:
    return " ".join(
        f"{item.get('category', '')} {item.get('signal', '')} {item.get('source_file', '')}"
        for item in security.get("security_signals", [])
    ).lower()


def _paths_for_security(security: dict, needles: tuple[str, ...]) -> list[str]:
    paths = []
    for item in security.get("security_signals", []):
        blob = f"{item.get('category', '')} {item.get('signal', '')}".lower()
        if any(needle in blob for needle in needles):
            paths.append(item.get("source_file"))
    return sorted(set(p for p in paths if p))


def _has_docker(records: list[FileRecord]) -> bool:
    return any("dockerfile" in r.path.lower() or "docker-compose" in r.path.lower() for r in records)

