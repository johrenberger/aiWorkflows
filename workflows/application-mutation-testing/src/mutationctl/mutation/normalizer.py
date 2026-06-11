from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from mutationctl.models import NormalizedMutant, NormalizedMutationResult

COUNT_PATTERN = re.compile(r"^(Killed|Survived|Timeout):\s*(\d+)\s*$", re.MULTILINE)
SURVIVOR_PATTERN = re.compile(
    r"^-\s+(.+?):(\d+)\s+(\S+)\s+(.+?)\s+->\s+(.+)$",
    re.MULTILINE,
)

STATUS_MAP = {
    "killed": "KILLED",
    "survived": "SURVIVED",
    "timeout": "TIMEOUT",
    "ignored": "IGNORED",
    "nocoverage": "NO_COVERAGE",
    "no_coverage": "NO_COVERAGE",
    "error": "ERROR",
}


def normalize_mutation_report(tool_name: str, report_path: str | Path, store=None) -> NormalizedMutationResult:
    path = Path(report_path)
    if tool_name == "mutmut":
        result = _normalize_mutmut(path)
    elif tool_name == "stryker":
        result = _normalize_stryker(path)
    elif tool_name == "pit":
        result = _normalize_pit(path)
    else:
        result = NormalizedMutationResult(tool_name, "PARTIAL", None, None, None, None, None, str(path), [])
    if store is not None:
        store.record_normalized_mutation_result(result)
    return result


def _normalize_mutmut(path: Path) -> NormalizedMutationResult:
    text = path.read_text(encoding="utf-8")
    counts = {name.lower(): int(value) for name, value in COUNT_PATTERN.findall(text)}
    mutants = [
        NormalizedMutant(
            f"mutmut-{index}",
            source_file,
            int(line),
            operator,
            original,
            mutated,
            "SURVIVED",
            match.group(0),
        )
        for index, match in enumerate(SURVIVOR_PATTERN.finditer(text), 1)
        for source_file, line, operator, original, mutated in [match.groups()]
    ]
    killed = counts.get("killed")
    survived = counts.get("survived")
    score = _score(killed, survived)
    return NormalizedMutationResult(
        "mutmut",
        "PASS" if killed is not None and survived is not None else "PARTIAL",
        killed,
        survived,
        counts.get("timeout"),
        None,
        score,
        str(path),
        mutants,
    )


def _normalize_stryker(path: Path) -> NormalizedMutationResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutants = []
    for source_file, file_data in data.get("files", {}).items():
        for raw in file_data.get("mutants", []):
            mutants.append(
                NormalizedMutant(
                    str(raw.get("id", "")),
                    source_file,
                    raw.get("location", {}).get("start", {}).get("line"),
                    raw.get("mutatorName", "unknown"),
                    None,
                    raw.get("replacement"),
                    STATUS_MAP.get(str(raw.get("status", "")).lower(), "UNKNOWN"),
                    json.dumps(raw, sort_keys=True),
                )
            )
    return _from_mutants("stryker", path, mutants)


def _normalize_pit(path: Path) -> NormalizedMutationResult:
    mutants = []
    for index, node in enumerate(ET.parse(path).getroot().findall("mutation"), 1):
        status = STATUS_MAP.get(node.attrib.get("status", "").lower(), "UNKNOWN")
        mutants.append(
            NormalizedMutant(
                f"pit-{index}",
                node.findtext("sourceFile") or "unknown",
                int(node.findtext("lineNumber")) if node.findtext("lineNumber") else None,
                node.findtext("mutator") or "unknown",
                node.findtext("description"),
                None,
                status,
                ET.tostring(node, encoding="unicode"),
            )
        )
    return _from_mutants("pit", path, mutants)


def _from_mutants(tool_name: str, path: Path, mutants: list[NormalizedMutant]) -> NormalizedMutationResult:
    killed = sum(mutant.status == "KILLED" for mutant in mutants)
    survived = sum(mutant.status == "SURVIVED" for mutant in mutants)
    timeout = sum(mutant.status == "TIMEOUT" for mutant in mutants)
    ignored = sum(mutant.status == "IGNORED" for mutant in mutants)
    return NormalizedMutationResult(
        tool_name, "PASS", killed, survived, timeout, ignored, _score(killed, survived), str(path), mutants
    )


def _score(killed: int | None, survived: int | None) -> float | None:
    if killed is None or survived is None or killed + survived == 0:
        return None
    return round(killed / (killed + survived) * 100, 2)
