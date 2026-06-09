from __future__ import annotations

from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, safe_read_text
from ..model import FileRecord


def detect_testing(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    urls_by_path = {record.path: record.github_url for record in records}
    all_test_paths = [r.path for r in records if r.role_guess == "test"]
    test_paths = all_test_paths[:DEFAULT_MAX_SUMMARY_ITEMS]
    if test_paths:
        findings.append(
            {
                "type": "test-surface",
                "framework_tool": _infer_framework(records, repo_path),
                "paths": sorted(test_paths),
                "github_urls": _urls(urls_by_path, test_paths),
                "path_count": len(all_test_paths),
                "paths_truncated": len(all_test_paths) > len(test_paths),
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
                "github_urls": _urls(urls_by_path, _paths_for(records, coverage)),
                "command": None,
                "confidence": "medium",
            }
        )
    all_ci = [r.path for r in records if ".github/workflows" in r.path or "gitlab-ci" in r.path.lower() or "jenkins" in r.path.lower()]
    ci = all_ci[:DEFAULT_MAX_SUMMARY_ITEMS]
    if ci:
        findings.append(
            {
                "type": "ci-test-step",
                "framework_tool": "CI workflow",
                "paths": sorted(ci),
                "github_urls": _urls(urls_by_path, ci),
                "path_count": len(all_ci),
                "paths_truncated": len(all_ci) > len(ci),
                "command": _ci_test_command(records, repo_path),
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


def _ci_test_command(records: list[FileRecord], repo_path: Path) -> str | None:
    for record in records:
        if ".github/workflows" in record.path:
            text, _ = safe_read_text(repo_path / record.path)
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
    return [r.path for r in records if needle.lower() in r.path.lower()][:DEFAULT_MAX_SUMMARY_ITEMS]


def _urls(urls_by_path: dict[str, str], paths: list[str]) -> list[str]:
    return sorted({urls_by_path[path] for path in paths if path in urls_by_path})


def _ratio(records: list[FileRecord]) -> dict:
    source = sum(1 for r in records if r.role_guess == "source")
    tests = sum(1 for r in records if r.role_guess == "test")
    return {"source_files": source, "test_files": tests, "ratio": round(tests / source, 4) if source else None}
