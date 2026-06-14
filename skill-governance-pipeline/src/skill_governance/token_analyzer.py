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

Note:
    The canonical implementation of runtime metrics ingestion lives in
    `runtime_metrics.ingest()`. The `analyze_runtime()` function here is
    a thin delegating wrapper kept for backward compatibility. It emits
    a DeprecationWarning and forwards to `runtime_metrics.ingest()`.
    New code should call `runtime_metrics.ingest()` directly.
"""
from __future__ import annotations

import json
import warnings
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


def analyze_runtime(log_paths: list[Path]) -> list[RuntimeTokenMetrics]:
    """Ingest runtime token metrics from log files.

    .. deprecated::
        Use :func:`skill_governance.runtime_metrics.ingest` instead.
        This wrapper is kept for backward compatibility and will be
        removed in a future release.

    Phase 1 returned an empty list. Phase 2 added the real
    implementation in :mod:`skill_governance.runtime_metrics`; this
    function now delegates to that canonical implementation.
    """
    warnings.warn(
        "token_analyzer.analyze_runtime() is deprecated; "
        "use skill_governance.runtime_metrics.ingest() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from .runtime_metrics import ingest
    return ingest(log_paths)


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
