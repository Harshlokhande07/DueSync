from datetime import date, timedelta
import pytest
from duelist.tracker import parse_due_date


def test_parse_dates_relative():
    ref_today = date(2026, 10, 25)  # Sunday
    assert parse_due_date("today", today=ref_today) == ref_today
    assert parse_due_date("tomorrow", today=ref_today) == ref_today + timedelta(days=1)
    assert parse_due_date("next week", today=ref_today) == ref_today + timedelta(days=7)


def test_parse_dates_iso_and_standard():
    ref_today = date(2026, 10, 25)
    assert parse_due_date("2026-11-05", today=ref_today) == date(2026, 11, 5)


def test_parse_dates_year_rollover():
    ref_today = date(2026, 10, 25)
    # June 20 has already passed in 2026, so it must roll over to 2027
    res = parse_due_date("June 20", today=ref_today)
    assert res == date(2027, 6, 20)

    # December 15 is in the future in 2026, so it remains in 2026
    res_future = parse_due_date("December 15", today=ref_today)
    assert res_future == date(2026, 12, 15)


def test_parse_dates_invalid():
    with pytest.raises(ValueError):
        parse_due_date("not-a-valid-date-at-all-12345")
