from __future__ import annotations

from pathlib import Path


BOUNDARY_TOKENS = {"controller", "route", "api", "client", "repository", "dao", "gateway", "adapter", "middleware", "http", "db", "database", "filesystem", "file", "socket", "auth", "payment", "billing", "queue", "event"}


def recommend_test_type(source_path: str, source_text: str = "") -> str:
    lower = f"{source_path}\n{source_text}".lower()
    if any(token in lower for token in BOUNDARY_TOKENS):
        return "component/integration"
    collaborators = sum(token in lower for token in ("mock", "stub", "spy", "repository", "service", "client"))
    if collaborators > 2:
        return "component/integration"
    if "middleware" in lower or "framework" in lower or "lifecycle" in lower:
        return "component/integration"
    return "unit"


def conventions_summary(language: str, source_path: str) -> str:
    if language == "java":
        return "Prefer JUnit 5 with Mockito and AssertJ; follow existing src/test/java package structure."
    if language == "javascript":
        return "Prefer Jest or Vitest; co-locate tests with *.test or *.spec naming unless repo conventions say otherwise."
    if language == "python":
        return "Prefer pytest; use tests/test_*.py or package-local test files based on repository style."
    return f"Follow existing {language} test style in the repository."

