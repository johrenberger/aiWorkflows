"""Data models for the skill governance pipeline.

These dataclasses are the canonical shape of every artifact
that flows through the pipeline. Keep them simple, serializable,
and stable — they are the contract between modules.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ArtifactType(str, Enum):
    """The kind of artifact discovered."""

    SKILL = "skill"
    AGENT = "agent"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity of a governance finding."""

    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class Decision(str, Enum):
    """Recommendation decisions."""

    KEEP = "keep"
    REWRITE = "rewrite"
    MERGE = "merge"
    SPLIT = "split"
    DEPRECATE = "deprecate"
    RETIRE = "retire"


class OverlapRecommendation(str, Enum):
    """Recommendation for a pair of overlapping artifacts."""

    MERGE = "merge"
    DIFFERENTIATE = "differentiate"
    KEEP_SEPARATE = "keep_separate"


class ResponsibilityFlag(str, Enum):
    """Coherence flag for a skill's responsibility."""

    OVER_BROAD = "over-broad"
    TOO_NARROW = "too-narrow"
    UNCLEAR = "unclear"
    COHERENT = "coherent"


# ---------------------------------------------------------------------------
# Discovered artifact
# ---------------------------------------------------------------------------

@dataclass
class SkillArtifact:
    """A single skill or agent artifact on disk.

    This is the canonical record produced by discovery and
    consumed by every downstream analyzer.
    """

    name: str
    path: str  # forward-slash relative path
    artifact_type: ArtifactType
    size_bytes: int
    estimated_tokens: int
    content_hash: str
    modified_timestamp: str  # ISO 8601 UTC, Z suffix
    declared_version: str | None = None
    owner: str | None = None
    category: str | None = None
    body_excerpt: str = ""  # first ~500 chars of the body for context

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["artifact_type"] = self.artifact_type.value
        return d


# ---------------------------------------------------------------------------
# Metadata and contracts
# ---------------------------------------------------------------------------

REQUIRED_METADATA_FIELDS = (
    "name",
    "artifact_type",
    "purpose",
    "category",
    "owner",
    "version",
    "inputs",
    "outputs",
    "dependencies",
    "intended_consumers",
    "quality_level",
    "last_reviewed",
)


@dataclass
class Metadata:
    """Parsed metadata block from a skill/agent."""

    raw: dict[str, Any]
    name: str | None = None
    artifact_type: str | None = None
    purpose: str | None = None
    category: str | None = None
    owner: str | None = None
    version: str | None = None
    inputs: Any = None
    outputs: Any = None
    dependencies: list[str] = field(default_factory=list)
    intended_consumers: list[str] = field(default_factory=list)
    quality_level: str | None = None
    last_reviewed: str | None = None

    def missing_fields(self) -> list[str]:
        """Return the list of required fields that are missing or empty."""
        out: list[str] = []
        for f in REQUIRED_METADATA_FIELDS:
            v = getattr(self, f, None)
            if v is None or v == "" or v == [] or v == {}:
                out.append(f)
        return out

    def is_purpose_vague(self) -> bool:
        """Return True if the purpose is missing or non-substantive."""
        if not self.purpose:
            return True
        p = self.purpose.strip().lower()
        if len(p) < 20:
            return True
        vague_phrases = {
            "analyze something",
            "do something",
            "produce a report",
            "handle stuff",
            "do work",
        }
        if p in vague_phrases:
            return True
        return False

    def has_structured_contracts(self) -> bool:
        """Return True if inputs and outputs look structured."""
        if not self.inputs or not self.outputs:
            return False
        # Inputs must be a list/dict, not a free-text string
        if isinstance(self.inputs, str):
            return False
        if isinstance(self.outputs, str):
            return False
        return True


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single governance finding."""

    finding_id: str
    artifact_name: str
    severity: Severity
    category: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    suggestion: str | None = None
    # Phase 6 fix: stable identifier for the source artifact. Same value
    # for all findings that originate from the same file, so consumers
    # can group findings by artifact without re-deriving from name.
    artifact_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


# ---------------------------------------------------------------------------
# Dependency analysis
# ---------------------------------------------------------------------------

@dataclass
class DependencyNode:
    """A node in the dependency graph."""

    name: str
    artifact_type: ArtifactType
    depends_on: list[str] = field(default_factory=list)
    depended_on_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["artifact_type"] = self.artifact_type.value
        return d


@dataclass
class DependencyGraph:
    """The full cross-artifact dependency graph."""

    nodes: dict[str, DependencyNode]
    missing_dependencies: list[tuple[str, str]] = field(default_factory=list)
    circular_dependencies: list[list[str]] = field(default_factory=list)
    unused_dependencies: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {n: node.to_dict() for n, node in sorted(self.nodes.items())},
            "missing_dependencies": [
                {"from": a, "to": b} for a, b in sorted(self.missing_dependencies)
            ],
            "circular_dependencies": [sorted(c) for c in self.circular_dependencies],
            "unused_dependencies": [
                {"from": a, "to": b} for a, b in sorted(self.unused_dependencies)
            ],
        }


# ---------------------------------------------------------------------------
# Overlap
# ---------------------------------------------------------------------------

@dataclass
class OverlapPair:
    """A pairwise overlap report between two artifacts."""

    artifact_a: str
    artifact_b: str
    overlap_score: int  # 0-100
    rationale: str
    recommendation: OverlapRecommendation

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["recommendation"] = self.recommendation.value
        return d


# ---------------------------------------------------------------------------
# Token cost
# ---------------------------------------------------------------------------

@dataclass
class TokenCostStatic:
    """Static token cost estimate for one artifact."""

    artifact_name: str
    estimated_tokens: int
    size_bytes: int
    high_cost: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeTokenMetrics:
    """Runtime token usage for one artifact (if logs are available)."""

    artifact_name: str
    invocations: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    retries: int = 0
    failures: int = 0
    avg_runtime_ms: float = 0.0
    failure_adjusted_cost: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Responsibility
# ---------------------------------------------------------------------------

@dataclass
class ResponsibilityReport:
    """Coherence report for one skill."""

    artifact_name: str
    responsibility_score: int  # 0-100
    flag: ResponsibilityFlag
    rationale: str
    responsibilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["flag"] = self.flag.value
        return d


# ---------------------------------------------------------------------------
# ROI
# ---------------------------------------------------------------------------

@dataclass
class ScorecardEntry:
    """ROI score and decision for one skill."""

    artifact_name: str
    roi_score: int  # 0-100
    decision: Decision
    rationale: str
    reuse_frequency: int = 0
    estimated_tokens: int = 0
    output_structure_quality: int = 0
    failure_rate: float = 0.0
    semantic_uniqueness: int = 0
    benchmark_pass_rate: float = 0.0
    business_criticality: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["decision"] = self.decision.value
        return d


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

@dataclass
class Recommendation:
    """A single governance recommendation."""

    recommendation_id: str
    affected_artifacts: list[str]
    decision: Decision
    priority: int  # 1 (highest) - 5 (lowest)
    rationale: str
    evidence: dict[str, Any] = field(default_factory=dict)
    estimated_token_impact: int = 0
    estimated_quality_impact: int = 0
    implementation_effort: str = "M"  # XS/S/M/L/XL
    risk: str = "low"
    ci_impact: str = "none"
    proposed_next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["decision"] = self.decision.value
        return d


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """A single benchmark result for an artifact."""

    artifact_name: str
    benchmark_name: str
    passed: bool
    score: float
    minimum_score: float
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Waiver
# ---------------------------------------------------------------------------

@dataclass
class Waiver:
    """An explicit waiver for a CI-blocking finding."""

    waiver_id: str
    finding_id: str
    owner: str
    expiration_date: str  # ISO date
    rationale: str
    approved_by: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_valid(self) -> bool:
        """Return True if the waiver has the required fields filled in."""
        return bool(
            self.waiver_id
            and self.finding_id
            and self.owner
            and self.expiration_date
            and self.rationale
            and self.approved_by
        )


# ---------------------------------------------------------------------------
# Pipeline results
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """The aggregated result of a full pipeline run."""

    inventory: list[SkillArtifact] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    dependency_graph: DependencyGraph | None = None
    overlap_pairs: list[OverlapPair] = field(default_factory=list)
    token_costs: list[TokenCostStatic] = field(default_factory=list)
    runtime_metrics: list[RuntimeTokenMetrics] = field(default_factory=list)
    responsibility: list[ResponsibilityReport] = field(default_factory=list)
    scorecards: list[ScorecardEntry] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    benchmark_results: list[BenchmarkResult] = field(default_factory=list)
    rewrites: dict[str, str] = field(default_factory=dict)  # artifact_name -> proposed body
    waivers: list[Waiver] = field(default_factory=list)
    ci_blocking_count: int = 0
    ci_passed: bool = True
    health_score: int = 0
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = {
            "inventory": [a.to_dict() for a in self.inventory],
            "findings": [f.to_dict() for f in self.findings],
            "dependency_graph": self.dependency_graph.to_dict() if self.dependency_graph else None,
            "overlap_pairs": [p.to_dict() for p in self.overlap_pairs],
            "token_costs": [t.to_dict() for t in self.token_costs],
            "runtime_metrics": [r.to_dict() for r in self.runtime_metrics],
            "responsibility": [r.to_dict() for r in self.responsibility],
            "scorecards": [s.to_dict() for s in self.scorecards],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "benchmark_results": [b.to_dict() for b in self.benchmark_results],
            "rewrites": self.rewrites,
            "waivers": [w.to_dict() for w in self.waivers],
            "ci_blocking_count": self.ci_blocking_count,
            "ci_passed": self.ci_passed,
            "health_score": self.health_score,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }
        return d
