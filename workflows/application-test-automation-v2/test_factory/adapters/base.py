from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from ..models import AdapterDetection, CommandSpec, CoverageRecord, FileRecord, MutationToolDetection


class BaseAdapter(ABC):
    language: str = "unknown"

    @abstractmethod
    def detect(self, repo_path: str | Path) -> AdapterDetection:
        raise NotImplementedError

    @abstractmethod
    def inventory(self, repo_path: str | Path) -> list[FileRecord]:
        raise NotImplementedError

    @abstractmethod
    def discover_test_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        raise NotImplementedError

    @abstractmethod
    def discover_coverage_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        raise NotImplementedError

    @abstractmethod
    def parse_coverage(self, report_paths: Sequence[str | Path]) -> list[CoverageRecord]:
        raise NotImplementedError

    @abstractmethod
    def find_test_candidates(self, source_file: str | Path) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def recommend_supporting_files(self, source_file: str | Path) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def detect_mutation_tool(self, repo_path: str | Path, module: str) -> MutationToolDetection:
        raise NotImplementedError

    @abstractmethod
    def discover_mutation_command(self, repo_path: str | Path, module: str, files: Sequence[str | Path]) -> CommandSpec:
        raise NotImplementedError

