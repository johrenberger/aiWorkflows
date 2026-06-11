from __future__ import annotations

from pathlib import PurePosixPath

EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    "vendor",
    "generated",
    "__pycache__",
    "coverage",
}

LANGUAGE_EXTENSIONS = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".ts", ".tsx"},
    "java": {".java"},
    "dotnet": {".cs"},
    "go": {".go"},
}


def exclusion_reason(source_file: str, language: str) -> str | None:
    path = PurePosixPath(source_file)
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return "Excluded generated, vendor, build, dependency, or coverage path"
    if source_file.endswith((".min.js", ".map")):
        return "Excluded generated or source-map artifact"
    if path.suffix.lower() not in LANGUAGE_EXTENSIONS.get(language, set()):
        return f"Unsupported extension for {language}"
    return None
