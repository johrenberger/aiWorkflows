from __future__ import annotations

from pathlib import Path

from mutationctl.detection.java_tools import detect_pit
from mutationctl.detection.javascript_tools import detect_stryker
from mutationctl.detection.language import detect_languages
from mutationctl.detection.python_tools import detect_mutmut
from mutationctl.models import Blocker, MutationToolEvidence, ToolDetectionResult


def detect_mutation_tools(
    repo_path: str | Path,
    store=None,
    allow_dependency_install: bool = False,
) -> ToolDetectionResult:
    root = Path(repo_path)
    detectors = [detect_mutmut, detect_stryker, detect_pit]
    evidence = [result for detector in detectors if (result := detector(root)) is not None]
    if evidence:
        result = ToolDetectionResult(evidence[0].tool_name, evidence[0].ecosystem, "PASS", evidence)
    else:
        languages = detect_languages(root)
        ecosystem = languages[0].language if languages else None
        missing = MutationToolEvidence(
            "none",
            ecosystem or "unknown",
            False,
            not allow_dependency_install,
            None,
            [],
            [item for language in languages for item in language.evidence],
            "No supported mutation tool was found in local project evidence",
        )
        result = ToolDetectionResult(None, ecosystem, "BLOCKED", [missing])
        if store is not None:
            store.record_blocker(
                Blocker(
                    "MUTATION_TOOL_NOT_FOUND",
                    "BLOCKED",
                    missing.blocker_reason or "Mutation tool unavailable",
                    ", ".join(missing.evidence) or str(root),
                )
            )
    if store is not None:
        store.record_tool_detection(result)
    return result
