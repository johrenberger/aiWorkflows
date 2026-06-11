from __future__ import annotations

from pathlib import Path

from mutationctl.models import CoverageFileSummary, MutationTarget, TargetSelectionResult
from mutationctl.targeting.eligibility import LANGUAGE_EXTENSIONS, exclusion_reason
from mutationctl.targeting.scorer import complexity_score, coverage_readiness, target_score


def select_targets(
    repo_path: str | Path,
    language: str,
    tool_name: str | None,
    coverage_files: list[CoverageFileSummary] | None = None,
    max_target_files: int = 5,
    fallback_allowed: bool = True,
    store=None,
) -> TargetSelectionResult:
    root = Path(repo_path)
    coverage_by_file = {item.source_file.replace("\\", "/"): item for item in coverage_files or []}
    candidates = []
    excluded = []
    supported_extensions = LANGUAGE_EXTENSIONS.get(language, set())

    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        reason = exclusion_reason(relative, language)
        if reason:
            if path.suffix.lower() in supported_extensions:
                excluded.append(_excluded_target(relative, language, reason))
            continue
        if tool_name is None:
            excluded.append(_excluded_target(relative, language, "No mutation tool available for language"))
            continue
        coverage_item = coverage_by_file.get(relative)
        line_coverage = coverage_item.line_coverage if coverage_item else None
        readiness = coverage_readiness(line_coverage, fallback_allowed)
        if line_coverage is None and not fallback_allowed:
            excluded.append(_excluded_target(relative, language, "Coverage unavailable and fallback disabled"))
            continue
        complexity = complexity_score(path.read_text(encoding="utf-8", errors="replace"))
        rationale = (
            f"Coverage {line_coverage:.1f}% and deterministic complexity score {complexity:.2f}"
            if line_coverage is not None
            else f"Coverage unavailable; fallback readiness applied with complexity score {complexity:.2f}"
        )
        candidates.append(
            MutationTarget(
                relative,
                language,
                target_score(readiness, complexity),
                "PASS",
                rationale,
                readiness,
                complexity,
                100.0,
                False,
            )
        )

    candidates.sort(key=lambda item: (-item.score, item.source_file))
    for target in candidates[:max_target_files]:
        target.selected = True
    selected = candidates[:max_target_files]
    excluded.extend(candidates[max_target_files:])
    for target in candidates[max_target_files:]:
        target.eligibility_status = "DEFERRED"
        target.rationale = f"Deferred by max_target_files={max_target_files} cap"

    result = TargetSelectionResult(selected, excluded, "PASS" if selected else "NOT_RUN")
    if store is not None:
        store.record_targets([*selected, *excluded])
    return result


def _excluded_target(source_file: str, language: str, rationale: str) -> MutationTarget:
    return MutationTarget(source_file, language, 0.0, "EXCLUDED", rationale, 0.0, 0.0, 0.0, False)
