"""Heuristic public-method extractor used when no coverage data is available.

When v2 doesn't have JaCoCo or coverage.py data (e.g. a fresh repo), the
work-item spec for each source file currently lists `Uncovered lines: none`
which is not actionable for the LLM. This module extracts a list of
public methods (or top-level functions) from the source so the LLM has
something concrete to write tests against.

The extractor is intentionally simple: regex-based, language-specific.
It does NOT do full AST parsing. The goal is "give the LLM a starting
list of method names" not "guarantee 100% correct method extraction."

Used by: orchestrator (when constructing WorkItemRecords with empty
uncovered_lines and no coverage data available).
"""
from __future__ import annotations

import re
from pathlib import Path


# Java: matches public method declarations.
# Looks for: public [static] [final] [synchronized] <Type> <name>(...) {
# Avoids matching comments, annotations, and multi-line signatures by
# requiring the opening brace on the same line.
_JAVA_PUBLIC_METHOD = re.compile(
    r"^\s*public\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?"
    r"(?:<[^>]+>\s+)?"  # generics
    r"[\w<>\[\],\s]+?\s+"
    r"(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
    re.MULTILINE,
)


# Java: package-level public class/interface declarations
_JAVA_PUBLIC_CLASS = re.compile(
    r"^\s*public\s+(?:abstract\s+|final\s+)?(?:class|interface|enum)\s+(\w+)",
    re.MULTILINE,
)


# Python: matches top-level function definitions (not methods).
# Looks for: def name(...):
_PYTHON_TOP_LEVEL_FUNC = re.compile(
    r"^(?:def|async\s+def)\s+(\w+)\s*\(",
    re.MULTILINE,
)


# Python: matches class definitions and their methods.
# This is a 2-step match: find "class X" and within, find "def method".
_PYTHON_CLASS_DEF = re.compile(
    r"^class\s+(\w+)(?:\([^)]*\))?\s*:",
    re.MULTILINE,
)


# JavaScript/TypeScript: matches public class methods.
# Two patterns:
# 1. ES6 class method: `name(...) {`
# 2. Object literal method: `name : function(...) {` (common in older JS)
_JS_CLASS_METHOD = re.compile(
    r"^\s*(?:async\s+)?(?:static\s+)?(\w+)\s*(?:\([^)]*\))?\s*(?:[:=]\s*(?:async\s+)?function\s*)?(?:\([^)]*\))?\s*\{",
    re.MULTILINE,
)


def extract_public_signatures(source_path: str, language: str, max_chars: int = 50000) -> list[str]:
    """Return a list of public method/function signatures for the given source.

    Returns an empty list if the file can't be read or language is unsupported.
    Used as a fallback when coverage data is missing — gives the LLM something
    concrete to write tests for instead of "Uncovered lines: none".
    """
    try:
        text = Path(source_path).read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []
    text = text[:max_chars]

    if language == "java":
        return _extract_java(text)
    if language == "python":
        return _extract_python(text)
    if language in ("javascript", "groovy"):
        return _extract_js_or_groovy(text)
    return []


def _extract_java(text: str) -> list[str]:
    """Extract public method names from a Java source."""
    methods = _JAVA_PUBLIC_METHOD.findall(text)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for m in methods:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out[:50]  # cap at 50 methods per source


def _extract_python(text: str) -> list[str]:
    """Extract top-level functions and public class methods."""
    out: list[str] = []
    # Find top-level functions
    for m in _PYTHON_TOP_LEVEL_FUNC.findall(text):
        if not m.startswith("_"):  # public convention
            out.append(m)
    # Find class methods
    for cls_match in _PYTHON_CLASS_DEF.finditer(text):
        cls_name = cls_match.group(1)
        # Find the class body
        cls_start = cls_match.end()
        # Get text up to the next class or end of file
        next_cls = _PYTHON_CLASS_DEF.search(text, cls_start)
        cls_end = next_cls.start() if next_cls else len(text)
        cls_body = text[cls_start:cls_end]
        # Find methods in class body (def at indent level >= 4 spaces)
        for method_match in re.finditer(r"^    (?:def|async\s+def)\s+(\w+)\s*\(", cls_body, re.MULTILINE):
            m = method_match.group(1)
            if not m.startswith("_"):
                out.append(f"{cls_name}.{m}")
    # Deduplicate
    seen = set()
    deduped = []
    for m in out:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped[:50]


def _extract_js_or_groovy(text: str) -> list[str]:
    """Extract likely public method names from JS/TS/Groovy.

    This is a heuristic — the regex matches any "name(" pattern at
    start of line. False positives are possible (e.g. if-blocks),
    but better than an empty list.
    """
    out = []
    for m in _JS_CLASS_METHOD.findall(text):
        # Filter out JS keywords and short noise
        if m in {"if", "for", "while", "switch", "return", "function", "class"}:
            continue
        if len(m) <= 1:
            continue
        if m not in out:
            out.append(m)
    return out[:50]
