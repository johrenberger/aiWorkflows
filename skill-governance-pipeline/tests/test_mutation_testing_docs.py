"""BDD tests for the MUTATION_TESTING.md documentation.

Locks in the contract that:
- MUTATION_TESTING.md exists at the SGP project root
- It has a Results section with the killed/survived totals
- It has a "legitimate survivors" section (so the 5
  observational-equivalence survivors are documented,
  not hidden)
- The script referenced in the docs (run_mutation_check_v1.py)
  actually exists
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = PROJECT_ROOT / "MUTATION_TESTING.md"
SCRIPT_PATH = PROJECT_ROOT / "run_mutation_check_v1.py"


class TestMutationTestingDocExists:
    """The MUTATION_TESTING.md must exist and be substantive."""

    def test_doc_file_exists(self) -> None:
        """Given the SGP project root
        When we look for the mutation testing doc
        Then MUTATION_TESTING.md exists.
        """
        assert DOC_PATH.exists(), (
            f"Expected MUTATION_TESTING.md at {DOC_PATH}, but it doesn't exist."
        )

    def test_doc_has_results_section(self) -> None:
        """Given the mutation testing doc
        When we read it
        Then it has a Results section with killed/survived counts.
        """
        text = DOC_PATH.read_text(encoding="utf-8")
        assert "## Results" in text, "Expected '## Results' section in MUTATION_TESTING.md"
        assert "KILLED" in text, "Expected 'KILLED' in MUTATION_TESTING.md"
        assert "SURVIVED" in text, "Expected 'SURVIVED' in MUTATION_TESTING.md"

    def test_doc_documents_legitimate_survivors(self) -> None:
        """Given the mutation testing doc
        When we read it
        Then it documents the 5 observational-equivalence
        survivors (so they're not hidden, they're HONESTLY
        reported as legitimate).
        """
        text = DOC_PATH.read_text(encoding="utf-8")
        assert "legitimate survivors" in text.lower() or "observational equivalence" in text.lower(), (
            "Expected legitimate survivors / observational equivalence "
            "section in MUTATION_TESTING.md"
        )

    def test_doc_explains_method(self) -> None:
        """Given the mutation testing doc
        When we read it
        Then it explains the method (manual script vs mutmut)
        so future maintainers know why we use the script.
        """
        text = DOC_PATH.read_text(encoding="utf-8")
        assert "Method" in text, "Expected Method section in MUTATION_TESTING.md"
        assert "manual" in text.lower() or "mutmut" in text.lower(), (
            "Expected mention of 'manual' or 'mutmut' in Method section"
        )


class TestMutationTestingScriptExists:
    """The mutation testing script must exist and be runnable."""

    def test_script_file_exists(self) -> None:
        """Given the SGP project root
        When we look for the mutation testing script
        Then run_mutation_check_v1.py exists.
        """
        assert SCRIPT_PATH.exists(), (
            f"Expected run_mutation_check_v1.py at {SCRIPT_PATH}, "
            f"but it doesn't exist."
        )

    def test_script_is_documented_in_doc(self) -> None:
        """Given the MUTATION_TESTING.md
        When we read it
        Then it references the script by name (so users know
        how to re-run the mutation check).
        """
        text = DOC_PATH.read_text(encoding="utf-8")
        assert "run_mutation_check_v1.py" in text, (
            "Expected 'run_mutation_check_v1.py' referenced in MUTATION_TESTING.md"
        )
