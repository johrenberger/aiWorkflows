from __future__ import annotations

from pathlib import Path

from ..io_utils import safe_read_text
from ..model import FileRecord


def detect_testing(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    test_paths = [r.path for r in records if r.role_guess == "test"]
    if test_paths:
        findings.append(
            {
                "type": "test-surface",
                "framework_tool": _infer_framework(records, repo_path),
                "paths": sorted(test_paths),
                "github_urls": _urls(records, test_paths),
                "command": _test_command(repo_path),
                "confidence": "high",
            }
        )
    coverage = _coverage_tool(records, repo_path)
    if coverage:
        findings.append(
            {
                "type": "coverage-tool",
                "framework_tool": coverage,
                "paths": _paths_for(records, coverage),
                "github_urls": _urls(records, _paths_for(records, coverage)),
                "command": None,
                "confidence": "medium",
            }
        )
    ci = [r.path for r in records if ".github/workflows" in r.path or "gitlab-ci" in r.path.lower() or "jenkins" in r.path.lower()]
    if ci:
        findings.append(
            {
                "type": "ci-test-step",
                "framework_tool": "CI workflow",
                "paths": sorted(ci),
                "github_urls": _urls(records, ci),
                "command": _ci_test_command(repo_path),
                "confidence": "medium",
            }
        )
    return {"testing": findings, "source_to_test_ratio": _ratio(records)}


def _infer_framework(records: list[FileRecord], repo_path: Path) -> str | None:
    if (repo_path / "package.json").exists():
        text, _ = safe_read_text(repo_path / "package.json")
        if text and any(name in text for name in ("jest", "vitest", "cypress", "playwright")):
            return "javascript test framework"
    if any(r.path.endswith(".java") for r in records):
        return "JUnit"
    if any(r.path.endswith(".py") for r in records):
        return "pytest/unittest"
    return None


def _coverage_tool(records: list[FileRecord], repo_path: Path) -> str | None:
    if (repo_path / ".coveragerc").exists() or any("coverage" in r.path.lower() for r in records):
        return "coverage.py"
    if any("jacoco" in r.path.lower() for r in records):
        return "JaCoCo"
    return None


def _test_command(repo_path: Path) -> str | None:
    package_json = repo_path / "package.json"
    if package_json.exists():
        text, _ = safe_read_text(package_json)
        if text and '"test"' in text:
            return "npm test"
    if (repo_path / "pyproject.toml").exists() or any((repo_path / name).exists() for name in ("pytest.ini", "tox.ini")):
        return "pytest"
    if (repo_path / "pom.xml").exists():
        return "mvn test"
    if (repo_path / "build.gradle").exists() or (repo_path / "build.gradle.kts").exists():
        return "gradle test"
    return None


def _ci_test_command(repo_path: Path) -> str | None:
    for path in repo_path.rglob("*"):
        if path.is_file() and ".github/workflows" in path.as_posix():
            text, _ = safe_read_text(path)
            if text and "test" in text.lower():
                if "npm test" in text:
                    return "npm test"
                if "pytest" in text:
                    return "pytest"
                if "mvn test" in text:
                    return "mvn test"
                if "gradle test" in text:
                    return "gradle test"
    return None


def _paths_for(records: list[FileRecord], needle: str) -> list[str]:
    return [r.path for r in records if needle.lower() in r.path.lower()]


def _urls(records: list[FileRecord], paths: list[str]) -> list[str]:
    urls = []
    for path in paths:
        for record in records:
            if record.path == path:
                urls.append(record.github_url)
    return sorted(set(urls))


def _ratio(records: list[FileRecord]) -> dict:
    source = sum(1 for r in records if r.role_guess == "source")
    tests = sum(1 for r in records if r.role_guess == "test")
    return {"source_files": source, "test_files": tests, "ratio": round(tests / source, 4) if source else None}

