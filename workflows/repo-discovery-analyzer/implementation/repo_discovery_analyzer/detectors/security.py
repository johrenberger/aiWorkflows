from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, redact_text, safe_read_text, short_snippet
from ..model import FileRecord


SECURITY_PATTERNS = (
    ("authentication", "Spring Security", "medium", re.compile(r"\bSpringSecurity\b|\bspring-security\b|\bSecurityFilterChain\b")),
    ("authentication", "Passport.js", "medium", re.compile(r"\bpassport(?:\.[A-Za-z]+)?\b", re.I)),
    ("authentication", "authentication handler", "medium", re.compile(r"\b(?:requireAuth|authenticate|verifyPassword|loginHandler)\b")),
    ("authorization", "authorization check", "medium", re.compile(r"\b(?:authorize|requireRole|hasRole|hasAuthority|accessControl|isAdmin)\b", re.I)),
    ("token/session", "JWT", "medium", re.compile(r"\b(?:jwt|jsonwebtoken|jose)\b", re.I)),
    ("token/session", "session", "medium", re.compile(r"\b(?:express-session|sessionMiddleware|req\.session)\b", re.I)),
    ("oauth/oidc/saml", "OAuth/OIDC/SAML", "medium", re.compile(r"\b(?:oauth2?|oidc|saml)\b", re.I)),
    ("cors/csrf", "CORS", "low", re.compile(r"(?:\bcors\s*\(|\bCorsConfiguration\b|\ballowedOrigins\b)", re.I)),
    ("cors/csrf", "CSRF", "low", re.compile(r"(?:\bcsrf\s*\(|\bcsrfToken\b|\bcsrfProtection\b)", re.I)),
    ("input validation", "input validation", "low", re.compile(r"\b(?:joi|zod|yup|express-validator|@Valid|@Validated)\b", re.I)),
    ("tls/https", "TLS/HTTPS", "low", re.compile(r"\b(?:https\.createServer|ssl_certificate|server\.ssl\.)\b", re.I)),
)

HASH_PATTERNS = (
    ("bcrypt", re.compile(r"\bbcrypt(?:js)?\b", re.I)),
    ("argon2", re.compile(r"\bargon2\b", re.I)),
    ("scrypt", re.compile(r"\bscrypt\b", re.I)),
    ("pbkdf2", re.compile(r"\bpbkdf2\b", re.I)),
)

QUOTED_SECRET_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b(api[_-]?key|secret|token|password|passwd|private[_-]?key|
       client[_-]?secret|aws_secret_access_key|refresh[_-]?token)\b
    \s*[:=]\s*
    ["']([^"']{8,})["']
    """
)
UNQUOTED_CONFIG_SECRET_RE = re.compile(
    r"""(?ix)
    ^\s*(?:-\s*)?
    (api[_-]?key|secret|token|password|passwd|private[_-]?key|
       client[_-]?secret|aws_secret_access_key|refresh[_-]?token)\b
    \s*:\s*
    ([A-Za-z0-9_./+=-]{8,})
    """
)

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".go", ".rs",
    ".cs", ".rb", ".php", ".scala", ".sh", ".ps1", ".sql", ".html",
}
CONFIG_EXTENSIONS = {".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".env"}
CONFIG_NAMES = {
    "package.json", "pom.xml", "build.gradle", "build.gradle.kts", "dockerfile",
    "containerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml",
    "compose.yaml",
}
PLACEHOLDER_VALUES = {
    "changeme", "change-me", "example", "placeholder", "test-secret", "test-token",
    "your-secret", "your-token", "dummy", "sample",
}


def detect_security(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    findings: list[dict] = []
    total_count = 0

    def add(finding: dict) -> None:
        nonlocal total_count
        total_count += 1
        if len(findings) < DEFAULT_MAX_SUMMARY_ITEMS:
            findings.append(finding)

    for record in records:
        if record.skipped or not _is_security_evidence(record):
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        lines = text.splitlines()
        for category, signal, severity, pattern in SECURITY_PATTERNS:
            match_line = _matching_line(lines, pattern)
            if match_line:
                add(_finding(category, signal, severity, record, match_line))
        for signal, pattern in HASH_PATTERNS:
            match_line = _matching_line(lines, pattern)
            if match_line:
                add(_finding("password hashing", signal, "low", record, match_line))
        for line in lines:
            secret_match = QUOTED_SECRET_ASSIGNMENT_RE.search(line)
            if not secret_match and Path(record.path).suffix.lower() in CONFIG_EXTENSIONS:
                secret_match = UNQUOTED_CONFIG_SECRET_RE.search(line)
            if secret_match and not _is_placeholder(secret_match.group(2)):
                add(
                    {
                        "category": "secrets-like pattern",
                        "signal": f"possible hardcoded {secret_match.group(1).lower()}",
                        "severity": "high",
                        "source_file": record.path,
                        "github_url": record.github_url,
                        "redacted_snippet": redact_text(short_snippet(line) or ""),
                        "confidence": "medium",
                    }
                )
                break
        env_pattern = re.compile(r"\b(?:os\.environ|os\.getenv|process\.env|System\.getenv)\b")
        if Path(record.path).suffix.lower() in CONFIG_EXTENSIONS:
            env_pattern = re.compile(
                r"\b(?:os\.environ|os\.getenv|process\.env|System\.getenv)\b|\$\{[A-Z_][A-Z0-9_]*\}"
            )
        env_line = _matching_line(lines, env_pattern)
        if env_line:
            add(_finding("environment variable usage", "environment variables", "info", record, env_line))

    return {
        "security_signals": sorted(findings, key=lambda x: (x["category"], x["source_file"], x["signal"])),
        "security_signals_total": total_count,
        "security_signals_truncated": total_count > len(findings),
    }


def _finding(category: str, signal: str, severity: str, record: FileRecord, text: str) -> dict:
    return {
        "category": category,
        "signal": signal,
        "severity": severity,
        "source_file": record.path,
        "github_url": record.github_url,
        "redacted_snippet": redact_text(short_snippet(text) or ""),
        "confidence": "medium",
    }


def _is_security_evidence(record: FileRecord) -> bool:
    path = Path(record.path)
    parts = {part.lower() for part in path.parts}
    if record.role_guess == "test" or parts.intersection({"docs", "_docs", "documentation", "coverage"}):
        return False
    if path.suffix.lower() in SOURCE_EXTENSIONS | CONFIG_EXTENSIONS:
        return True
    return path.name.lower() in CONFIG_NAMES


def _matching_line(lines: list[str], pattern: re.Pattern[str]) -> str | None:
    for line in lines:
        if pattern.search(line):
            return line
    return None


def _is_placeholder(value: str) -> bool:
    lowered = value.lower().strip()
    return (
        lowered in PLACEHOLDER_VALUES
        or lowered.startswith(("test-", "example-", "dummy-", "sample-", "your-"))
        or "${" in value
        or lowered.startswith(("process.env", "os.environ", "system.getenv"))
    )
