from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from mutationctl.models import CoverageFileSummary


def parse_coverage_xml(path: Path) -> list[CoverageFileSummary]:
    root = ET.parse(path).getroot()
    summaries = []
    for class_node in root.findall(".//class"):
        source_file = class_node.attrib.get("filename")
        if not source_file:
            continue
        rate = class_node.attrib.get("line-rate")
        covered = []
        uncovered = []
        for line in class_node.findall(".//line"):
            number = int(line.attrib["number"])
            (covered if int(line.attrib.get("hits", "0")) > 0 else uncovered).append(number)
        summaries.append(
            CoverageFileSummary(
                source_file,
                round(float(rate) * 100, 2) if rate is not None else _coverage(covered, uncovered),
                None,
                covered,
                uncovered,
                str(path),
                "PASS",
            )
        )
    return summaries


def _coverage(covered: list[int], uncovered: list[int]) -> float | None:
    total = len(covered) + len(uncovered)
    return round(len(covered) / total * 100, 2) if total else None
