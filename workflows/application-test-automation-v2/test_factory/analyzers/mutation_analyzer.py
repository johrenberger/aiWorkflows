from __future__ import annotations

import shutil
import sys
from importlib import util as importlib_util
from pathlib import Path

from ..models import MutationToolDetection


def _python_tool_installed(name: str) -> bool:
    """A Python mutation tool is considered available if either:
    1. Its CLI is on PATH (shutil.which), OR
    2. The package is importable in the current Python (importlib.util.find_spec).

    The original detect_mutation_tool only checked the config-file mention,
    which meant a tool installed via `pip install mutmut` with no config
    declaration was reported as unavailable. Bug surfaced 2026-06-10 on
    v2's own self-coverage run; see PR #22.
    """
    if shutil.which(name):
        return True
    return importlib_util.find_spec(name.replace("-", "_")) is not None or importlib_util.find_spec(name) is not None


def detect_mutation_tool(repo_root: str | Path, module: str = "", language: str = "") -> MutationToolDetection:
    repo_root = Path(repo_root)
    evidence: list[str] = []
    if language == "java":
        for candidate in (repo_root / "pom.xml", repo_root / "build.gradle", repo_root / "build.gradle.kts"):
            if candidate.exists() and "pit" in candidate.read_text(encoding="utf-8", errors="ignore").lower():
                evidence.append(candidate.name)
                return MutationToolDetection(language="java", tool="pitest", available=True, evidence=evidence, command=["mvn", "test", "org.pitest:pitest-maven:mutationCoverage"])
    if language == "javascript":
        for candidate in (repo_root / "package.json", repo_root / "stryker.conf.js", repo_root / "stryker.conf.ts", repo_root / "stryker.conf.json"):
            if candidate.exists() and "stryker" in candidate.read_text(encoding="utf-8", errors="ignore").lower():
                evidence.append(candidate.name)
                return MutationToolDetection(language="javascript", tool="stryker", available=True, evidence=evidence, command=["npx", "stryker", "run"])
    if language == "python":
        # Check the config-file declaration first (preserves the original
        # intent: respect the project's explicit choice). Then fall through
        # to a runtime-install check so a venv-installed tool is also seen.
        for candidate in (repo_root / "pyproject.toml", repo_root / "setup.cfg", repo_root / "pytest.ini"):
            if candidate.exists():
                text = candidate.read_text(encoding="utf-8", errors="ignore").lower()
                if "mutmut" in text:
                    return MutationToolDetection(language="python", tool="mutmut", available=_python_tool_installed("mutmut"), evidence=[candidate.name], command=["mutmut", "run"])
                if "cosmic-ray" in text:
                    return MutationToolDetection(language="python", tool="cosmic-ray", available=_python_tool_installed("cosmic-ray"), evidence=[candidate.name], command=["cosmic-ray", "run"])
        # No config-file mention — still report available if mutmut is
        # importable in the current Python. This is the most common
        # Python mutation tool and the one most likely to be pre-installed
        # in CI images; defaulting to it gives a useful signal instead
        # of a dead-end "no tool available".
        if _python_tool_installed("mutmut"):
            return MutationToolDetection(language="python", tool="mutmut", available=True, evidence=["runtime:mutmut"], command=["mutmut", "run"])
        if _python_tool_installed("cosmic-ray"):
            return MutationToolDetection(language="python", tool="cosmic-ray", available=True, evidence=["runtime:cosmic-ray"], command=["cosmic-ray", "run"])
    return MutationToolDetection(language=language or "unknown", tool="", available=False, evidence=evidence, command=[])


def mutation_candidates_from_scores(scores: list[dict[str, object]], high_risk_only: bool = True) -> list[dict[str, object]]:
    candidates = []
    for item in scores:
        risk = float(item.get("risk_score", 0))
        coverage = float(item.get("coverage_gap", 0))
        if high_risk_only and risk < 50 and coverage < 20:
            continue
        if coverage <= 0 and risk <= 0:
            continue
        candidates.append({"path": item["path"], "module": item["module"], "score": risk + coverage, "evidence": item})
    candidates.sort(key=lambda x: (-float(x["score"]), str(x["path"])))
    return candidates

