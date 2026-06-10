from __future__ import annotations

from pathlib import Path

from ..models import MutationToolDetection


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
        for candidate in (repo_root / "pyproject.toml", repo_root / "setup.cfg", repo_root / "pytest.ini"):
            if candidate.exists() and ("mutmut" in candidate.read_text(encoding="utf-8", errors="ignore").lower() or "cosmic-ray" in candidate.read_text(encoding="utf-8", errors="ignore").lower()):
                text = candidate.read_text(encoding="utf-8", errors="ignore").lower()
                tool = "mutmut" if "mutmut" in text else "cosmic-ray"
                command = ["mutmut", "run"] if tool == "mutmut" else ["cosmic-ray", "run"]
                return MutationToolDetection(language="python", tool=tool, available=True, evidence=[candidate.name], command=command)
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

