from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from ..analyzers.coverage_normalizer import parse_coverage_final_json, parse_lcov_info
from ..analyzers.module_detector import detect_language_and_module
from ..analyzers.mutation_analyzer import detect_mutation_tool
from ..analyzers.source_test_mapper import map_source_to_tests
from ..models import AdapterDetection, CommandSpec, CoverageRecord, FileRecord, MutationToolDetection
from .base import BaseAdapter


class JsJestVitestAdapter(BaseAdapter):
    language = "javascript"

    def detect(self, repo_path: str | Path) -> AdapterDetection:
        repo_path = Path(repo_path)
        evidence = []
        confidence = 0.0
        pkg = repo_path / "package.json"
        if pkg.exists():
            evidence.append("package.json")
            confidence += 0.4
            text = pkg.read_text(encoding="utf-8", errors="ignore").lower()
            if "jest" in text:
                confidence += 0.2
            if "vitest" in text:
                confidence += 0.2
        for pattern in ("*.js", "*.jsx", "*.ts", "*.tsx"):
            if any(repo_path.rglob(pattern)):
                confidence += 0.1
                break
        return AdapterDetection(language="javascript", adapter="js_jest_vitest", confidence=min(confidence, 1.0), evidence=evidence)

    def inventory(self, repo_path: str | Path) -> list[FileRecord]:
        repo_path = Path(repo_path)
        records: list[FileRecord] = []
        for path in repo_path.rglob("*"):
            if path.suffix.lower() not in {".js", ".jsx", ".ts", ".tsx"}:
                continue
            language, module, _ = detect_language_and_module(repo_path, path)
            records.append(FileRecord(path=str(path.relative_to(repo_path)).replace("\\", "/"), language=language, module=module, size=path.stat().st_size))
        return records

    def discover_test_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        repo_path = Path(repo_path)
        pkg = repo_path / "package.json"
        if pkg.exists():
            text = pkg.read_text(encoding="utf-8", errors="ignore").lower()
            if "pnpm" in text:
                return CommandSpec(command=["pnpm", "test"], cwd=str(repo_path), description="Run pnpm tests")
            if "yarn" in text:
                return CommandSpec(command=["yarn", "test"], cwd=str(repo_path), description="Run yarn tests")
        return CommandSpec(command=["npm", "test"], cwd=str(repo_path), description="Run npm tests")

    def discover_coverage_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        repo_path = Path(repo_path)
        pkg = repo_path / "package.json"
        if pkg.exists():
            text = pkg.read_text(encoding="utf-8", errors="ignore").lower()
            if "pnpm" in text:
                return CommandSpec(command=["pnpm", "test", "--", "--coverage"], cwd=str(repo_path), description="Run pnpm coverage")
            if "yarn" in text:
                return CommandSpec(command=["yarn", "test", "--coverage"], cwd=str(repo_path), description="Run yarn coverage")
        return CommandSpec(command=["npm", "run", "test:coverage"], cwd=str(repo_path), description="Run npm coverage")

    def parse_coverage(self, report_paths: Sequence[str | Path]) -> list[CoverageRecord]:
        records: list[CoverageRecord] = []
        for report in report_paths:
            report = Path(report)
            if report.name == "coverage-final.json":
                records.extend(parse_coverage_final_json(report))
            elif report.suffix == ".info":
                records.extend(parse_lcov_info(report))
        return records

    def find_test_candidates(self, source_file: str | Path) -> list[str]:
        return map_source_to_tests(str(source_file), "javascript")

    def recommend_supporting_files(self, source_file: str | Path) -> list[str]:
        p = Path(source_file)
        return [str(p.parent / "package.json"), str(p.parent / "jest.config.js"), str(p.parent / "vitest.config.ts")]

    def detect_mutation_tool(self, repo_path: str | Path, module: str) -> MutationToolDetection:
        return detect_mutation_tool(repo_path, module, "javascript")

    def discover_mutation_command(self, repo_path: str | Path, module: str, files: Sequence[str | Path]) -> CommandSpec:
        detection = self.detect_mutation_tool(repo_path, module)
        if detection.available:
            return CommandSpec(command=detection.command, cwd=str(repo_path), description="Run JS mutation testing")
        return CommandSpec(command=["npm", "test"], cwd=str(repo_path), description="Fallback JS test command")

