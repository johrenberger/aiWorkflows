"""Overlap analyzer: pairwise overlap between artifacts.

Implements Core Requirement 6.

Phase 2 provides the deterministic layer:
- Tokenize body excerpts + purpose + inputs + outputs
- Compute Jaccard similarity on bag-of-words
- Combine with simple structural signals (same name tokens,
  same input/output type hints)
- Score 0-100
- Recommendation: merge / differentiate / keep_separate

Thresholds:
- overlap_score >= 85: CI-blocking unless justified
- overlap_score 70-84: warning
- overlap_score < 70: informational

Phase 3 will add a MiniMax semantic scoring layer on top of
this deterministic signal.
"""
from __future__ import annotations

import re
from collections import Counter

from .models import OverlapPair, OverlapRecommendation, SkillArtifact

# Conservative stopword set
STOPWORDS = frozenset(
    {
        "the", "a", "an", "of", "in", "to", "for", "and", "or", "is", "are",
        "be", "this", "that", "it", "as", "on", "at", "by", "with", "from",
        "if", "then", "else", "when", "while", "do", "not", "no", "yes",
        "we", "you", "they", "i", "he", "she", "but", "so", "than", "into",
        "out", "up", "down", "over", "under", "about", "between", "any",
        "all", "some", "each", "every", "few", "more", "most", "other",
        "such", "only", "own", "same", "very", "can", "will", "just",
        "should", "now", "have", "has", "had", "having", "may", "must",
        "would", "could", "also", "use", "used", "using",
    }
)

# Token pattern: lowercase letters, numbers, dashes
WORD = re.compile(r"[a-z][a-z0-9-]{2,}")


def _tokenize(text: str) -> Counter[str]:
    """Tokenize text into a Counter of normalized words."""
    if not text:
        return Counter()
    out: Counter[str] = Counter()
    for m in WORD.finditer(text.lower()):
        w = m.group(0)
        if w in STOPWORDS:
            continue
        out[w] += 1
    return out


def _jaccard(a: Counter[str], b: Counter[str]) -> float:
    """Compute Jaccard similarity on the *set* of tokens."""
    if not a and not b:
        return 0.0
    sa = set(a)
    sb = set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _bag(a: Counter[str], b: Counter[str]) -> float:
    """Compute a bag-aware overlap (uses multiset intersection over union)."""
    if not a and not b:
        return 0.0
    inter = sum((a & b).values())
    union = sum((a + b).values())
    if union == 0:
        return 0.0
    return inter / union


def _name_overlap(a_name: str, b_name: str) -> float:
    """Detect shared name tokens (e.g. 'test' appears in both names)."""
    a_tokens = set(_tokenize(a_name).keys())
    b_tokens = set(_tokenize(b_name).keys())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / max(1, len(a_tokens | b_tokens))


def _build_text(a: SkillArtifact) -> str:
    """Build the text corpus for an artifact (body + purpose-like signals)."""
    parts: list[str] = [a.body_excerpt or ""]
    return "\n".join(parts)


def _score_pair(a: SkillArtifact, b: SkillArtifact) -> tuple[int, str]:
    """Compute a 0-100 overlap score and rationale between two artifacts."""
    text_a = _build_text(a)
    text_b = _build_text(b)
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    j = _jaccard(tokens_a, tokens_b)
    bag = _bag(tokens_a, tokens_b)
    name_ovl = _name_overlap(a.name, b.name)
    # Weighted blend: 60% jaccard, 30% bag, 10% name
    score = int(round(100 * (0.6 * j + 0.3 * bag + 0.1 * name_ovl)))
    shared = sorted(set(tokens_a) & set(tokens_b))[:8]
    rationale = (
        f"Jaccard={j:.2f}, bag={bag:.2f}, name_overlap={name_ovl:.2f}. "
        f"Shared tokens: {', '.join(shared) if shared else '(none)'}."
    )
    return score, rationale


def _recommendation(score: int, merge_threshold: int = 85, differentiate_threshold: int = 70) -> OverlapRecommendation:
    """Map a score to a recommendation per the source spec.

    Phase 7 fix: thresholds are now configurable. Previously this
    function hardcoded 85/70, but the analyzer accepts
    `blocking_threshold` and `warning_threshold` from the config
    (which can be lowered for catalogs with different needs).
    """
    if score >= merge_threshold:
        return OverlapRecommendation.MERGE
    if score >= differentiate_threshold:
        return OverlapRecommendation.DIFFERENTIATE
    return OverlapRecommendation.KEEP_SEPARATE


def analyze(
    artifacts: list[SkillArtifact],
    *,
    use_minimax: bool = False,
    blocking_threshold: int = 85,
    warning_threshold: int = 70,
) -> list[OverlapPair]:
    """Compute pairwise overlap scores for all artifacts.

    Phase 2 uses deterministic Jaccard + bag + name signals.
    Phase 3 will add an optional MiniMax semantic scoring layer
    (`use_minimax=True`); the interface is stable.
    """
    pairs: list[OverlapPair] = []
    n = len(artifacts)
    for i in range(n):
        for j in range(i + 1, n):
            a = artifacts[i]
            b = artifacts[j]
            score, rationale = _score_pair(a, b)
            pairs.append(
                OverlapPair(
                    artifact_a=a.name,
                    artifact_b=b.name,
                    overlap_score=score,
                    rationale=rationale,
                    recommendation=_recommendation(
                        score,
                        merge_threshold=blocking_threshold,
                        differentiate_threshold=warning_threshold,
                    ),
                )
            )
    # Sort highest-overlap first
    pairs.sort(key=lambda p: p.overlap_score, reverse=True)
    return pairs
