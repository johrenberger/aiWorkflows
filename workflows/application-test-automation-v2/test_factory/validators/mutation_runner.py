from __future__ import annotations

from pathlib import Path

from ..analyzers.mutation_analyzer import mutation_candidates_from_scores
from ..models import MutationToolDetection


def discover_mutation_candidates(score_rows: list[dict[str, object]], high_risk_only: bool = True) -> list[dict[str, object]]:
    return mutation_candidates_from_scores(score_rows, high_risk_only=high_risk_only)


def mutation_command_for_detection(detection: MutationToolDetection, repo_root: str | Path) -> list[str]:
    if detection.available and detection.command:
        return detection.command
    return []

