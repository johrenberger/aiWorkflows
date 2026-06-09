from __future__ import annotations

from pathlib import Path

from ..io_utils import safe_read_text
from ..model import FileRecord


def detect_contradictions(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord], stack: dict, routes: dict, tests: dict, build_deploy: dict) -> dict:
    findings: list[dict] = []
    readme_mentions = _docs_mentions(repo_path, records)
    techs = {item["technology"].lower() for item in stack.get("technologies", [])}
    if any(db in readme_mentions and db not in techs for db in ("postgres", "mysql", "mariadb", "oracle", "sql server", "mongodb", "redis", "elasticsearch")):
        findings.append(_candidate("README mentions a database not found in configs", "README/docs mentions a database, but config evidence does not confirm it", "check docs vs. config", "medium", True))
    if len({Path(r.path).name for r in records if Path(r.path).name in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}}) > 1:
        findings.append(_candidate("package manager mismatch", "multiple package manager lockfiles were found", "normalize package management", "high", False))
    if routes.get("routes") and not _api_docs_present(records):
        findings.append(_candidate("routes exist but no API documentation evidence found", "route evidence exists", "add API docs or note omission", "medium", True))
    if tests.get("testing") and not _ci_runs_tests(repo_path, records):
        findings.append(_candidate("tests exist but CI does not appear to run them", "tests were detected", "verify CI test execution", "medium", True))
    if build_deploy.get("build_deploy"):
        docker_ports = [p for item in build_deploy["build_deploy"] for p in item.get("commands_or_ports", []) if isinstance(p, int)]
        app_ports = _app_ports(repo_path, records)
        if docker_ports and app_ports and set(docker_ports) != set(app_ports):
            findings.append(_candidate("Docker exposed port differs from application port", "docker ports differ from app ports", "check runtime port mapping", "medium", True))
    findings = sorted(findings, key=lambda x: x["summary"])
    return {"contradiction_candidates": findings}


def _candidate(summary: str, evidence_a: str, evidence_b: str, confidence: str, needs_ai: bool) -> dict:
    return {
        "summary": summary,
        "evidence_a": evidence_a,
        "evidence_b": evidence_b,
        "impact_hint": "possible documentation/configuration mismatch",
        "confidence": confidence,
        "needs_ai_interpretation": needs_ai,
    }


def _docs_mentions(repo_path: Path, records: list[FileRecord]) -> str:
    texts = []
    for record in records:
        name = Path(record.path).name.upper()
        if name.startswith("README"):
            text, _ = safe_read_text(repo_path / record.path)
            if text:
                texts.append(text.lower())
    return "\n".join(texts)


def _api_docs_present(records: list[FileRecord]) -> bool:
    for record in records:
        name = Path(record.path).name.lower()
        if any(token in name for token in ("openapi", "swagger", "api")) and Path(record.path).suffix.lower() in {".md", ".json", ".yaml", ".yml"}:
            return True
    return False


def _ci_runs_tests(repo_path: Path, records: list[FileRecord]) -> bool:
    for record in records:
        if ".github/workflows" in record.path:
            text, _ = safe_read_text(repo_path / record.path)
            if text and "test" in text.lower():
                return True
    return False


def _app_ports(repo_path: Path, records: list[FileRecord]) -> list[int]:
    ports: list[int] = []
    for record in records:
        if Path(record.path).name.lower() in {"dockerfile", "containerfile"}:
            text, _ = safe_read_text(repo_path / record.path)
            if text:
                for line in text.splitlines():
                    if "EXPOSE" in line.upper():
                        for token in line.split():
                            if token.isdigit():
                                ports.append(int(token))
    return ports
