from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


TOOL_NAME = "repo-discovery-analyzer"


@dataclass(slots=True)
class AnalysisConfig:
    repo_path: Path
    github_url: str
    commit: str
    output_dir: Path
    include_large_files: bool = False
    max_file_bytes: int = 2_000_000
    json_indent: int = 2
    fail_on_validation_error: bool = False
    verbose: bool = False


@dataclass(slots=True)
class FileRecord:
    path: str
    extension: str
    size_bytes: int
    language_guess: str
    role_guess: str
    line_count: int | None
    source_line_count: int | None
    github_url: str
    reviewed_by_analyzer: bool
    skipped: bool
    skip_reason: str | None = None


@dataclass(slots=True)
class AnalysisManifest:
    tool_name: str
    tool_version: str
    repo_path: str
    source_url_prefix: str
    commit: str
    output_dir: str
    start_time_utc: str
    end_time_utc: str
    elapsed_ms: int
    warnings: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


def dataclass_to_json(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, dict):
        return {k: dataclass_to_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [dataclass_to_json(v) for v in value]
    if isinstance(value, tuple):
        return [dataclass_to_json(v) for v in value]
    return value
