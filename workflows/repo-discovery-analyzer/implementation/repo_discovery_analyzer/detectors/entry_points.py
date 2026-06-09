from __future__ import annotations

from pathlib import Path

from ..io_utils import safe_read_text, short_snippet
from ..model import FileRecord


def detect_entry_points(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    files = {r.path: r for r in records}
    entries: list[dict] = []

    for record in records:
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        if record.path.endswith(".java") and "public static void main" in text:
            entries.append(_entry("java-main", record.path, files, "Java", "high", "main"))
        if record.path.endswith(".java") and "@SpringBootApplication" in text:
            entries.append(_entry("spring-boot-app", record.path, files, "Spring Boot", "high", "application"))
        if record.path in {"app.py", "main.py", "__main__.py"} or text.startswith("if __name__ == \"__main__\""):
            entries.append(_entry("python-entry", record.path, files, "Python", "medium", "main"))
        if record.path.endswith(("index.ts", "index.tsx", "index.js", "index.jsx")):
            entries.append(_entry("frontend-entry", record.path, files, "frontend", "medium", "index"))
        if record.path.endswith(("server.js", "server.ts", "app.js", "app.ts")):
            entries.append(_entry("server-entry", record.path, files, "Node.js", "medium", "server"))

    package_json = repo_path / "package.json"
    if package_json.exists():
        text, _ = safe_read_text(package_json)
        if text:
            for line in text.splitlines():
                if '"start"' in line or '"dev"' in line or '"build"' in line:
                    entries.append(
                        {
                            "type": "script",
                            "path": "package.json",
                            "github_url": files.get("package.json").github_url if "package.json" in files else None,
                            "handler": short_snippet(line),
                            "framework": "package.json script",
                            "confidence": "medium",
                        }
                    )

    entries = sorted(entries, key=lambda x: (x.get("type", ""), x.get("path", ""), x.get("handler", "")))
    return {"entry_points": entries}


def _entry(entry_type: str, path: str, files: dict[str, FileRecord], framework: str, confidence: str, handler: str) -> dict:
    return {
        "type": entry_type,
        "path": path,
        "github_url": files[path].github_url if path in files else None,
        "handler": handler,
        "framework": framework,
        "confidence": confidence,
    }

