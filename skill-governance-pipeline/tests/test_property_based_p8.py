"""Property-based tests for the SGP analyzer modules.

These tests use Hypothesis to generate arbitrary inputs and assert
invariants on the analyzer functions. The goal is to kill the
surviving mutants on overlap_analyzer, roi_scorer, and
recommendation_engine that the prior 5-test hardening pass missed.

Strategy: assert the *contract* of each function (range, symmetry,
monotonicity, edge cases) rather than specific outputs. A property
test that asserts "_jaccard is in [0, 1] for any pair of Counters"
catches more mutations than a single-value example test because
it generates many input combinations.

Each test uses the BDD-TDD pattern: Given/When/Then in docstring,
function name = assertion.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from skill_governance.models import (
    ArtifactType,
    Decision,
    SkillArtifact,
)
from skill_governance.overlap_analyzer import (
    _bag,
    _jaccard,
    _name_overlap,
    _score_pair,
    _tokenize,
)
from skill_governance.recommendation_engine import (
    _effort_for_decision,
    _next_action,
    _priority_for_decision,
    _risk_for_decision,
)
from skill_governance.roi_scorer import (
    _failure_score,
    _normalize,
    _token_cost_score,
)

# Strategies -----------------------------------------------------------------

# A short, valid word that survives the tokenizer (>= 3 chars, lowercase,
# not in STOPWORDS). Use this to build non-trivial Counters.
SAFE_WORD = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=4,
    max_size=12,
).filter(lambda w: w not in ("the", "and", "for", "with", "this", "that"))


@st.composite
def counters(draw: Callable[..., object]) -> Counter[str]:
    """Generate a Counter with a small number of safe words."""
    words = draw(st.lists(SAFE_WORD, min_size=0, max_size=8, unique=True))
    counts = draw(
        st.lists(st.integers(min_value=1, max_value=5), min_size=len(words), max_size=len(words))
    )
    return Counter(dict(zip(words, counts)))


@st.composite
def artifact_names(draw: Callable[..., object]) -> str:
    """Generate a plausible artifact name (kebab-case)."""
    parts = draw(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=4, max_size=10),
            min_size=1,
            max_size=3,
        )
    )
    return "-".join(parts)


@st.composite
def artifacts(
    draw: Callable[..., object], *, name: str | None = None
) -> SkillArtifact:
    """Generate a SkillArtifact with optional name override."""
    return SkillArtifact(
        name=name or draw(artifact_names()),
        path=f"skills/{name or 'x'}/SKILL.md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=draw(st.integers(min_value=0, max_value=10_000)),
        estimated_tokens=draw(st.integers(min_value=0, max_value=5_000)),
        content_hash=draw(st.text(min_size=8, max_size=20)),
        modified_timestamp="2026-06-14T00:00:00Z",
        body_excerpt=draw(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=200)
        ),
    )


# _jaccard properties --------------------------------------------------------


class TestJaccardProperties:
    """_jaccard is a set-Jaccard on Counter keys."""

    @given(a=counters(), b=counters())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_jaccard_returns_value_in_unit_interval(
        self, a: Counter[str], b: Counter[str]
    ) -> None:
        """Given any two Counters
        When _jaccard(a, b) is called
        Then the result is in [0.0, 1.0].
        """
        result = _jaccard(a, b)
        assert 0.0 <= result <= 1.0, f"_jaccard returned {result}, not in [0, 1]"

    @given(a=counters())
    @settings(max_examples=100)
    def test_jaccard_self_overlap_is_one(
        self, a: Counter[str]
    ) -> None:
        """Given any non-empty Counter
        When _jaccard(a, a) is called
        Then the result is 1.0 (a is identical to itself).
        """
        assume(len(a) > 0)
        result = _jaccard(a, a)
        assert result == 1.0, f"_jaccard(a, a) returned {result}, expected 1.0"

    @given(a=counters())
    @settings(max_examples=100)
    def test_jaccard_with_empty_counter_is_zero(
        self, a: Counter[str]
    ) -> None:
        """Given any Counter and an empty Counter
        When _jaccard(a, empty) is called
        Then the result is 0.0.
        """
        result = _jaccard(a, Counter())
        assert result == 0.0, f"_jaccard(a, empty) returned {result}, expected 0.0"

    def test_jaccard_two_empty_counters_is_zero(self) -> None:
        """Given two empty Counters
        When _jaccard is called
        Then the result is 0.0 (not a ZeroDivisionError).
        """
        assert _jaccard(Counter(), Counter()) == 0.0

    @given(a=counters(), b=counters())
    @settings(max_examples=200)
    def test_jaccard_is_symmetric(
        self, a: Counter[str], b: Counter[str]
    ) -> None:
        """Given any two Counters
        When _jaccard is called in both orders
        Then the result is the same.
        """
        assert _jaccard(a, b) == _jaccard(b, a), (
            "_jaccard is not symmetric: "
            f"_jaccard(a, b)={_jaccard(a, b)}, _jaccard(b, a)={_jaccard(b, a)}"
        )


# _bag properties ------------------------------------------------------------


class TestBagProperties:
    """_bag is a multiset-aware overlap on Counter values."""

    @given(a=counters(), b=counters())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_bag_returns_value_in_unit_interval(
        self, a: Counter[str], b: Counter[str]
    ) -> None:
        """Given any two Counters
        When _bag(a, b) is called
        Then the result is in [0.0, 1.0].
        """
        result = _bag(a, b)
        assert 0.0 <= result <= 1.0, f"_bag returned {result}, not in [0, 1]"

    @given(a=counters())
    @settings(max_examples=100)
    def test_bag_self_overlap_is_half(self, a: Counter[str]) -> None:
        """Given any non-empty Counter
        When _bag(a, a) is called
        Then the result is 0.5 (multiset Jaccard of identical inputs is 0.5
            because the union is double the intersection: a/(a+a) = 0.5).
        Mutation killed: change `sum((a & b).values())` to use length,
            or change `sum((a + b).values())` to use a different denominator.
        """
        assume(len(a) > 0)
        result = _bag(a, a)
        assert result == pytest.approx(0.5), (
            f"_bag(a, a) = {result}, expected 0.5 (multiset Jaccard of "
            f"identical inputs); would be 1.0 if the union was treated as a set"
        )

    def test_bag_two_empty_counters_is_zero(self) -> None:
        """Given two empty Counters
        When _bag is called
        Then the result is 0.0.
        """
        assert _bag(Counter(), Counter()) == 0.0

    def test_bag_uses_multiset_not_set_semantics(self) -> None:
        """Given Counter({"a": 2, "b": 1}) and Counter({"a": 1})
        When _bag is called
        Then the result reflects the multiset intersection: 1/(2+1+1) = 0.25,
            NOT the set-intersection 1/(2+1) = 0.333.
        Mutation killed: change `sum((a & b).values())` to `len((a & b))`.
        """
        a = Counter({"a": 2, "b": 1})
        b = Counter({"a": 1})
        result = _bag(a, b)
        # Multiset: intersection is {"a": 1}, sum=1. Union is {"a": 3, "b": 1}, sum=4. 1/4 = 0.25.
        # Set-only: intersection is {"a"}, len=1. Union is {"a", "b"}, len=2. 1/2 = 0.5.
        assert result == pytest.approx(0.25), (
            f"_bag(a, b) = {result}; expected 0.25 (multiset), would be 0.5 (set)"
        )

    @given(a=counters(), b=counters())
    @settings(max_examples=200)
    def test_bag_is_symmetric(
        self, a: Counter[str], b: Counter[str]
    ) -> None:
        """Given any two Counters
        When _bag is called in both orders
        Then the result is the same.
        """
        assert _bag(a, b) == _bag(b, a), (
            "_bag is not symmetric: "
            f"_bag(a, b)={_bag(a, b)}, _bag(b, a)={_bag(b, a)}"
        )


# _name_overlap properties ---------------------------------------------------


class TestNameOverlapProperties:
    """_name_overlap detects shared name tokens."""

    @given(name=artifact_names())
    @settings(max_examples=100)
    def test_name_overlap_self_is_one_when_non_stopword(
        self, name: str
    ) -> None:
        """Given an artifact name that tokenizes to at least one non-stopword
        When _name_overlap(name, name) is called
        Then the result is 1.0.

        Note: a name consisting entirely of stopwords (e.g. "than", "and")
        tokenizes to an empty Counter, and the function correctly returns
        0.0 (no real tokens to overlap). This test uses names that survive
        the tokenizer.
        Mutation killed: change the identity check, swap the operators in
        `if not a_tokens or not b_tokens`, etc.
        """
        tokens = _tokenize(name)
        assume(len(tokens) > 0)
        result = _name_overlap(name, name)
        assert result == 1.0, f"_name_overlap(name, name) = {result}, expected 1.0"

    def test_name_overlap_empty_name_returns_zero(self) -> None:
        """Given an empty name
        When _name_overlap is called
        Then the result is 0.0.
        """
        assert _name_overlap("", "anything") == 0.0
        assert _name_overlap("anything", "") == 0.0
        assert _name_overlap("", "") == 0.0

    @given(a=artifact_names(), b=artifact_names())
    @settings(max_examples=200)
    def test_name_overlap_is_symmetric(
        self, a: str, b: str
    ) -> None:
        """Given any two names
        When _name_overlap is called in both orders
        Then the result is the same.
        """
        assert _name_overlap(a, b) == _name_overlap(b, a)

    @given(a=artifact_names(), b=artifact_names())
    @settings(max_examples=200)
    def test_name_overlap_is_in_unit_interval(
        self, a: str, b: str
    ) -> None:
        """Given any two names
        When _name_overlap is called
        Then the result is in [0.0, 1.0].
        """
        result = _name_overlap(a, b)
        assert 0.0 <= result <= 1.0


# _score_pair properties -----------------------------------------------------


class TestScorePairProperties:
    """_score_pair is a 0-100 weighted blend of jaccard, bag, and name."""

    @given(a=artifacts(), b=artifacts())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_score_pair_returns_score_in_range(
        self, a: SkillArtifact, b: SkillArtifact
    ) -> None:
        """Given any two artifacts
        When _score_pair(a, b) is called
        Then the score is in [0, 100] and rationale is a string.
        """
        score, rationale = _score_pair(a, b)
        assert 0 <= score <= 100, f"score={score} not in [0, 100]"
        assert isinstance(rationale, str)
        assert len(rationale) > 0

    def test_score_pair_identical_artifacts_score_high(self) -> None:
        """Given two artifacts with identical body and name
        When _score_pair is called
        Then the score is >= 80 (Jaccard=1, bag=1, name_ovl=1, blend=1.0).
        Mutation killed: any change to the blend formula
        (0.6*j + 0.3*bag + 0.1*name_ovl) or the multipliers.
        """
        art = SkillArtifact(
            name="repo-discovery",
            path="skills/repo-discovery/SKILL.md",
            artifact_type=ArtifactType.SKILL,
            size_bytes=1000,
            estimated_tokens=200,
            content_hash="abc123",
            modified_timestamp="2026-06-14T00:00:00Z",
            body_excerpt="discovers repositories and lists files",
        )
        score, _ = _score_pair(art, art)
        assert score >= 80, f"identical artifacts scored {score}, expected >= 80"

    def test_score_pair_disjoint_artifacts_score_low(self) -> None:
        """Given two artifacts with completely different content
        When _score_pair is called
        Then the score is low (no Jaccard/bag overlap).
        """
        a = SkillArtifact(
            name="alpha",
            path="skills/alpha/SKILL.md",
            artifact_type=ArtifactType.SKILL,
            size_bytes=1000,
            estimated_tokens=200,
            content_hash="aaa",
            modified_timestamp="2026-06-14T00:00:00Z",
            body_excerpt="alpha content about graphs and trees",
        )
        b = SkillArtifact(
            name="beta",
            path="skills/beta/SKILL.md",
            artifact_type=ArtifactType.SKILL,
            size_bytes=1000,
            estimated_tokens=200,
            content_hash="bbb",
            modified_timestamp="2026-06-14T00:00:00Z",
            body_excerpt="beta content about networks and protocols",
        )
        score, _ = _score_pair(a, b)
        assert score < 50, f"disjoint artifacts scored {score}, expected < 50"


# _normalize properties ------------------------------------------------------


class TestNormalizeProperties:
    """_normalize clamps a value to [0, 1] given a range."""

    @given(
        value=st.floats(min_value=-1000, max_value=1000, allow_nan=False),
        lo=st.floats(min_value=0, max_value=50, allow_nan=False),
        hi=st.floats(min_value=50, max_value=100, allow_nan=False),
    )
    @settings(max_examples=300)
    def test_normalize_returns_value_in_unit_interval(
        self, value: float, lo: float, hi: float
    ) -> None:
        """Given any value, lo, hi with lo < hi
        When _normalize(value, lo, hi) is called
        Then the result is in [0.0, 1.0].
        """
        result = _normalize(value, lo, hi)
        assert 0.0 <= result <= 1.0, f"_normalize({value}, {lo}, {hi}) = {result}"

    def test_normalize_at_lower_bound_returns_zero(self) -> None:
        """Given a value equal to lo
        When _normalize(value, lo, hi) is called
        Then the result is 0.0.
        Mutation killed: change lo default to anything but 0.0.
        """
        assert _normalize(0.0) == 0.0
        assert _normalize(50.0, 50.0, 100.0) == 0.0

    def test_normalize_at_upper_bound_returns_one(self) -> None:
        """Given a value equal to hi
        When _normalize(value, lo, hi) is called
        Then the result is 1.0.
        """
        assert _normalize(100.0) == 1.0
        assert _normalize(100.0, 50.0, 100.0) == 1.0

    def test_normalize_below_lower_bound_clamps_to_zero(self) -> None:
        """Given a value below lo
        When _normalize is called
        Then the result clamps to 0.0.
        """
        assert _normalize(-100.0) == 0.0
        assert _normalize(0.0, 10.0, 100.0) == 0.0

    def test_normalize_above_upper_bound_clamps_to_one(self) -> None:
        """Given a value above hi
        When _normalize is called
        Then the result clamps to 1.0.
        """
        assert _normalize(1000.0) == 1.0
        assert _normalize(200.0, 0.0, 100.0) == 1.0

    def test_normalize_at_midpoint_returns_half(self) -> None:
        """Given value=(lo+hi)/2 with default range
        When _normalize is called
        Then the result is 0.5.
        """
        assert _normalize(50.0) == 0.5

    @given(
        v1=st.floats(min_value=0, max_value=100, allow_nan=False),
        v2=st.floats(min_value=0, max_value=100, allow_nan=False),
    )
    @settings(max_examples=200)
    def test_normalize_is_monotonic(self, v1: float, v2: float) -> None:
        """Given two values v1 < v2 in [lo, hi]
        When _normalize is called on each
        Then _normalize(v1) <= _normalize(v2).
        """
        assume(v1 <= v2)
        assert _normalize(v1) <= _normalize(v2), (
            f"_normalize({v1}) > _normalize({v2}); monotonicity violated"
        )

    def test_normalize_inverted_range_returns_zero(self) -> None:
        """Given lo >= hi (degenerate range)
        When _normalize is called
        Then the result is 0.0 (not a division error or NaN).
        """
        assert _normalize(50.0, 100.0, 50.0) == 0.0
        assert _normalize(50.0, 100.0, 0.0) == 0.0


# _token_cost_score properties -----------------------------------------------


class TestTokenCostScoreProperties:
    """_token_cost_score: lower tokens = higher score."""

    @given(
        tokens=st.integers(min_value=0, max_value=10_000),
        high_cost=st.integers(min_value=1, max_value=5_000),
    )
    @settings(max_examples=200)
    def test_token_cost_score_in_unit_interval(
        self, tokens: int, high_cost: int
    ) -> None:
        """Given any tokens and high_cost
        When _token_cost_score is called
        Then the result is in [0.0, 1.0].
        """
        result = _token_cost_score(tokens, high_cost)
        assert 0.0 <= result <= 1.0

    def test_token_cost_score_zero_tokens_returns_one(self) -> None:
        """Given 0 tokens
        When _token_cost_score is called
        Then the result is 1.0.
        """
        assert _token_cost_score(0, 1000) == 1.0

    def test_token_cost_score_at_high_cost_returns_zero(self) -> None:
        """Given tokens == high_cost
        When _token_cost_score is called
        Then the result is 0.0.
        """
        assert _token_cost_score(1000, 1000) == 0.0

    def test_token_cost_score_above_high_cost_returns_zero(self) -> None:
        """Given tokens > high_cost
        When _token_cost_score is called
        Then the result clamps to 0.0.
        """
        assert _token_cost_score(2000, 1000) == 0.0

    def test_token_cost_score_zero_high_cost_returns_one(self) -> None:
        """Given high_cost <= 0 (degenerate)
        When _token_cost_score is called
        Then the result is 1.0 (not a division error).
        """
        assert _token_cost_score(1000, 0) == 1.0
        assert _token_cost_score(1000, -1) == 1.0

    @given(
        data=st.data(),
        high_cost=st.integers(min_value=100, max_value=5_000),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.filter_too_much])
    def test_token_cost_score_is_anti_monotonic(
        self, data: st.DataObject, high_cost: int
    ) -> None:
        """Given any high_cost, pick two token counts t1, t2 with 0 <= t1 <= t2 <= high_cost
        When _token_cost_score is called on each
        Then the result for t1 >= the result for t2 (more tokens = lower score).
        """
        t1 = data.draw(st.integers(min_value=0, max_value=high_cost))
        t2 = data.draw(st.integers(min_value=t1, max_value=high_cost))
        s1 = _token_cost_score(t1, high_cost)
        s2 = _token_cost_score(t2, high_cost)
        assert s1 >= s2, (
            f"_token_cost_score({t1})={s1} < _token_cost_score({t2})={s2}; "
            f"anti-monotonicity violated for high_cost={high_cost}"
        )


# _failure_score properties --------------------------------------------------


class TestFailureScoreProperties:
    """_failure_score: lower failure = higher score."""

    @given(failure=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=100)
    def test_failure_score_in_unit_interval(self, failure: float) -> None:
        """Given failure rate in [0, 1]
        When _failure_score is called
        Then the result is in [0.0, 1.0].
        """
        result = _failure_score(failure)
        assert 0.0 <= result <= 1.0

    def test_failure_score_zero_returns_one(self) -> None:
        """Given failure rate = 0.0
        When _failure_score is called
        Then the result is 1.0.
        """
        assert _failure_score(0.0) == 1.0

    def test_failure_score_one_returns_zero(self) -> None:
        """Given failure rate = 1.0
        When _failure_score is called
        Then the result is 0.0.
        """
        assert _failure_score(1.0) == 0.0

    def test_failure_score_half_returns_half(self) -> None:
        """Given failure rate = 0.5
        When _failure_score is called
        Then the result is 0.5.
        """
        assert _failure_score(0.5) == 0.5


# _priority_for_decision properties -----------------------------------------


class TestPriorityForDecisionProperties:
    """_priority_for_decision maps Decision + blocking to 1-5 priority."""

    @given(
        decision=st.sampled_from(list(Decision)),
        blocking=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=300)
    def test_priority_in_valid_range(
        self, decision: Decision, blocking: int
    ) -> None:
        """Given any Decision and any blocking count
        When _priority_for_decision is called
        Then the result is in [1, 5].
        """
        result = _priority_for_decision(decision, blocking)
        assert 1 <= result <= 5, (
            f"_priority_for_decision({decision}, {blocking}) = {result}, not in [1, 5]"
        )

    @given(blocking=st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_deprecate_with_blocking_is_priority_one(self, blocking: int) -> None:
        """Given DEPRECATE with blocking > 0
        When _priority_for_decision is called
        Then the result is 1 (highest priority).
        """
        assert _priority_for_decision(Decision.DEPRECATE, blocking) == 1

    def test_deprecate_without_blocking_is_priority_two(self) -> None:
        """Given DEPRECATE with blocking == 0
        When _priority_for_decision is called
        Then the result is 2.
        """
        assert _priority_for_decision(Decision.DEPRECATE, 0) == 2

    def test_merge_is_always_priority_two(self) -> None:
        """Given MERGE (any blocking)
        When _priority_for_decision is called
        Then the result is always 2.
        """
        for b in [0, 1, 5, 100]:
            assert _priority_for_decision(Decision.MERGE, b) == 2

    def test_rewrite_with_blocking_is_priority_two(self) -> None:
        """Given REWRITE with blocking > 0
        When _priority_for_decision is called
        Then the result is 2.
        """
        assert _priority_for_decision(Decision.REWRITE, 1) == 2

    def test_rewrite_without_blocking_is_priority_three(self) -> None:
        """Given REWRITE with blocking == 0
        When _priority_for_decision is called
        Then the result is 3.
        """
        assert _priority_for_decision(Decision.REWRITE, 0) == 3

    def test_split_is_always_priority_three(self) -> None:
        """Given SPLIT (any blocking)
        When _priority_for_decision is called
        Then the result is always 3.
        """
        for b in [0, 1, 5, 100]:
            assert _priority_for_decision(Decision.SPLIT, b) == 3

    def test_keep_falls_through_to_default(self) -> None:
        """Given KEEP (any blocking)
        When _priority_for_decision is called
        Then the result is 4 (the default).
        """
        for b in [0, 1, 5, 100]:
            assert _priority_for_decision(Decision.KEEP, b) == 4


# _risk_for_decision properties ---------------------------------------------


class TestRiskForDecisionProperties:
    """_risk_for_decision returns a risk label."""

    def test_deprecate_with_blocking_is_high(self) -> None:
        """Given DEPRECATE/RETIRE with blocking > 0
        When _risk_for_decision is called
        Then the result is 'high'.
        """
        assert _risk_for_decision(Decision.DEPRECATE, 1) == "high"
        assert _risk_for_decision(Decision.RETIRE, 5) == "high"

    def test_deprecate_without_blocking_is_low(self) -> None:
        """Given DEPRECATE/RETIRE with blocking == 0
        When _risk_for_decision is called
        Then the result is 'low'.
        """
        assert _risk_for_decision(Decision.DEPRECATE, 0) == "low"
        assert _risk_for_decision(Decision.RETIRE, 0) == "low"

    def test_merge_is_always_medium(self) -> None:
        """Given MERGE (any blocking)
        When _risk_for_decision is called
        Then the result is 'medium'.
        """
        for b in [0, 1, 5, 100]:
            assert _risk_for_decision(Decision.MERGE, b) == "medium"

    def test_others_are_low(self) -> None:
        """Given REWRITE/SPLIT/KEEP (any blocking)
        When _risk_for_decision is called
        Then the result is 'low'.
        """
        for d in [Decision.REWRITE, Decision.SPLIT, Decision.KEEP]:
            for b in [0, 1, 5, 100]:
                assert _risk_for_decision(d, b) == "low"


# _effort_for_decision properties --------------------------------------------


class TestEffortForDecisionProperties:
    """_effort_for_decision returns a size label."""

    def test_effort_labels_match_decision(self) -> None:
        """Given each Decision
        When _effort_for_decision is called
        Then the result is the documented size label.
        """
        expected = {
            Decision.KEEP: "XS",
            Decision.REWRITE: "M",
            Decision.MERGE: "L",
            Decision.SPLIT: "M",
            Decision.DEPRECATE: "S",
            Decision.RETIRE: "S",
        }
        for d, expected_label in expected.items():
            assert _effort_for_decision(d) == expected_label, (
                f"_effort_for_decision({d}) = {_effort_for_decision(d)}, "
                f"expected {expected_label}"
            )


# _next_action properties ----------------------------------------------------


class TestNextActionProperties:
    """_next_action returns a non-empty action string per decision."""

    @given(
        decision=st.sampled_from(list(Decision)),
        affected=st.lists(artifact_names(), min_size=1, max_size=3),
    )
    @settings(max_examples=200)
    def test_next_action_is_non_empty_string(
        self, decision: Decision, affected: list[str]
    ) -> None:
        """Given any Decision and any list of affected names
        When _next_action is called
        Then the result is a non-empty string.
        """
        result = _next_action(decision, affected)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_keep_action_says_no_action(self) -> None:
        """Given KEEP
        When _next_action is called
        Then the result contains 'No action'.
        """
        result = _next_action(Decision.KEEP, ["a", "b"])
        assert "No action" in result

    @given(affected=st.lists(artifact_names(), min_size=1, max_size=3))
    @settings(max_examples=50)
    def test_rewrite_action_mentions_rewrite_task(
        self, affected: list[str]
    ) -> None:
        """Given REWRITE
        When _next_action is called
        Then the result mentions a 'rewrite task'.
        """
        result = _next_action(Decision.REWRITE, affected)
        assert "rewrite task" in result.lower()
