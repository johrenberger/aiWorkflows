"""Contract validation: enforce structured I/O contracts.

Implements Core Requirement 3.

Rules:
- Inputs must be structured.
- Outputs must define format and required fields.
- Avoid vague outputs like 'analysis', 'summary', 'report' without
  structure.
- Output contracts should prefer JSON, Markdown with required
  sections, or named artifacts.
"""
from __future__ import annotations

import re
from pathlib import Path

from .metadata_parser import parse_metadata
from .models import Finding, Severity

# Vague single-word outputs that should be flagged
VAGUE_OUTPUT_PATTERNS = [
    re.compile(r"^\s*(a|an|the)?\s*report\s*$", re.IGNORECASE),
    re.compile(r"^\s*(a|an|the)?\s*analysis\s*$", re.IGNORECASE),
    re.compile(r"^\s*(a|an|the)?\s*summary\s*$", re.IGNORECASE),
    re.compile(r"^\s*(a|an|the)?\s*review\s*$", re.IGNORECASE),
    re.compile(r"^\s*some\s+output\s*$", re.IGNORECASE),
    re.compile(r"^\s*analysis\s+results?\s*$", re.IGNORECASE),
    re.compile(r"^\s*tbd\s*$", re.IGNORECASE),
    re.compile(r"^\s*todo\s*$", re.IGNORECASE),
]

# Acceptable output format hints
ACCEPTABLE_OUTPUT_FORMATS = {"json", "markdown", "md", "yaml", "txt", "html", "csv", "named_artifact"}


def is_vague_output(outputs: object) -> bool:
    """Return True if the outputs description is a single vague word."""
    if outputs is None:
        return True
    if isinstance(outputs, str):
        s = outputs.strip()
        for pat in VAGUE_OUTPUT_PATTERNS:
            if pat.match(s):
                return True
        return False
    if isinstance(outputs, list):
        # A list of strings - check each entry
        for item in outputs:
            if isinstance(item, str):
                for pat in VAGUE_OUTPUT_PATTERNS:
                    if pat.match(item.strip()):
                        return True
        return False
    if isinstance(outputs, dict):
        # A dict: must have at least one of format/structure/sections
        if "format" not in outputs and "structure" not in outputs and "sections" not in outputs and "fields" not in outputs:
            return True
        return False
    return True


def has_structured_format_hint(outputs: object) -> bool:
    """Return True if outputs declare a structured format hint."""
    if isinstance(outputs, dict):
        fmt = outputs.get("format")
        if isinstance(fmt, str) and fmt.lower() in ACCEPTABLE_OUTPUT_FORMATS:
            return True
        # Even without explicit format, having fields/sections is enough
        if outputs.get("fields") or outputs.get("sections"):
            return True
        return False
    if isinstance(outputs, list):
        # A non-empty list of named outputs is structured
        return any(isinstance(item, dict) or (isinstance(item, str) and item.strip()) for item in outputs)
    return False


def validate_contract(artifact_name: str, path: Path) -> list[Finding]:
    """Run contract validation on a single artifact.

    Returns a list of findings (empty = pass).
    """
    metadata = parse_metadata(path)
    findings: list[Finding] = []

    if not metadata.has_structured_contracts():
        if metadata.inputs is None:
            findings.append(
                Finding(
                    finding_id=f"contract.inputs.missing.{artifact_name}",
                    artifact_name=artifact_name,
                    severity=Severity.BLOCKING,
                    category="contract",
                    message="Inputs contract is missing or unstructured.",
                    evidence={"path": str(path)},
                    suggestion="Define `inputs` as a list of named fields or a dict of field->type.",
                )
            )
        if metadata.outputs is None:
            findings.append(
                Finding(
                    finding_id=f"contract.outputs.missing.{artifact_name}",
                    artifact_name=artifact_name,
                    severity=Severity.BLOCKING,
                    category="contract",
                    message="Outputs contract is missing or unstructured.",
                    evidence={"path": str(path)},
                    suggestion="Define `outputs` with an explicit format (json/markdown/yaml) and a `fields` or `sections` list.",
                )
            )

    if is_vague_output(metadata.outputs):
        findings.append(
            Finding(
                finding_id=f"contract.outputs.vague.{artifact_name}",
                artifact_name=artifact_name,
                severity=Severity.BLOCKING,
                category="vague-output",
                message="Outputs contract is vague (e.g. 'a report', 'analysis', 'summary').",
                evidence={"outputs": str(metadata.outputs)},
                suggestion="Specify output format (json/markdown/yaml) and required fields or sections.",
            )
        )

    if not has_structured_format_hint(metadata.outputs):
        findings.append(
            Finding(
                finding_id=f"contract.outputs.format_hint_missing.{artifact_name}",
                artifact_name=artifact_name,
                severity=Severity.WARNING,
                category="contract",
                message="Outputs do not declare a structured format hint (json/markdown/yaml/...).",
                evidence={"outputs": str(metadata.outputs)},
                suggestion="Add `format: json` (or markdown/yaml) to the outputs contract.",
            )
        )

    return findings
