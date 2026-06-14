"""BDD-TDD coverage tests for waiver_store.py (Batch 3).

Triggered by application-test-coverage assessment: waiver_store.py
was 70% line coverage. Missing lines cover:
- load_waivers: list format, dict with waivers key, missing file, invalid item,
  Waiver construction failure
- is_waiver_active: missing expiration, valid date, ISO format, invalid format
- active_waivers: filters by is_waiver_active

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

from pathlib import Path

from skill_governance.models import Waiver
from skill_governance.waiver_store import (
    active_waivers,
    is_waiver_active,
    load_waivers,
)


def _waiver(waiver_id: str = "w1", expiration: str = "2099-12-31") -> Waiver:
    return Waiver(
        waiver_id=waiver_id,
        finding_id="f1",
        owner="team-x",
        expiration_date=expiration,
        rationale="test waiver",
        approved_by="lead",
    )


# ===========================================================================
# SCENARIO 1: load_waivers returns [] for missing file
# ===========================================================================
def test_load_waivers_returns_empty_for_missing_file(tmp_path: Path):
    """A nonexistent waiver file returns []."""
    result = load_waivers(tmp_path / "missing.yaml")
    assert result == []


# ===========================================================================
# SCENARIO 2: load_waivers handles dict-with-waivers-key format
# ===========================================================================
def test_load_waivers_handles_dict_with_waivers_key(tmp_path: Path):
    """A YAML dict with 'waivers' key parses the list."""
    p = tmp_path / "waivers.yaml"
    p.write_text(
        "waivers:\n"
        "  - waiver_id: w1\n"
        "    finding_id: f1\n"
        "    owner: team-x\n"
        "    expiration_date: '2099-12-31'\n"
        "    rationale: reason\n"
        "    approved_by: lead\n"
    )
    result = load_waivers(p)
    assert len(result) == 1
    assert result[0].waiver_id == "w1"


# ===========================================================================
# SCENARIO 3: load_waivers handles bare-list format
# ===========================================================================
def test_load_waivers_handles_bare_list_format(tmp_path: Path):
    """A YAML list (not wrapped in dict) parses directly."""
    p = tmp_path / "waivers.yaml"
    p.write_text(
        "- waiver_id: w1\n"
        "  finding_id: f1\n"
        "  owner: team-x\n"
        "  expiration_date: '2099-12-31'\n"
        "  rationale: reason\n"
        "  approved_by: lead\n"
    )
    result = load_waivers(p)
    assert len(result) == 1
    assert result[0].waiver_id == "w1"


# ===========================================================================
# SCENARIO 4: load_waivers skips items that fail Waiver construction
# ===========================================================================
def test_load_waivers_skips_invalid_items(tmp_path: Path):
    """Items that fail Waiver construction are skipped (no exception)."""
    p = tmp_path / "waivers.yaml"
    p.write_text(
        "waivers:\n"
        "  - waiver_id: good\n"
        "    finding_id: f1\n"
        "    owner: team-x\n"
        "    expiration_date: '2099-12-31'\n"
        "    rationale: reason\n"
        "    approved_by: lead\n"
        "  - this is not a dict: at all\n"  # this is a string, not a dict
    )
    # The second item is a string, will be skipped
    result = load_waivers(p)
    assert len(result) == 1
    assert result[0].waiver_id == "good"


# ===========================================================================
# SCENARIO 5: load_waivers returns [] for empty file
# ===========================================================================
def test_load_waivers_returns_empty_for_empty_file(tmp_path: Path):
    """An empty YAML file returns []."""
    p = tmp_path / "waivers.yaml"
    p.write_text("")
    result = load_waivers(p)
    assert result == []


# ===========================================================================
# SCENARIO 6: is_waiver_active returns False for missing expiration
# ===========================================================================
def test_is_waiver_active_returns_false_for_missing_expiration():
    """A waiver with no expiration_date is not active."""
    w = _waiver(expiration="")
    assert is_waiver_active(w) is False


# ===========================================================================
# SCENARIO 7: is_waiver_active returns True for future expiration
# ===========================================================================
def test_is_waiver_active_returns_true_for_future_date():
    """A waiver expiring in 2099 is active today."""
    w = _waiver(expiration="2099-12-31")
    assert is_waiver_active(w) is True


# ===========================================================================
# SCENARIO 8: is_waiver_active returns False for past expiration
# ===========================================================================
def test_is_waiver_active_returns_false_for_past_date():
    """A waiver expired in 2000 is not active."""
    w = _waiver(expiration="2000-01-01")
    assert is_waiver_active(w) is False


# ===========================================================================
# SCENARIO 9: is_waiver_active accepts ISO format dates
# ===========================================================================
def test_is_waiver_active_accepts_iso_format_date():
    """A waiver with full ISO datetime in expiration_date is handled."""
    w = _waiver(expiration="2099-12-31T00:00:00")
    assert is_waiver_active(w) is True


# ===========================================================================
# SCENARIO 10: is_waiver_active returns False for invalid date format
# ===========================================================================
def test_is_waiver_active_returns_false_for_invalid_date_format():
    """An unparseable date returns False (not raise)."""
    w = _waiver(expiration="not a date")
    assert is_waiver_active(w) is False


# ===========================================================================
# SCENARIO 11: active_waivers filters by is_waiver_active
# ===========================================================================
def test_active_waivers_filters_by_active_status():
    """active_waivers returns only waivers where is_waiver_active is True."""
    active_w = _waiver(waiver_id="active", expiration="2099-12-31")
    expired_w = _waiver(waiver_id="expired", expiration="2000-01-01")
    result = active_waivers([active_w, expired_w])
    assert len(result) == 1
    assert result[0].waiver_id == "active"


# ===========================================================================
# SCENARIO 12: load_waivers returns [] for malformed YAML
# ===========================================================================
def test_load_waivers_returns_empty_for_malformed_yaml(tmp_path: Path):
    """Invalid YAML returns [] (no exception)."""
    p = tmp_path / "waivers.yaml"
    p.write_text(": this is [broken: yaml:\n  - { unclosed")
    result = load_waivers(p)
    assert result == []


# ===========================================================================
# SCENARIO 13: load_waivers returns [] for non-list-non-dict YAML
# ===========================================================================
def test_load_waivers_returns_empty_for_scalar_yaml(tmp_path: Path):
    """A scalar YAML (string/number) returns [] (not a list or dict)."""
    p = tmp_path / "waivers.yaml"
    p.write_text("42\n")
    result = load_waivers(p)
    assert result == []


# ===========================================================================
# SCENARIO 14: load_waivers skips waivers that fail is_valid
# ===========================================================================
def test_load_waivers_skips_invalid_waivers_missing_required_fields(tmp_path: Path):
    """Waivers missing required fields (failing is_valid) are skipped."""
    p = tmp_path / "waivers.yaml"
    # Missing owner, rationale, approved_by — should fail is_valid
    p.write_text(
        "waivers:\n"
        "  - waiver_id: incomplete\n"
        "    finding_id: f1\n"
        "    expiration_date: '2099-12-31'\n"
    )
    result = load_waivers(p)
    # The incomplete waiver is skipped (is_valid returns False)
    assert result == []
