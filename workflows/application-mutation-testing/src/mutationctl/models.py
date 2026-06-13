from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_STATUSES = {
    "PASS",
    "PARTIAL",
    "BLOCKED",
    "EXCLUDED",
    "DEFERRED",
    "FAIL",
    "NOT_RUN",
}


@dataclass(slots=True)
class WorkflowConfig:
    repo_url: str | None = None
    repo_path: str | None = None
    branch: str | None = None
    mode: str = "report"
    allow_commit: bool = False
    allow_dependency_install: bool = False
    allow_production_fixes: bool = False
    allow_test_changes: bool = False
    max_target_files: int = 5
    mutation_target_initial: int = 60
    mutation_target_mature: int = 75


@dataclass(slots=True)
class RepoInput:
    original: str
    repo_url: str | None = None
    repo_path: str | None = None


@dataclass(slots=True)
class RepoMetadata:
    repo_path: str
    repo_url: str | None
    branch: str
    commit_sha: str
    is_dirty: bool
    captured_at: str


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    exit_code: int | None
    duration_seconds: float
    status: str
    stdout_path: str | None = None
    stderr_path: str | None = None
    timed_out: bool = False


@dataclass(slots=True)
class RunRecord:
    run_id: str
    repo_url: str | None
    repo_path: str | None
    branch: str | None
    mode: str
    status: str
    created_at: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Blocker:
    code: str
    status: str
    reason: str
    evidence: str


@dataclass(slots=True)
class LedgerTask:
    task_id: str
    title: str
    status: str
    details: str | None = None


@dataclass(slots=True)
class ValidationGateResult:
    gate_name: str
    status: str
    details: str | None = None


@dataclass(slots=True)
class LanguageDetectionResult:
    language: str
    confidence: float
    evidence: list[str]


@dataclass(slots=True)
class MutationToolEvidence:
    tool_name: str
    ecosystem: str
    available: bool
    install_required: bool
    version: str | None
    config_files: list[str]
    evidence: list[str]
    blocker_reason: str | None = None


@dataclass(slots=True)
class ToolDetectionResult:
    selected_tool: str | None
    ecosystem: str | None
    status: str
    evidence: list[MutationToolEvidence]


@dataclass(slots=True)
class CoverageFileSummary:
    source_file: str
    line_coverage: float | None
    branch_coverage: float | None
    covered_lines: list[int]
    uncovered_lines: list[int]
    evidence_path: str
    status: str
    # Optional complexity signal. When a coverage source (e.g. v2's
    # test-factory risk_scores.json) emits a per-file complexity value,
    # it lands here. When None, callers should fall back to
    # ``mutationctl.targeting.scorer.complexity_score(source)`` if they
    # need a numeric value.
    #
    # NOTE: added as the LAST field with a default so existing
    # positional callers (e.g. test_007_target_selection.py) keep
    # working. New callers should pass by keyword.
    complexity: float | None = None


@dataclass(slots=True)
class CoverageSummary:
    source_file: str | None
    line_coverage: float | None
    branch_coverage: float | None
    covered_lines: list[int]
    uncovered_lines: list[int]
    evidence_path: str | None
    status: str
    files: list[CoverageFileSummary] = field(default_factory=list)


@dataclass(slots=True)
class MutationTarget:
    source_file: str
    language: str
    score: float
    eligibility_status: str
    rationale: str
    coverage_readiness: float
    complexity_score: float
    runtime_feasibility: float
    selected: bool


@dataclass(slots=True)
class TargetSelectionResult:
    selected: list[MutationTarget]
    excluded: list[MutationTarget]
    status: str


@dataclass(slots=True)
class MutationCommand:
    tool_name: str
    ecosystem: str
    target_file: str
    command: list[str]
    timeout_seconds: int
    working_directory: str


@dataclass(slots=True)
class MutationRunResult:
    tool_name: str
    target_file: str
    command: list[str]
    exit_code: int | None
    status: str
    runtime_seconds: float
    stdout_path: str | None
    stderr_path: str | None
    report_paths: list[str]
    timed_out: bool = False


@dataclass(slots=True)
class NormalizedMutant:
    mutant_id: str
    source_file: str
    line: int | None
    operator: str
    original: str | None
    mutated: str | None
    status: str
    evidence: str


@dataclass(slots=True)
class NormalizedMutationResult:
    tool_name: str
    status: str
    killed: int | None
    survived: int | None
    timeout: int | None
    ignored: int | None
    mutation_score: float | None
    evidence_path: str
    mutants: list[NormalizedMutant] = field(default_factory=list)


@dataclass(slots=True)
class SourceContext:
    file_path: str
    start_line: int
    end_line: int
    content: str
    truncated: bool


@dataclass(slots=True)
class RelatedTestReference:
    file_path: str
    test_name: str | None
    start_line: int
    end_line: int
    content: str
    evidence: list[str]


@dataclass(slots=True)
class TestContext:
    references: list[RelatedTestReference]
    truncated: bool = False


@dataclass(slots=True)
class SurvivorPacket:
    packet_id: str
    mutant_id: str
    source_file: str
    line: int | None
    operator: str
    original: str | None
    mutated: str | None
    mutant_status: str
    source_context: SourceContext
    related_tests: list[RelatedTestReference]
    coverage_context: dict[str, Any] | None
    size_bytes: int
    truncated: bool
    evidence: list[str]
    status: str


@dataclass(slots=True)
class DeterministicClassificationRule:
    rule_id: str
    operators: list[str]
    classification: str
    confidence: str
    recommended_action: str


@dataclass(slots=True)
class SurvivorClassification:
    classification_id: str
    mutant_id: str
    source_file: str
    line: int | None
    operator: str
    classification: str | None
    confidence: str | None
    evidence: list[str]
    recommended_action: str
    equivalent_candidate: bool
    needs_human_review: bool
    classifier_type: str
    requires_llm_review: bool = False
    status: str = "PASS"
    reason: str | None = None


@dataclass(slots=True)
class LLMClassificationRequest:
    request_id: str
    packet_id: str
    mutant_id: str
    allowed_classifications: list[str]
    survivor_packet: SurvivorPacket
    constraints: dict[str, Any]
    expected_response_schema_version: str


@dataclass(slots=True)
class LLMClassificationResponse:
    schema_version: str
    request_id: str
    packet_id: str
    mutant_id: str
    classification: str
    confidence: str
    evidence: list[str]
    recommended_action: str
    equivalent_candidate: bool
    needs_human_review: bool
    rationale: str


@dataclass(slots=True)
class LLMValidationResult:
    request_id: str
    packet_id: str
    status: str
    accepted: bool
    reason: str
    response: LLMClassificationResponse | None = None


@dataclass(slots=True)
class PatchFileChange:
    path: str
    change_type: str
    diff: str
    is_test_file: bool
    is_production_file: bool


@dataclass(slots=True)
class PatchProposal:
    proposal_id: str
    source_type: str
    mutant_ids: list[str]
    classification_ids: list[str]
    files: list[PatchFileChange]
    rationale: str
    expected_behavior: str
    evidence: list[str]
    parse_error: str | None = None


@dataclass(slots=True)
class TestWeakeningFinding:
    path: str
    finding_type: str
    reason: str
    evidence: list[str]


@dataclass(slots=True)
class PatchSafetyResult:
    proposal_id: str
    status: str
    accepted: bool
    reasons: list[str]
    rejected_files: list[str]
    weakening_findings: list[TestWeakeningFinding]
    requires_human_review: bool
    evidence: list[str]


@dataclass(slots=True)
class PatchApplyResult:
    proposal_id: str
    status: str
    applied: bool
    files_changed: list[str]
    failure_reason: str | None
    evidence: list[str]
    backups: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class PatchRevertResult:
    proposal_id: str
    status: str
    reverted: bool
    files_restored: list[str]
    failure_reason: str | None
    evidence: list[str]


@dataclass(slots=True)
class FocusedTestCommand:
    command: list[str]
    working_directory: str
    timeout_seconds: int


@dataclass(slots=True)
class FocusedTestResult:
    command: list[str]
    exit_code: int | None
    status: str
    runtime_seconds: float
    stdout_path: str | None
    stderr_path: str | None
    evidence: list[str]


@dataclass(slots=True)
class ValidationGate:
    gate_id: str
    name: str
    required: bool


@dataclass(slots=True)
class ValidationGateResult:
    gate_id: str
    name: str
    status: str
    reason: str
    evidence: list[str]
    required: bool


@dataclass(slots=True)
class ValidationSummary:
    total_gates: int
    pass_count: int
    partial_count: int
    blocked_count: int
    fail_count: int
    not_run_count: int
    required_gates_passed: bool
    commit_allowed: bool
    blocking_gate_ids: list[str]
    evidence: list[str]
    gates: list[ValidationGateResult] = field(default_factory=list)


@dataclass(slots=True)
class MutationRecheckPlan:
    target_file: str
    baseline_command: list[str]
    recheck_command: list[str]
    tool_name: str
    scope: str
    evidence: list[str]


@dataclass(slots=True)
class MutationScoreDelta:
    score_before: float | None
    score_after: float | None
    delta: float | None


@dataclass(slots=True)
class MutationRecheckResult:
    target_file: str
    baseline_result_id: str
    recheck_result_id: str
    command: list[str]
    status: str
    killed_before: int | None
    survived_before: int | None
    score_before: float | None
    killed_after: int | None
    survived_after: int | None
    score_after: float | None
    score_delta: float | None
    remaining_survivors: list[NormalizedMutant]
    evidence: list[str]


@dataclass(slots=True)
class ChangedFile:
    path: str
    change_type: str
    allowed: bool
    reason: str


@dataclass(slots=True)
class GitStatus:
    branch: str
    commit_sha: str
    dirty: bool
    changed_files: list[ChangedFile]
    untracked_files: list[str]
    evidence: list[str]


@dataclass(slots=True)
class BranchPlan:
    base_branch: str
    proposed_branch: str
    branch_exists: bool
    safe_to_create: bool
    reason: str
    evidence: list[str]


@dataclass(slots=True)
class CommitPlan:
    plan_id: str
    base_branch: str
    proposed_branch: str
    commit_message: str
    files_to_commit: list[str]
    excluded_files: list[str]
    validation_summary_id: str
    commit_allowed: bool
    reasons: list[str]
    evidence: list[str]


@dataclass(slots=True)
class CommitGateResult:
    status: str
    allow_commit: bool
    validation_passed: bool
    changed_files_allowed: bool
    branch_safe: bool
    commit_allowed: bool
    blockers: list[str]
    evidence: list[str]


@dataclass(slots=True)
class CommitExecutionResult:
    status: str
    commit_created: bool
    commit_sha: str | None
    branch: str
    message: str
    evidence: list[str]


@dataclass(slots=True)
class WorkflowRunPlan:
    mode: str
    repo_path: str
    workspace: str
    phases: list[str]


@dataclass(slots=True)
class WorkflowRunResult:
    run_id: str
    status: str
    phases_completed: list[str]
    phases_blocked: list[str]
    ledger_path: str
    final_summary_path: str
    validation_summary: ValidationSummary
    commit_plan: CommitPlan
    evidence: list[str]


@dataclass(slots=True)
class EndToEndSyntheticResult:
    workflow_result: WorkflowRunResult
    synthetic_repo_path: str
    external_tools_used: bool


@dataclass(slots=True)
class RealToolPolicy:
    allow_real_tools: bool = False
    allow_mutmut: bool = False
    allow_dependency_install: bool = False
    allow_network: bool = False
    require_clean_tree: bool = True
    require_existing_tool: bool = True
    timeout_seconds: int = 600
    allow_dirty_tree: bool = False


@dataclass(slots=True)
class RealToolExecutionDecision:
    allowed: bool
    tool_name: str
    command: list[str]
    reasons: list[str]
    blockers: list[str]
    evidence: list[str]


@dataclass(slots=True)
class FinalSummary:
    run_id: str
    status: str
    path: str
    sections: list[str]
    evidence: list[str]
