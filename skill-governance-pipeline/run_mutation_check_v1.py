#!/usr/bin/env python3
"""Manual mutation check for the v1.0.0 release.

Targets the modules added or hardened in the late-stage work:
- recommend_task.py (PR #53)
- cross_references.py (PR #51)
- overlap_analyzer.py (PR #49 hardening)
- roi_scorer.py (PR #49 hardening)
- discovery.py (PR #45 hardening)

For each targeted file, introduces a list of small mutations and runs
the new tests against the mutated code. A mutant is "killed" if at
least one test fails; otherwise it "survives".

Usage: python3 run_mutation_check_v1.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "src" / "skill_governance"

# (file_relpath, original_substring, mutated_substring, label, tests_to_run)
MUTANTS: list[tuple[str, str, str, str, list[str]]] = [
    # ---- recommend_task.py (PR #53) ----
    (
        "recommend_task.py",
        "len(intersection) / min(len(task_set), len(artifact_set))",
        "len(intersection) / max(len(task_set), len(artifact_set))",
        "PR #53: use max instead of min in overlap coefficient",
        ["tests/test_recommend_task.py"],
    ),
    (
        "recommend_task.py",
        "if token.endswith(suffix) and len(token) - len(suffix) >= min_stem:",
        "if token.endswith(suffix) and len(token) - len(suffix) > min_stem:",
        "PR #53: change stemmer >= to > (off-by-one boundary)",
        ["tests/test_recommend_task.py"],
    ),
    (
        "recommend_task.py",
        "if not task_tokens:",
        "if task_tokens:",
        "PR #53: invert the empty-task guard",
        ["tests/test_recommend_task.py"],
    ),
    (
        "recommend_task.py",
        "results.sort(key=lambda x: (-x[1], x[0]))",
        "results.sort(key=lambda x: (x[1], x[0]))",
        "PR #53: ascending sort instead of descending",
        ["tests/test_recommend_task.py"],
    ),
    (
        "recommend_task.py",
        'results.append((a.name, score))',
        'results.append((a.name, 0.0))',
        "PR #53: always append 0.0 (matcher returns nothing)",
        ["tests/test_recommend_task.py"],
    ),
    # ---- cross_references.py (PR #51) ----
    (
        "cross_references.py",
        "if name not in skill_used_by:",
        "if name in skill_used_by:",
        "PR #51: invert the one-way reference check (Check 1)",
        ["tests/test_cross_references.py"],
    ),
    (
        "cross_references.py",
        "if name not in agent_uses:",
        "if name in agent_uses:",
        "PR #51: invert the other one-way reference check (Check 2)",
        ["tests/test_cross_references.py"],
    ),
    (
        "cross_references.py",
        "inconsistencies.append(\n                    Inconsistency(",
        "inconsistencies.append(\n                    _InconsistencyInternal(",
        "PR #51: rename Inconsistency so check_consistency returns empty",
        ["tests/test_cross_references.py"],
    ),
    # ---- overlap_analyzer.py (PR #49 hardening) ----
    (
        "overlap_analyzer.py",
        "if not a and not b:\n        return 0.0\n    sa = set(a)\n    sb = set(b)",
        "if not a or not b:\n        return 0.0\n    sa = set(a)\n    sb = set(b)",
        "GAP-PR49: jaccard - change 'and' to 'or' (empty intersection bug)",
        [
            "tests/test_hardening_p7.py",
            "tests/test_property_based_p8.py",
            "tests/test_focused_picks_gap003_overlap_boundaries.py",
        ],
    ),
    (
        "overlap_analyzer.py",
        "inter = sum((a & b).values())",
        "inter = len(a & b)",
        "GAP-PR49: bag - multiset to set overlap (loses multiplicity)",
        [
            "tests/test_hardening_p7.py",
            "tests/test_property_based_p8.py",
        ],
    ),
    (
        "overlap_analyzer.py",
        "if not a_tokens or not b_tokens:",
        "if not a_tokens and not b_tokens:",
        "GAP-PR49: name overlap - change 'or' to 'and' (loses zero case)",
        [
            "tests/test_hardening_p7.py",
            "tests/test_property_based_p8.py",
        ],
    ),
    # ---- roi_scorer.py (PR #49 hardening) ----
    (
        "roi_scorer.py",
        "lo: float = 0.0,",
        "lo: float = 1.0,",
        "GAP-PR49: _normalize - default lo: 1.0",
        [
            "tests/test_hardening_p7.py",
            "tests/test_focused_picks_gap005_roi_split_boundary.py",
        ],
    ),
    # ---- discovery.py (PR #45 hardening) ----
    (
        "discovery.py",
        "if AGENT_PATH_PATTERN.search(directory):\n        return ArtifactType.AGENT",
        "if AGENT_PATH_PATTERN.search(directory):\n        return ArtifactType.SKILL",
        "GAP-PR45: classify_artifact - agent dir hint returns SKILL",
        ["tests/test_focused_picks_p2_gap001_classify_artifact.py"],
    ),
    (
        "discovery.py",
        "if SKILL_PATH_PATTERN.search(directory):\n        return ArtifactType.SKILL",
        "if SKILL_PATH_PATTERN.search(directory):\n        return ArtifactType.AGENT",
        "GAP-PR45: classify_artifact - skill dir hint returns AGENT",
        ["tests/test_focused_picks_p2_gap001_classify_artifact.py"],
    ),
]


def run_mutant_check():
    """Run each mutant, return (killed, survived, errors, results)."""
    killed = 0
    survived = 0
    errors = []
    results: list[tuple[str, str, str]] = []
    for relpath, original, mutated, label, tests in MUTANTS:
        path = SRC / relpath
        text = path.read_text()
        if original not in text:
            results.append((label, "ERROR", f"original substring not found in {relpath}"))
            errors.append(label)
            continue
        mutated_text = text.replace(original, mutated, 1)
        if mutated_text == text:
            results.append((label, "ERROR", "substitution produced no change"))
            errors.append(label)
            continue
        backup = text
        path.write_text(mutated_text)
        try:
            cmd = ["python3", "-m", "pytest", *tests, "-q", "--no-cov", "-p", "no:randomly", "--tb=line"]
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                status = "SURVIVED"
                survived += 1
            else:
                status = "KILLED"
                killed += 1
            # Last meaningful line
            detail = ""
            for line in r.stdout.splitlines()[::-1]:
                if "passed" in line or "failed" in line or "error" in line.lower():
                    detail = line.strip()
                    break
            if not detail:
                detail = r.stdout.splitlines()[-1] if r.stdout else "(no output)"
            results.append((label, status, detail))
        except subprocess.TimeoutExpired:
            results.append((label, "TIMEOUT", "test run timed out"))
            errors.append(label)
        except Exception as e:
            results.append((label, "ERROR", str(e)))
            errors.append(label)
        finally:
            path.write_text(backup)
    return killed, survived, errors, results


def main():
    print("=" * 80)
    print("Manual mutation check (v1.0.0 release)")
    print("=" * 80)
    killed, survived, errors, results = run_mutant_check()
    for label, status, detail in results:
        marker = "K" if status == "KILLED" else ("S" if status == "SURVIVED" else "?")
        print(f"  [{marker}] {status:10s}  {label}")
        if status != "KILLED":
            print(f"      {detail[:120]}")
    print("-" * 80)
    total = len(results)
    if total:
        print(f"Total mutants: {total}")
        print(f"Killed:        {killed}/{total}  ({100*killed//total}%)")
        print(f"Survived:      {survived}/{total}")
        print(f"Errors:        {len(errors)}")
    return 0 if survived == 0 and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
