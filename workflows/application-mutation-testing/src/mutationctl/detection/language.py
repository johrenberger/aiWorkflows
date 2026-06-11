from __future__ import annotations

from pathlib import Path

from mutationctl.models import LanguageDetectionResult

LANGUAGE_MARKERS = {
    "python": ({"pyproject.toml", "requirements.txt", "requirements-dev.txt", "setup.cfg", "tox.ini"}, {".py"}),
    "javascript": ({"package.json"}, {".js", ".jsx", ".ts", ".tsx"}),
    "java": ({"pom.xml", "build.gradle"}, {".java"}),
    "dotnet": (set(), {".cs"}),
    "go": ({"go.mod"}, {".go"}),
}


def detect_languages(repo_path: str | Path) -> list[LanguageDetectionResult]:
    root = Path(repo_path)
    results = []
    for language, (markers, extensions) in LANGUAGE_MARKERS.items():
        evidence = sorted(marker for marker in markers if (root / marker).is_file())
        source_files = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions
        )
        evidence.extend(source_files[:5])
        if evidence:
            marker_count = sum(1 for item in evidence if item in markers)
            confidence = 1.0 if marker_count and source_files else 0.7
            results.append(LanguageDetectionResult(language, confidence, evidence))
    return sorted(results, key=lambda item: (-item.confidence, item.language))
