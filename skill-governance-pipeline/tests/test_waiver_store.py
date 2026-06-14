"""Tests for the waiver store."""
from __future__ import annotations

from datetime import date

from skill_governance.models import Waiver
from skill_governance.waiver_store import (
    active_waivers,
    is_waiver_active,
    load_waivers,
)


def test_load_waivers_from_list_yaml(tmp_path):
    """A list of waiver dicts loads cleanly."""
    p = tmp_path / "waivers.yaml"
    p.write_text(
        """- waiver_id: w1
  finding_id: f1
  owner: justin
  expiration_date: "2099-01-01"
  rationale: "accepted risk"
  approved_by: justin
- waiver_id: w2
  finding_id: f2
  owner: justin
  expiration_date: "2099-12-31"
  rationale: "another"
  approved_by: justin
"""
    )
    waivers = load_waivers(p)
    assert len(waivers) == 2
    assert waivers[0].waiver_id == "w1"
    assert waivers[0].finding_id == "f1"


def test_load_waivers_from_dict_yaml(tmp_path):
    """A dict with a 'waivers' key loads cleanly."""
    p = tmp_path / "waivers.yaml"
    p.write_text(
        """waivers:
  - waiver_id: w1
    finding_id: f1
    owner: justin
    expiration_date: "2099-01-01"
    rationale: "x"
    approved_by: justin
"""
    )
    waivers = load_waivers(p)
    assert len(waivers) == 1


def test_load_waivers_missing_file(tmp_path):
    """A non-existent file returns an empty list."""
    assert load_waivers(tmp_path / "missing.yaml") == []


def test_load_waivers_invalid_entry_is_skipped(tmp_path):
    """An entry missing required fields is silently skipped."""
    p = tmp_path / "waivers.yaml"
    p.write_text(
        """- waiver_id: w1
  finding_id: f1
  owner: justin
  expiration_date: "2099-01-01"
  rationale: "x"
  approved_by: justin
- waiver_id: w2
  # missing fields
"""
    )
    waivers = load_waivers(p)
    assert len(waivers) == 1
    assert waivers[0].waiver_id == "w1"


def test_is_waiver_active_future():
    """A future expiration is active."""
    w = Waiver(
        waiver_id="w1", finding_id="f1", owner="o",
        expiration_date="2099-01-01", rationale="r", approved_by="a",
    )
    assert is_waiver_active(w, today=date(2026, 6, 14)) is True


def test_is_waiver_active_past():
    """A past expiration is not active."""
    w = Waiver(
        waiver_id="w1", finding_id="f1", owner="o",
        expiration_date="2020-01-01", rationale="r", approved_by="a",
    )
    assert is_waiver_active(w, today=date(2026, 6, 14)) is False


def test_is_waiver_active_today():
    """An expiration equal to today is still active."""
    w = Waiver(
        waiver_id="w1", finding_id="f1", owner="o",
        expiration_date="2026-06-14", rationale="r", approved_by="a",
    )
    assert is_waiver_active(w, today=date(2026, 6, 14)) is True


def test_active_waivers_filters_expired():
    """active_waivers returns only non-expired entries."""
    w_active = Waiver(
        waiver_id="w1", finding_id="f1", owner="o",
        expiration_date="2099-01-01", rationale="r", approved_by="a",
    )
    w_expired = Waiver(
        waiver_id="w2", finding_id="f2", owner="o",
        expiration_date="2020-01-01", rationale="r", approved_by="a",
    )
    active = active_waivers([w_active, w_expired], today=date(2026, 6, 14))
    assert len(active) == 1
    assert active[0].waiver_id == "w1"
