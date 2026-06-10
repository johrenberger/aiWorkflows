from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..analyzers.coverage_normalizer import parse_jacoco_xml
from ..analyzers.module_detector import detect_language_and_module
from ..analyzers.mutation_analyzer import detect_mutation_tool
from ..analyzers.source_test_mapper import map_source_to_tests
from ..models import AdapterDetection, CommandSpec, CoverageRecord, FileRecord, MutationToolDetection
from .base import BaseAdapter


class JavaJUnitAdapter(BaseAdapter):
    language = "java"

    def detect(self, repo_path: str | Path) -> AdapterDetection:
        repo_path = Path(repo_path)
        evidence = []
        confidence = 0.0
        for candidate in (repo_path / "pom.xml", repo_path / "build.gradle", repo_path / "build.gradle.kts"):
            if candidate.exists():
                evidence.append(candidate.name)
                confidence += 0.4
        for path in repo_path.rglob("*.java"):
            evidence.append(path.name)
            confidence += 0.1
            break
        return AdapterDetection(language="java", adapter="java_junit", confidence=min(confidence, 1.0), evidence=evidence)

    def inventory(self, repo_path: str | Path) -> list[FileRecord]:
        repo_path = Path(repo_path)
        records: list[FileRecord] = []
        for path in repo_path.rglob("*.java"):
            language, module, _ = detect_language_and_module(repo_path, path)
            records.append(FileRecord(path=str(path.relative_to(repo_path)).replace("\\", "/"), language=language, module=module, size=path.stat().st_size))
        return records

    def discover_test_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        repo_path = Path(repo_path)
        if (repo_path / "pom.xml").exists():
            return CommandSpec(command=["mvn", "test"], cwd=str(repo_path), description="Run Maven tests")
        return CommandSpec(command=["./gradlew", "test"], cwd=str(repo_path), description="Run Gradle tests")

    def discover_coverage_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        repo_path = Path(repo_path)
        if (repo_path / "pom.xml").exists():
            return CommandSpec(command=["mvn", "test", "jacoco:report"], cwd=str(repo_path), description="Run Maven with JaCoCo")
        return CommandSpec(command=["./gradlew", "test", "jacocoTestReport"], cwd=str(repo_path), description="Run Gradle with JaCoCo")

    def parse_coverage(self, report_paths: Sequence[str | Path]) -> list[CoverageRecord]:
        records: list[CoverageRecord] = []
        for report in report_paths:
            report = Path(report)
            if report.suffix.lower() == ".xml":
                records.extend(parse_jacoco_xml(report))
        return records

    def find_test_candidates(self, source_file: str | Path) -> list[str]:
        return map_source_to_tests(str(source_file), "java")

    def recommend_supporting_files(self, source_file: str | Path) -> list[str]:
        p = Path(source_file)
        return [str(p.parent / "pom.xml"), str(p.parent / "build.gradle"), str(p.parent / "build.gradle.kts")]

    def detect_mutation_tool(self, repo_path: str | Path, module: str) -> MutationToolDetection:
        return detect_mutation_tool(repo_path, module, "java")

    def discover_mutation_command(self, repo_path: str | Path, module: str, files: Sequence[str | Path]) -> CommandSpec:
        detection = self.detect_mutation_tool(repo_path, module)
        if detection.available:
            return CommandSpec(command=detection.command, cwd=str(repo_path), description="Run Java mutation testing")
        return CommandSpec(command=["mvn", "test"], cwd=str(repo_path), description="Fallback Java test command")

