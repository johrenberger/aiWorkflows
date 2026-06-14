"""BDD-TDD coverage tests for CTA-GAP-001: discovery._classify_artifact ambiguity.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-GAP-001 is a P2 gap (T2 risk):

    "_classify_artifact uses 'SKILL' as a fallback when filename is
    exactly 'SKILL' but the path doesn't contain 'skill'. The fallback
    returns ArtifactType.SKILL even if the file is in an 'agents/'
    directory. Need a test for the 'agents/SKILL.md' case (where
    filename and directory hint disagree)."

The current code does:
  if SKILL_PATH_PATTERN.search(rel): return ArtifactType.SKILL
  if AGENT_PATH_PATTERN.search(rel): return ArtifactType.AGENT

The SKILL pattern (case-insensitive substring "skill" in any path
component) ALSO matches "agents/SKILL.md" because the filename "SKILL"
contains "skill" as a substring. So the function returns SKILL, but
the directory hint says AGENT. The gap calls for: directory hint wins
over filename hint.

These tests lock the desired behavior:
- 'agents/SKILL.md' -> AGENT (directory hint wins)
- 'skills/AGENT.md' -> SKILL (directory hint wins)
- 'loose/SKILL.md' -> SKILL (no directory hint, filename hint used)
- 'loose/AGENT.md' -> AGENT (no directory hint, filename hint used)

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
- Red-phase: tests fail against the current code (red)
- Green-phase: tests pass after fixing `classify_artifact`
"""
from __future__ import annotations

from pathlib import Path

from skill_governance.discovery import classify_artifact
from skill_governance.models import ArtifactType


# ===========================================================================
# SCENARIO 1: agents/SKILL.md -> AGENT (directory hint wins)
#
# Given: a file at "agents/SKILL.md"
# When:  classify_artifact is called
# Then:  returns ArtifactType.AGENT (the directory "agents" is the
#        stronger hint than the filename "SKILL")
# ===========================================================================
def test_classify_artifact_directory_hint_wins_over_skill_filename():
    """A file at 'agents/SKILL.md' is classified as AGENT (directory hint wins)."""
    assert classify_artifact(Path("agents/SKILL.md"), Path(".")) == ArtifactType.AGENT


# ===========================================================================
# SCENARIO 2: skills/AGENT.md -> SKILL (directory hint wins)
#
# Given: a file at "skills/AGENT.md"
# When:  classify_artifact is called
# Then:  returns ArtifactType.SKILL (the directory "skills" is the
#        stronger hint than the filename "AGENT")
# ===========================================================================
def test_classify_artifact_directory_hint_wins_over_agent_filename():
    """A file at 'skills/AGENT.md' is classified as SKILL (directory hint wins)."""
    assert classify_artifact(Path("skills/AGENT.md"), Path(".")) == ArtifactType.SKILL


# ===========================================================================
# SCENARIO 3: loose/SKILL.md (no directory hint) -> SKILL (filename hint)
#
# Given: a file at "loose/SKILL.md" (directory "loose" has no skill/agent hint)
# When:  classify_artifact is called
# Then:  returns ArtifactType.SKILL (filename "SKILL" matches the SKILL fallback)
# ===========================================================================
def test_classify_artifact_filename_hint_used_when_no_directory_hint_skill():
    """A file at 'loose/SKILL.md' is classified as SKILL (no directory conflict)."""
    assert classify_artifact(Path("loose/SKILL.md"), Path(".")) == ArtifactType.SKILL


# ===========================================================================
# SCENARIO 4: loose/AGENT.md (no directory hint) -> AGENT (filename hint)
#
# Given: a file at "loose/AGENT.md" (directory "loose" has no skill/agent hint)
# When:  classify_artifact is called
# Then:  returns ArtifactType.AGENT (filename "AGENT" matches the AGENT fallback)
# ===========================================================================
def test_classify_artifact_filename_hint_used_when_no_directory_hint_agent():
    """A file at 'loose/AGENT.md' is classified as AGENT (no directory conflict)."""
    assert classify_artifact(Path("loose/AGENT.md"), Path(".")) == ArtifactType.AGENT


# ===========================================================================
# SCENARIO 5: deeper paths also work (agents/sub/SKILL.md)
#
# Given: a file at "agents/sub/SKILL.md" (agent dir is in the path tree)
# When:  classify_artifact is called
# Then:  returns ArtifactType.AGENT (any ancestor directory hint wins)
# ===========================================================================
def test_classify_artifact_deep_agent_directory_with_skill_filename():
    """A file at 'agents/sub/SKILL.md' is classified as AGENT."""
    assert classify_artifact(Path("agents/sub/SKILL.md"), Path(".")) == ArtifactType.AGENT


# ===========================================================================
# SCENARIO 6: deeper paths also work (skills/sub/AGENT.md)
#
# Given: a file at "skills/sub/AGENT.md" (skill dir is in the path tree)
# When:  classify_artifact is called
# Then:  returns ArtifactType.SKILL (any ancestor directory hint wins)
# ===========================================================================
def test_classify_artifact_deep_skill_directory_with_agent_filename():
    """A file at 'skills/sub/AGENT.md' is classified as SKILL."""
    assert classify_artifact(Path("skills/sub/AGENT.md"), Path(".")) == ArtifactType.SKILL
