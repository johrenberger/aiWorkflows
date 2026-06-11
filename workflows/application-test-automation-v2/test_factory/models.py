from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


def dataclass_dict(instance: Any) -> dict[str, Any]:
    return asdict(instance)


@dataclass(slots=True)
class ValidationTimeouts:
    targeted_seconds: int = 300
    module_seconds: int = 900
    full_seconds: int = 3600
    mutation_seconds: int = 900


@dataclass(slots=True)
class MutationConfig:
    enabled: bool = False
    high_risk_only: bool = True
    fail_under_score: Optional[float] = None
    tools: dict[str, str] = field(default_factory=lambda: {"java": "pitest", "javascript": "stryker", "python": "mutmut"})
    timeout_seconds: int = 900


@dataclass(slots=True)
class BranchingConfig:
    enabled: bool = False
    allow_dirty: bool = False
    commit_granularity: str = "module"
    branch_prefix: str = "test-automation-v2"


@dataclass(slots=True)
class Config:
    coverage_threshold_line: int = 90
    coverage_threshold_branch: int = 90
    max_supporting_files_per_work_item: int = 5
    max_ai_work_item_chars: int = 120000
    max_retries: int = 3
    eligible_source_globs: list[str] = field(default_factory=lambda: ["**/*.java", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx", "**/*.py"])
    excluded_globs: list[str] = field(default_factory=lambda: ["**/.git/**", "**/node_modules/**", "**/target/**", "**/build/**", "**/dist/**", "**/coverage/**", "**/.venv/**", "**/venv/**", "**/__pycache__/**"])
    generated_file_patterns: list[str] = field(default_factory=lambda: ["generated", "autogen", ".g.dart"])
    exclude_simple_dto: bool = False
    exclude_migrations: bool = False
    exclude_config: bool = False
    language_adapters: dict[str, bool] = field(default_factory=lambda: {"java": True, "javascript": True, "python": True})
    validation_timeouts: ValidationTimeouts = field(default_factory=ValidationTimeouts)
    mutation: MutationConfig = field(default_factory=MutationConfig)
    branching: BranchingConfig = field(default_factory=BranchingConfig)
    max_source_file_chars: int = 200_000


@dataclass(slots=True)
class FileRecord:
    path: str
    language: str
    module: str
    size: int
    sha256: str = ""
    is_test: bool = False
    is_generated: bool = False
    is_excluded: bool = False
    exclusion_reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CoverageRecord:
    path: str
    line_coverage: float = 0.0
    branch_coverage: Optional[float] = None
    uncovered_lines: list[int] = field(default_factory=list)
    uncovered_branches: list[str] = field(default_factory=list)
    report_ref: str = ""


@dataclass(slots=True)
class RiskScoreRecord:
    path: str
    module: str
    line_coverage: float
    branch_coverage: Optional[float]
    complexity: float = 0.0
    churn: float = 0.0
    public_api_exposure: float = 0.0
    dependency_fan_in: float = 0.0
    defect_history: float = 0.0
    data_or_security_sensitivity: float = 0.0
    coverage_gap: float = 0.0
    risk_score: float = 0.0
    missing_evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceTestMapRecord:
    source_path: str
    candidate_tests: list[str] = field(default_factory=list)
    candidate_paths: list[str] = field(default_factory=list)
    supporting_files: list[str] = field(default_factory=list)
    recommended_test_type: str = "unit"
    conventions_summary: str = ""


@dataclass(slots=True)
class WorkItemRecord:
    work_item_id: str
    source_path: str
    language: str
    module: str
    current_line_coverage: float
    current_branch_coverage: Optional[float]
    uncovered_lines: list[int] = field(default_factory=list)
    uncovered_branches: list[str] = field(default_factory=list)
    risk_score: float = 0.0
    risk_factors: dict[str, float] = field(default_factory=dict)
    existing_test_files: list[str] = field(default_factory=list)
    recommended_test_type: str = "unit"
    supporting_files: list[str] = field(default_factory=list)
    conventions_summary: str = ""
    validation_command: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    status: str = "pending"
    priority: float = 0.0
    content_path: str = ""
    validated_files: list[str] = field(default_factory=list)
    validation_repo_sha: str = ""
    validation_reason: str = ""
    validation_report_path: str = ""


@dataclass(slots=True)
class ValidationRunRecord:
    work_item_id: str
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    timeout_seconds: int = 0
    artifact_path: str = ""
    phase: str = "targeted"
    status: str = "completed"


@dataclass(slots=True)
class CommandSpec:
    command: list[str]
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    description: str = ""

    def render(self) -> str:
        return " ".join(self.command)


@dataclass(slots=True)
class AdapterDetection:
    language: str
    adapter: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MutationToolDetection:
    language: str
    tool: str
    available: bool
    evidence: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BranchRunRecord:
    branch_name: str
    module: str
    created: bool
    dirty: bool
    sha: str = ""


@dataclass(slots=True)
class CommitRecord:
    module: str
    message: str
    sha: str = ""
    files: list[str] = field(default_factory=list)
