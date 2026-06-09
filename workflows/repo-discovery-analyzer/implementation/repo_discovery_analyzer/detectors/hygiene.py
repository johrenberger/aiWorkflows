from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, redact_text, safe_read_text, short_snippet
from ..model import FileRecord


KEYWORDS = ("todo", "fixme", "hack", "xxx", "techdebt", "deprecated", "@deprecated")
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".go", ".rs",
    ".cs", ".rb", ".php", ".scala", ".sh", ".ps1", ".sql", ".html",
}
CONFIG_EXTENSIONS = {".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".env"}
URL_RE = re.compile(r"https?://[^\s'\"<>]+")
QUOTED_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b(api[_-]?key|secret|token|password|passwd|private[_-]?key|
       client[_-]?secret|aws_secret_access_key|refresh[_-]?token)\b
    \s*[:=]\s*
    ["']([^"']{8,})["']
    """
)
UNQUOTED_CONFIG_CREDENTIAL_RE = re.compile(
    r"""(?ix)
    ^\s*(?:-\s*)?
    (api[_-]?key|secret|token|password|passwd|private[_-]?key|
       client[_-]?secret|aws_secret_access_key|refresh[_-]?token)\b
    \s*:\s*
    ([A-Za-z0-9_./+=-]{8,})
    """
)


def detect_hygiene(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    total_count = 0

    def add(finding: dict) -> None:
        nonlocal total_count
        total_count += 1
        if len(findings) < DEFAULT_MAX_SUMMARY_ITEMS:
            findings.append(finding)

    manager_files = [r.path for r in records if Path(r.path).name in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "pom.xml", "build.gradle", "build.gradle.kts"}]
    if len({Path(p).name for p in manager_files if Path(p).name}) > 1:
        add(
            {
                "type": "package-manager-conflict",
                "path": ", ".join(sorted({Path(p).name for p in manager_files})),
                "github_url": None,
                "line_number": None,
                "redacted_snippet": None,
                "impact_hint": "multiple package managers can make dependency resolution ambiguous",
                "confidence": "medium",
            }
        )

    for record in records:
        if record.role_guess == "source" and record.line_count and record.line_count > 1000:
            add(_finding("large-file", record.path, record.github_url, None, None, "large file may be hard to review", "high"))
        if not record.skipped and _is_hygiene_evidence(record):
            text, _ = safe_read_text(repo_path / record.path)
            if not text:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                lowered = line.lower()
                if record.role_guess != "test" and _has_marker(lowered):
                    add(
                        {
                            "type": "marker",
                            "path": record.path,
                            "github_url": record.github_url,
                            "line_number": lineno,
                            "redacted_snippet": redact_text(short_snippet(line) or ""),
                            "impact_hint": "marker indicates unfinished or risky code",
                            "confidence": "high",
                        }
                    )
                url_match = URL_RE.search(line)
                if record.role_guess != "test" and url_match and _is_actionable_url(url_match.group(0), line):
                    add(
                        _finding(
                            "hardcoded-url",
                            record.path,
                            record.github_url,
                            lineno,
                            line,
                            "hardcoded external URL may need environment-specific configuration",
                            "medium",
                        )
                    )
                credential_match = QUOTED_CREDENTIAL_ASSIGNMENT_RE.search(line)
                if not credential_match and Path(record.path).suffix.lower() in CONFIG_EXTENSIONS:
                    credential_match = UNQUOTED_CONFIG_CREDENTIAL_RE.search(line)
                if (
                    record.role_guess != "test"
                    and credential_match
                    and not _is_placeholder(credential_match.group(2))
                ):
                    add(
                        _finding(
                            "credential-like-key",
                            record.path,
                            record.github_url,
                            lineno,
                            line,
                            "possible hardcoded credential requires review",
                            "high",
                        )
                    )
    return {
        "hygiene_findings": sorted(findings, key=lambda x: (x["type"], x["path"], x.get("line_number") or 0)),
        "hygiene_findings_total": total_count,
        "hygiene_findings_truncated": total_count > len(findings),
    }


def _finding(
    type_: str,
    path: str,
    github_url: str | None,
    line_number: int | None,
    snippet: str | None,
    impact_hint: str,
    confidence: str,
) -> dict:
    return {
        "type": type_,
        "path": path,
        "github_url": github_url,
        "line_number": line_number,
        "redacted_snippet": redact_text(short_snippet(snippet) or "") if snippet else None,
        "impact_hint": impact_hint,
        "confidence": confidence,
    }


def _is_hygiene_evidence(record: FileRecord) -> bool:
    path = Path(record.path)
    parts = {part.lower() for part in path.parts}
    if parts.intersection({"docs", "_docs", "documentation", "coverage"}):
        return False
    return path.suffix.lower() in SOURCE_EXTENSIONS | CONFIG_EXTENSIONS


def _has_marker(line: str) -> bool:
    return any(re.search(rf"\b{re.escape(keyword.lstrip('@'))}\b", line) for keyword in KEYWORDS)


def _is_actionable_url(url: str, line: str) -> bool:
    lowered = url.lower().rstrip(".,);]")
    if any(host in lowered for host in ("localhost", "127.0.0.1", "github.com", "schemas.", "json-schema.org")):
        return False
    if any(token in line for token in ("process.env", "os.environ", "System.getenv", "${")):
        return False
    return True


def _is_placeholder(value: str) -> bool:
    lowered = value.lower().strip()
    return (
        lowered in {"changeme", "change-me", "example", "placeholder", "dummy", "sample"}
        or lowered.startswith(("test-", "example-", "dummy-", "sample-", "your-"))
        or "${" in value
        or lowered.startswith(("process.env", "os.environ", "system.getenv"))
    )
