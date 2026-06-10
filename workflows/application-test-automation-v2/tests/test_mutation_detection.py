from __future__ import annotations

from pathlib import Path

from test_factory.analyzers.mutation_analyzer import detect_mutation_tool


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-repo"


def test_mutation_detection_degrades_gracefully():
    detection = detect_mutation_tool(FIXTURE, language="python")
    assert detection.available is False or detection.tool in {"mutmut", "cosmic-ray"}
