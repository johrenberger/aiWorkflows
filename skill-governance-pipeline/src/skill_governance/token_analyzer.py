"""Token analyzer: static + runtime token cost analysis.

Implements Core Requirement 7.

Static analysis uses the 4-chars-per-token heuristic.

Runtime analysis ingests logs that contain:
- input tokens
- output tokens
- total tokens
- retries
- failures
- runtime
- invoking workflow

Output:
- output/token_cost_static.json
- output/runtime_token_metrics.json
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import RuntimeTokenMetrics, SkillArtifact, TokenCostStatic
from .utils import write_json


def analyze_static(artifacts: list[SkillArtifact], high_cost_threshold: int = 8000) -> list[TokenCostStatic]:
    """Compute static token costs and flag high-cost artifacts."""
    out: list[TokenCostStatic] = []
    for a in artifacts:
        out.append(
            TokenCostStatic(
                artifact_name=a.name,
                estimated_tokens=a.estimated_tokens,
                size_bytes=a.size_bytes,
                high_cost=a.estimated_tokens >= high_cost_threshold,
            )
        )
    return out


def analyze_runtime(log_paths: list[Path]) -> list[RuntimeTokenMetrics]:  # pragma: no cover - stub
    """Ingest runtime token metrics from log files.

    Phase 1 returns an empty list. Phase 2 will define a log
    format (JSONL) and parse invocations, tokens, retries, etc.
    """
    return []


def write_static(costs: list[TokenCostStatic], output_dir: Path) -> Path:
    """Write the static token costs to disk."""
    p = output_dir / "token_cost_static.json"
    write_json(p, [c.to_dict() for c in costs])
    return p


def write_runtime(metrics: list[RuntimeTokenMetrics], output_dir: Path) -> Path:
    """Write the runtime token metrics to disk."""
    p = output_dir / "runtime_token_metrics.json"
    write_json(p, [m.to_dict() for m in metrics])
    return p
