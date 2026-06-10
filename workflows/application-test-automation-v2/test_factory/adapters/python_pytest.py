from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..analyzers.coverage_normalizer import parse_python_coverage_xml
from ..analyzers.module_detector import detect_language_and_module
from ..analyzers.mutation_analyzer import detect_mutation_tool
from ..analyzers.source_test_mapper import map_source_to_tests
from ..models import AdapterDetection, CommandSpec, CoverageRecord, FileRecord, MutationToolDetection
from .base import BaseAdapter


class PythonPytestAdapter(BaseAdapter):
    language = "python"

    def detect(self, repo_path: str | Path) -> AdapterDetection:
        repo_path = Path(repo_path)
        evidence = []
        confidence = 0.0
        for candidate in ("pyproject.toml", "requirements.txt", "setup.py", "pytest.ini"):
            if (repo_path / candidate).exists():
                evidence.append(candidate)
                confidence += 0.25
        for path in repo_path.rglob("*.py"):
            evidence.append(path.name)
            confidence += 0.1
            break
        return AdapterDetection(language="python", adapter="python_pytest", confidence=min(confidence, 1.0), evidence=evidence)

    def inventory(self, repo_path: str | Path) -> list[FileRecord]:
        repo_path = Path(repo_path)
        records: list[FileRecord] = []
        for path in repo_path.rglob("*.py"):
            language, module, _ = detect_language_and_module(repo_path, path)
            records.append(FileRecord(path=str(path.relative_to(repo_path)).replace("\\", "/"), language=language, module=module, size=path.stat().st_size))
        return records

    def discover_test_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        return CommandSpec(command=["pytest"], cwd=str(repo_path), description="Run pytest")

    def discover_coverage_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        return CommandSpec(command=["pytest", "--cov", "--cov-report=xml"], cwd=str(repo_path), description="Run pytest with coverage")

    def parse_coverage(self, report_paths: Sequence[str | Path]) -> list[CoverageRecord]:
        records: list[CoverageRecord] = []
        for report in report_paths:
            report = Path(report)
            if report.suffix.lower() == ".xml":
                records.extend(parse_python_coverage_xml(report))
        return records

    def find_test_candidates(self, source_file: str | Path) -> list[str]:
        return map_source_to_tests(str(source_file), "python")

    def recommend_supporting_files(self, source_file: str | Path) -> list[str]:
        p = Path(source_file)
        return [str(p.parent / "pyproject.toml"), str(p.parent / "pytest.ini"), str(p.parent / "setup.py")]

    def detect_mutation_tool(self, repo_path: str | Path, module: str) -> MutationToolDetection:
        return detect_mutation_tool(repo_path, module, "python")

    def discover_mutation_command(self, repo_path: str | Path, module: str, files: Sequence[str | Path]) -> CommandSpec:
        detection = self.detect_mutation_tool(repo_path, module)
        if detection.available:
            return CommandSpec(command=detection.command, cwd=str(repo_path), description="Run Python mutation testing")
        return CommandSpec(command=["pytest"], cwd=str(repo_path), description="Fallback Python test command")

