"""BDD tests for the SGP pre-commit hook feature.

The pre-commit hook is a workflow integration that:
1. Lets SGP validate only a specific set of files (staged in git)
2. Installs a hook script into a target repo's .git/hooks/
3. Blocks commits on blocking findings
4. Reports per-file findings to the developer

These tests verify the CLI surface and the hook install behavior.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from skill_governance.cli import main

# ---------------------------------------------------------------------------
# `validate-files` subcommand
# ---------------------------------------------------------------------------


class TestValidateFilesSubcommand:
    """`validate-files` runs validation scoped to specific files."""

    def test_validate_files_exits_zero_when_no_blocking_findings(
        self, tmp_path: Path, minimal_artifact_setup: Path
    ) -> None:
        """Given a target repo with a valid skill
        When `validate-files` is called with the skill's path
        Then the command exits 0 (no blocking findings).
        """
        runner = CliRunner()
        config = minimal_artifact_setup  # a valid skill + config
        skill_file = config / "skills" / "valid-skill" / "SKILL.md"
        result = runner.invoke(
            main,
            [
                "validate-files",
                "--config",
                str(config / "config.yaml"),
                str(skill_file),
            ],
        )
        assert result.exit_code == 0, (
            f"Expected exit 0 for valid skill, got {result.exit_code}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_validate_files_exits_nonzero_on_blocking_finding(
        self, tmp_path: Path, minimal_artifact_setup: Path
    ) -> None:
        """Given a target repo with a skill missing required metadata
        When `validate-files` is called with the skill's path
        Then the command exits non-zero (blocking finding present).
        """
        runner = CliRunner()
        config = minimal_artifact_setup
        # Create a skill with missing name (blocking finding)
        bad_skill = config / "skills" / "bad-skill" / "SKILL.md"
        bad_skill.parent.mkdir(parents=True)
        bad_skill.write_text(
            "---\nartifact_type: skill\npurpose: Missing name field\n---\n",
            encoding="utf-8",
        )
        result = runner.invoke(
            main,
            [
                "validate-files",
                "--config",
                str(config / "config.yaml"),
                str(bad_skill),
            ],
        )
        assert result.exit_code != 0, (
            f"Expected non-zero exit for skill missing name, got {result.exit_code}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # Distinguish SGP exit (blocking finding) from Click error
        # (no such command). When Click can't find the command, the
        # error is "No such command 'validate-files'". An SGP
        # exit should not have that.
        output = result.stdout + result.stderr
        assert "No such command" not in output, (
            f"Expected SGP's own exit, not Click's 'no such command'.\n"
            f"Got: {output[:500]}"
        )

    def test_validate_files_only_reports_findings_for_specified_files(
        self, tmp_path: Path, minimal_artifact_setup: Path
    ) -> None:
        """Given two skills, one valid and one with a blocking finding
        When `validate-files` is called with only the VALID skill's path
        Then the exit code is 0 (the other skill is not in scope).
        """
        runner = CliRunner()
        config = minimal_artifact_setup
        # Add a bad skill (will produce a blocking finding)
        bad_skill = config / "skills" / "bad-skill" / "SKILL.md"
        bad_skill.parent.mkdir(parents=True)
        bad_skill.write_text(
            "---\nartifact_type: skill\npurpose: Missing name field\n---\n",
            encoding="utf-8",
        )
        # Reference the GOOD skill's path
        good_skill = config / "skills" / "valid-skill" / "SKILL.md"
        result = runner.invoke(
            main,
            [
                "validate-files",
                "--config",
                str(config / "config.yaml"),
                str(good_skill),
            ],
        )
        assert result.exit_code == 0, (
            f"Expected exit 0 (only good skill in scope), got {result.exit_code}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_validate_files_output_lists_per_file_findings(
        self, tmp_path: Path, minimal_artifact_setup: Path
    ) -> None:
        """Given a skill with a blocking finding
        When `validate-files` is called
        Then the output includes the file path and finding category
        (so the developer can see what to fix).
        """
        runner = CliRunner()
        config = minimal_artifact_setup
        bad_skill = config / "skills" / "bad-skill" / "SKILL.md"
        bad_skill.parent.mkdir(parents=True)
        bad_skill.write_text(
            "---\nartifact_type: skill\npurpose: Missing name field\n---\n",
            encoding="utf-8",
        )
        result = runner.invoke(
            main,
            [
                "validate-files",
                "--config",
                str(config / "config.yaml"),
                str(bad_skill),
            ],
        )
        # Output should mention the file or the finding category
        output = result.stdout + result.stderr
        assert "bad-skill" in output or "metadata" in output.lower(), (
            f"Expected output to mention the bad skill or metadata category.\n"
            f"Got: {output[:500]}"
        )


# ---------------------------------------------------------------------------
# `install-hooks` subcommand
# ---------------------------------------------------------------------------


class TestInstallHooksSubcommand:
    """`install-hooks` copies the SGP pre-commit hook into a target repo."""

    def test_install_hooks_creates_git_hooks_pre_commit(
        self, tmp_path: Path
    ) -> None:
        """Given a target repo (a directory with a .git/ subdir)
        When `install-hooks` is called with the target repo path
        Then .git/hooks/pre-commit exists and is executable.
        """
        # Set up a fake git repo
        repo = tmp_path / "my-project"
        repo.mkdir()
        (repo / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(main, ["install-hooks", str(repo)])
        assert result.exit_code == 0, (
            f"Expected exit 0, got {result.exit_code}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        hook = repo / ".git" / "hooks" / "pre-commit"
        assert hook.exists(), f"Expected hook at {hook}"
        assert hook.stat().st_mode & 0o111, f"Expected hook to be executable, mode={oct(hook.stat().st_mode)}"

    def test_install_hooks_hook_script_uses_sgp_validate_files(
        self, tmp_path: Path
    ) -> None:
        """Given an installed hook
        When the hook script is read
        Then it calls `python -m skill_governance.cli validate-files` (or equivalent)
        so that staged files are validated.
        """
        repo = tmp_path / "my-project"
        repo.mkdir()
        (repo / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        result = runner.invoke(main, ["install-hooks", str(repo)])
        assert result.exit_code == 0
        hook = repo / ".git" / "hooks" / "pre-commit"
        content = hook.read_text(encoding="utf-8")
        assert "validate-files" in content, (
            f"Expected hook to call validate-files, got: {content[:500]}"
        )

    def test_install_hooks_fails_gracefully_without_git_dir(
        self, tmp_path: Path
    ) -> None:
        """Given a target path that has no .git/ subdir
        When `install-hooks` is called
        Then the command exits non-zero with a clear error message.
        """
        not_a_repo = tmp_path / "not-a-git-repo"
        not_a_repo.mkdir()
        runner = CliRunner()
        result = runner.invoke(main, ["install-hooks", str(not_a_repo)])
        assert result.exit_code != 0, (
            f"Expected non-zero exit for non-git target, got {result.exit_code}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # Should mention .git. Specifically `.git` (the literal
        # path component), not just the word "git" appearing in
        # "No such command 'install-hooks'". We check for the
        # path component or the word "not a git" / "missing .git".
        output = result.stdout + result.stderr
        assert ".git" in output or "not a git" in output.lower(), (
            f"Expected error to mention .git path, got: {output[:300]}"
        )

    def test_install_hooks_is_idempotent(
        self, tmp_path: Path
    ) -> None:
        """Given an already-installed hook
        When `install-hooks` is called again
        Then it overwrites the hook without erroring (idempotent).
        """
        repo = tmp_path / "my-project"
        repo.mkdir()
        (repo / ".git" / "hooks").mkdir(parents=True)
        runner = CliRunner()
        runner.invoke(main, ["install-hooks", str(repo)])
        result = runner.invoke(main, ["install-hooks", str(repo)])
        assert result.exit_code == 0, (
            f"Expected idempotent install, got {result.exit_code}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        hook = repo / ".git" / "hooks" / "pre-commit"
        assert hook.exists()


# ---------------------------------------------------------------------------
# The pre-commit hook itself
# ---------------------------------------------------------------------------


class TestPreCommitHookScript:
    """The pre-commit hook script must:
    1. Read staged files via `git diff --cached --name-only`
    2. Skip when no relevant files are staged (fast-path)
    3. Call sgp validate-files with the staged paths
    4. Exit 0 when no blocking findings, non-zero when blockers
    5. Be a valid shell script
    """

    HOOK_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "hooks" / "pre-commit"

    def test_hook_script_exists(self) -> None:
        """The hook script must exist in the SGP repo at hooks/pre-commit."""
        assert self.HOOK_SCRIPT_PATH.exists(), (
            f"Hook script not found at {self.HOOK_SCRIPT_PATH}"
        )

    def test_hook_script_is_valid_shell(self) -> None:
        """The hook script must pass `bash -n` syntax check."""
        result = subprocess.run(
            ["bash", "-n", str(self.HOOK_SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Hook script has shell syntax errors: {result.stderr}"
        )

    def test_hook_script_skips_when_no_skill_or_agent_files_staged(self) -> None:
        """The hook should exit 0 fast when no relevant files are staged.

        The pre-commit hook reads `git diff --cached --name-only` to
        find staged files. If none match `*/SKILL.md` or `*AGENT.md`,
        the hook should skip the validation (no work to do).
        """
        content = self.HOOK_SCRIPT_PATH.read_text(encoding="utf-8")
        # The hook should check for relevant files before running sgp
        assert "SKILL.md" in content or "AGENT.md" in content or "skip" in content.lower(), (
            "Expected hook to have a skip/filter step for staged files"
        )

    def test_hook_script_calls_sgp_validate_files(self) -> None:
        """The hook must call `validate-files` to validate staged files."""
        content = self.HOOK_SCRIPT_PATH.read_text(encoding="utf-8")
        assert "validate-files" in content, (
            "Expected hook to call `validate-files`"
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_artifact_setup(tmp_path: Path) -> Path:
    """Create a minimal target repo with a valid skill and SGP config.

    Returns the tmp_path (used as the target repo root).
    """
    skills_dir = tmp_path / "skills"
    valid_skill_dir = skills_dir / "valid-skill"
    valid_skill_dir.mkdir(parents=True)
    valid_skill_dir.joinpath("SKILL.md").write_text(
        "---\n"
        "name: valid-skill\n"
        "artifact_type: skill\n"
        "purpose: A valid skill for testing the pre-commit hook feature in this SGP test suite.\n"
        "category: operations\n"
        "owner: test\n"
        "version: 1.0.0\n"
        "inputs:\n  - trigger\n"
        "outputs:\n  - result\n"
        "dependencies: none\n"
        "intended_consumers:\n  - test-automation-agent\n"
        "quality_level: usable\n"
        "last_reviewed: 2026-06-14\n"
        "---\n",
        encoding="utf-8",
    )
    config = tmp_path / "config.yaml"
    config.write_text(
        f"skill_directories: [{skills_dir}]\n"
        "agent_directories: []\n"
        "output_directory: output\n"
        "ci_blocking_categories: [metadata, contract, vague-output]\n"
        "health_weights: {metadata: 1.0}\n"
        "inclusion_patterns: ['**/SKILL.md', '**/*AGENT.md']\n"
        "exclusion_patterns: []\n",
        encoding="utf-8",
    )
    return tmp_path
