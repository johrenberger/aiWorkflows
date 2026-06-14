"""BDD-TDD coverage tests for CTA-GAP-010: utils.parse_iso_timestamp round-trip.

Triggered by application-test-coverage (FOCUSED_PICKS2 pass) on the
component-test-analysis gap-backlog. CTA-GAP-010 is a P3 gap (T3 risk):

    "utils.parse_iso_timestamp accepts 'Z' suffix but the corresponding
    inverse utils.utc_now_iso produces 'Z'-suffixed output. No round-trip
    test exists. Risk: if utc_now_iso() is changed to use '+00:00' instead
    of 'Z', the parser would still work, but the format would be
    inconsistent across the system."

The round-trip is the canonical contract: any value produced by
utc_now_iso() should be parseable by parse_iso_timestamp() and should
yield an equivalent datetime.

These tests lock:
- parse_iso_timestamp(utc_now_iso()) returns a non-None datetime
- The returned datetime's year/month/day/hour match the wall clock at
  the time of the call (within a small tolerance)
- The format of utc_now_iso() ends in 'Z' (the 'Z' suffix)
- The returned datetime has UTC offset (timezone-aware)

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from skill_governance.utils import parse_iso_timestamp, utc_now_iso


# ===========================================================================
# SCENARIO 1: parse_iso_timestamp(utc_now_iso()) round-trip succeeds
#
# Given: the current time, formatted as an ISO 8601 string by utc_now_iso
# When:  parse_iso_timestamp is called on that string
# Then:  returns a non-None datetime
# ===========================================================================
def test_round_trip_returns_non_none_datetime():
    """parse_iso_timestamp(utc_now_iso()) returns a non-None datetime."""
    iso = utc_now_iso()
    result = parse_iso_timestamp(iso)
    assert result is not None, f"round-trip of {iso!r} returned None"


# ===========================================================================
# SCENARIO 2: utc_now_iso() output ends in 'Z' (the format lock)
#
# Given: a call to utc_now_iso()
# When:  the returned string is inspected
# Then:  it ends with the 'Z' suffix (not '+00:00')
# ===========================================================================
def test_utc_now_iso_output_ends_in_z():
    """utc_now_iso() returns an ISO 8601 string with the 'Z' suffix (not '+00:00')."""
    iso = utc_now_iso()
    assert iso.endswith("Z"), f"utc_now_iso() output should end in 'Z'; got {iso!r}"
    # Sanity: should NOT also end in '+00:00'
    assert not iso.endswith("+00:00"), f"utc_now_iso() should not produce '+00:00' suffix; got {iso!r}"


# ===========================================================================
# SCENARIO 3: the format of utc_now_iso() is YYYY-MM-DDTHH:MM:SSZ
#
# Given: a call to utc_now_iso()
# When:  the returned string is matched against a regex
# Then:  it matches the canonical format
# ===========================================================================
def test_utc_now_iso_format_is_canonical_iso_8601_z_suffixed():
    """utc_now_iso() output matches the regex r'\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z'."""
    iso = utc_now_iso()
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    assert pattern.match(iso), f"utc_now_iso() output {iso!r} does not match canonical format"


# ===========================================================================
# SCENARIO 4: the round-tripped datetime is timezone-aware (UTC)
#
# Given: utc_now_iso() output
# When:  parse_iso_timestamp parses it
# Then:  the resulting datetime has tzinfo set (UTC-aware)
# ===========================================================================
def test_round_tripped_datetime_is_timezone_aware():
    """The datetime from the round-trip is timezone-aware (UTC)."""
    iso = utc_now_iso()
    result = parse_iso_timestamp(iso)
    assert result is not None
    assert result.tzinfo is not None, (
        f"round-tripped datetime should be timezone-aware; got tzinfo={result.tzinfo}"
    )
    # The offset should be UTC (or zero)
    assert result.utcoffset().total_seconds() == 0, (
        f"round-tripped datetime should have UTC offset; got {result.utcoffset()}"
    )


# ===========================================================================
# SCENARIO 5: the round-tripped datetime year/month/day matches the
#        actual wall clock at call time
#
# Given: a call to utc_now_iso() at time T
# When:  the round-trip datetime is compared to datetime.now(UTC) at
#        the same moment
# Then:  the year/month/day should be equal (within a small tolerance
#        for sub-second precision)
# ===========================================================================
def test_round_trip_preserves_date_components():
    """The round-tripped datetime's date matches the actual current UTC date."""
    before = datetime.now(timezone.utc)
    iso = utc_now_iso()
    after = datetime.now(timezone.utc)
    result = parse_iso_timestamp(iso)
    assert result is not None
    # The result's date should be between `before.date()` and `after.date()`
    assert before.date() <= result.date() <= after.date(), (
        f"round-trip date {result.date()} outside expected range "
        f"[{before.date()}, {after.date()}]"
    )


# ===========================================================================
# SCENARIO 6: parse_iso_timestamp accepts both 'Z' and '+00:00' formats
#        (lock the parser's flexibility)
#
# Given: a string ending in 'Z' and an equivalent string ending in '+00:00'
# When:  parse_iso_timestamp is called on each
# Then:  both yield equivalent datetimes
# ===========================================================================
def test_parse_iso_timestamp_accepts_both_z_and_offset_formats():
    """parse_iso_timestamp() accepts both 'Z'-suffixed and '+00:00'-suffixed strings."""
    z_form = "2026-06-13T22:00:00Z"
    offset_form = "2026-06-13T22:00:00+00:00"
    z_result = parse_iso_timestamp(z_form)
    offset_result = parse_iso_timestamp(offset_form)
    assert z_result is not None and offset_result is not None
    # Both should yield the same instant in time
    assert z_result == offset_result, (
        f"Z form and offset form should yield the same datetime; got {z_result} vs {offset_result}"
    )
