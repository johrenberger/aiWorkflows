"""Cross-reference consistency checks for skills and agents.

The cross-reference feature adds two new optional fields to the
skill/agent YAML frontmatter:

- ``uses_skills: list[str]`` (on agents) — names of skills the agent uses
- ``used_by_agents: list[str]`` (on skills) — names of agents that use this skill

The relationship is symmetric. This module checks for
inconsistencies: if agent A claims to use skill B, then skill B
should claim to be used by agent A. If not, it's an inconsistency
that should be flagged for review.

Inconsistencies are reported as Inconsistency dataclasses with
enough context to point to the problem (artifact name, the
referencing artifact, and which direction is missing).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Inconsistency:
    """A bidirectional cross-reference inconsistency.

    Either:
    - artifact A claims it uses/used-by B, but B doesn't reciprocate
      (``missing_inverse=True``)
    """

    artifact: str  # The artifact whose inverse reference is missing
    referenced_by: str  # The artifact that references it
    reference_type: str  # 'uses_skills' or 'used_by_agents'
    missing_inverse: bool  # True: the reference is one-way


def check_consistency(
    artifacts: list[tuple[str, str, list[str], list[str]]],
) -> list[Inconsistency]:
    """Check cross-reference consistency across a set of artifacts.

    Args:
        artifacts: A list of (name, type, uses_skills, used_by_agents)
            tuples for every artifact in the catalog.

    Returns:
        A list of Inconsistency objects for any one-way references.
        An empty list means all cross-references are bidirectional.
    """
    inconsistencies: list[Inconsistency] = []

    # Build lookup: name -> (type, uses_skills, used_by_agents)
    lookup: dict[str, tuple[str, list[str], list[str]]] = {}
    for name, atype, uses_skills, used_by_agents in artifacts:
        lookup[name] = (atype, uses_skills, used_by_agents)

    # Check 1: For each agent that uses a skill, the skill should
    # have the agent in its used_by_agents.
    for name, atype, uses_skills, _used_by_agents in artifacts:
        if atype != "agent":
            continue
        for skill_name in uses_skills:
            if skill_name not in lookup:
                # Skill doesn't exist; that's a separate concern
                # (covered by `missing-dependency` finding), not by
                # cross-reference consistency. Skip.
                continue
            _, _, skill_used_by = lookup[skill_name]
            if name not in skill_used_by:
                inconsistencies.append(
                    Inconsistency(
                        artifact=skill_name,
                        referenced_by=name,
                        reference_type="uses_skills",
                        missing_inverse=True,
                    )
                )

    # Check 2: For each skill that lists an agent in used_by_agents,
    # the agent should have the skill in its uses_skills.
    for name, atype, _uses_skills, used_by_agents in artifacts:
        if atype != "skill":
            continue
        for agent_name in used_by_agents:
            if agent_name not in lookup:
                # Agent doesn't exist; skip.
                continue
            _, agent_uses, _ = lookup[agent_name]
            if name not in agent_uses:
                inconsistencies.append(
                    Inconsistency(
                        artifact=agent_name,
                        referenced_by=name,
                        reference_type="used_by_agents",
                        missing_inverse=True,
                    )
                )

    return inconsistencies
