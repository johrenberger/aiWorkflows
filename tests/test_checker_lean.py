"""Differential checks between the Python checker and Lean trajectory evaluation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from collatz_research.canonical import write_jsonl
from collatz_research.certificates import build_descent_certificate
from collatz_research.checker import check_certificate


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean toolchain is not available")
def test_checker_fixture_matches_lean_trajectory(tmp_path) -> None:
    cert = build_descent_certificate(5, 1)
    path = tmp_path / "certificate.jsonl"
    path.write_bytes(write_jsonl([cert.as_dict()]))
    checked = check_certificate(path)

    lean_file = tmp_path / "CheckerFixture.lean"
    lean_file.write_text(
        "\n".join(
            [
                "import CollatzResearch.Certificate",
                "",
                f"#eval CollatzResearch.trajectory {checked.start} {checked.steps}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    repo_root = Path(__file__).parents[1]
    result = subprocess.run(
        ["lake", "env", "lean", str(lean_file)],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )
    assert result.stdout.strip() == str(checked.target)
