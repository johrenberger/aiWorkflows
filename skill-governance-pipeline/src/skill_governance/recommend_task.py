"""Task-to-artifact recommendation for SGP.

Given a natural-language task description, return the top N
artifacts (agents + skills) that best match the task.

This is a deterministic, token-based matcher — no LLM. The
intent is to give a starting point for a user who doesn't
yet know the catalog. LLM-based matching is a future extension.

The algorithm:
1. Tokenize the task (lowercase, remove stopwords, remove punctuation)
2. For each artifact in the catalog, build a token index
   (one entry per artifact, with the artifact's "matchable text"
   = situation text + purpose text)
3. Score each artifact by token overlap with the task
4. Return the top N (default 3) sorted by score

The scoring uses a Jaccard-like formula: |overlap| / |union of
tokens in (task, artifact)|, capped at 1.0. This is robust to
artifacts of different lengths.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# English stopwords for task tokenization. Conservative — we
# keep words that might be meaningful in a task (e.g. 'need',
# 'run', 'fix', 'build') even if they're common in English.
STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "is", "are", "was", "were",
    "i", "you", "we", "they", "he", "she", "it",
    "my", "your", "our", "their", "his", "her", "its",
    "to", "of", "in", "on", "at", "by", "for", "with", "from",
    "as", "be", "this", "that", "these", "those",
    "am", "do", "does", "did", "has", "have", "had",
    "can", "could", "should", "would", "will", "shall", "may", "might",
    "me", "us", "them", "him",
})


def _stem(token: str) -> str:
    """Strip common English suffixes to normalize word forms.

    This is a very lightweight stemmer (not Porter/Snowball) but
    handles the common cases that affect task matching:
    - plural → singular: "tests" → "test", "skills" → "skill"
    - gerund → base:    "deploying" → "deploy", "running" → "runn"
    - past → base:      "deployed" → "deploy", "shipped" → "ship"
    - agentive:         "engineer" → "engine", "manager" → "manag"

    We don't try to be perfect. We just normalize the most common
    inflectional forms so "deploy" matches "deployment" / "deploying".
    """
    if len(token) <= 4:
        return token
    # Order matters: try the longest suffixes first so that
    # "deployments" → "deploy" (matches "ments" first, not "s").
    for suffix, min_stem in [
        ("ments", 4), ("tions", 4), ("sions", 4), ("nesses", 4),
        ("tion", 4), ("sion", 4), ("ment", 4), ("ness", 4),
        ("ings", 3), ("ers", 3), ("ies", 3),
        ("ing", 3), ("ed", 3), ("er", 3), ("es", 3), ("ly", 3), ("s", 3),
    ]:
        if token.endswith(suffix) and len(token) - len(suffix) >= min_stem:
            return token[: -len(suffix)]
    return token


def tokenize(task: str) -> list[str]:
    """Tokenize a task description.

    Steps:
    1. Lowercase
    2. Replace any non-alphanumeric char with a space
    3. Split on whitespace
    4. Remove empty tokens
    5. Remove stopwords
    6. Apply lightweight stemming

    Returns a list of normalized tokens (no duplicates removed
    intentionally — duplication reflects emphasis).
    """
    s = task.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    raw_tokens = s.split()
    return [_stem(t) for t in raw_tokens if t and t not in STOPWORDS]


def score_artifact(
    task_tokens: list[str],
    situation_text: str,
    purpose_text: str,
) -> float:
    """Score a single artifact against a tokenized task.

    Uses the **overlap coefficient**: |intersection| / min(|task|, |artifact|).
    This rewards any overlap regardless of artifact length, unlike
    Jaccard which is biased toward short artifacts.

    Args:
        task_tokens: the tokenized task description
        situation_text: free text describing when this artifact applies
        purpose_text: free text describing what the artifact does

    Returns:
        A score in [0.0, 1.0]. 0.0 means no overlap.
    """
    if not task_tokens:
        return 0.0
    # Tokenize the artifact's matchable text the same way
    artifact_text = f"{situation_text}\n{purpose_text}"
    artifact_tokens = tokenize(artifact_text)
    if not artifact_tokens:
        return 0.0

    task_set = set(task_tokens)
    artifact_set = set(artifact_tokens)
    intersection = task_set & artifact_set
    if not intersection:
        return 0.0
    return len(intersection) / min(len(task_set), len(artifact_set))


@dataclass(frozen=True)
class Artifact:
    """A catalog entry used for matching.

    Fields:
        name: the artifact's name (kebab-case identifier)
        type: 'agent' or 'skill'
        situation: free text describing when this applies
        purpose: free text describing what the artifact does
    """

    name: str
    type: str
    situation: str
    purpose: str

    @property
    def matchable_text(self) -> str:
        return f"{self.situation}\n{self.purpose}"


# Type alias for the simple tuple form used by the public API.
# `ArtifactTuple = tuple[str, str, str, str]` is
# (name, type, situation, purpose). This form is convenient
# for tests and for callers who don't want to use the
# Artifact dataclass.
ArtifactTuple = tuple[str, str, str, str]


def _to_artifact(item: Artifact | ArtifactTuple) -> Artifact:
    """Coerce an Artifact or 4-tuple to an Artifact."""
    if isinstance(item, Artifact):
        return item
    return Artifact(name=item[0], type=item[1], situation=item[2], purpose=item[3])


def build_token_index(
    artifacts: list[Artifact] | list[ArtifactTuple],
) -> dict[str, set[str]]:
    """Build a per-artifact token set for fast lookup.

    The index maps artifact name -> set of tokens from that
    artifact's matchable text. This is a memory/CPU trade-off:
    indexing costs O(N * L) where N is artifact count and L is
    average text length; matching is then O(1) per query.

    Accepts either a list of Artifact dataclasses or a list
    of 4-tuples (name, type, situation, purpose).
    """
    return {
        a.name: set(tokenize(a.matchable_text))
        for a in (_to_artifact(item) for item in artifacts)
    }


def match_task(
    task_tokens: list[str],
    index: dict[str, set[str]],
    artifacts: list[Artifact] | list[ArtifactTuple],
) -> list[tuple[str, float]]:
    """Match a tokenized task against an index of artifacts.

    Returns a list of (artifact_name, score) sorted by score
    descending. Entries with score 0 are omitted. Scoring uses
    the overlap coefficient (see `score_artifact`).
    """
    if not task_tokens:
        return []
    task_set = set(task_tokens)
    results: list[tuple[str, float]] = []
    for item in artifacts:
        a = _to_artifact(item)
        artifact_tokens = index.get(a.name, set())
        if not artifact_tokens:
            continue
        intersection = task_set & artifact_tokens
        if not intersection:
            continue
        score = len(intersection) / min(len(task_set), len(artifact_tokens))
        if score > 0:
            results.append((a.name, score))
    results.sort(key=lambda x: (-x[1], x[0]))
    return results


def recommend_task(
    task: str,
    artifacts: list[Artifact] | list[ArtifactTuple],
    top_n: int = 3,
) -> list[tuple[str, str, float]]:
    """High-level: tokenize the task, match, return top N.

    Args:
        task: natural-language task description
        artifacts: catalog of (name, type, situation, purpose)
            (either Artifact dataclasses or 4-tuples)
        top_n: number of results to return (default 3)

    Returns:
        A list of (name, type, score) tuples sorted by score desc.
    """
    task_tokens = tokenize(task)
    if not task_tokens:
        return []
    index = build_token_index(artifacts)
    matches = match_task(task_tokens, index, artifacts)
    type_lookup = {_to_artifact(item).name: _to_artifact(item).type for item in artifacts}
    return [
        (name, type_lookup.get(name, "?"), score)
        for name, score in matches[:top_n]
    ]
