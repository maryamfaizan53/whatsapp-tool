"""
Unit tests for PSXService.get_market_status().

Patches datetime.now() to control the simulated clock.
No Redis, no HTTP calls — pure time-based logic.

PSX market hours: Monday–Friday, 09:15–15:30 PKT (UTC+5).
Pre-opening session: 09:00–09:15 PKT.
"""
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from src.services.psx_service import PSXService

PKT = ZoneInfo("Asia/Karachi")

# Reference weekday dates (week of 9 Mar 2026)
_DATES = {
    0: (2026, 3, 9),   # Monday
    1: (2026, 3, 10),  # Tuesday
    4: (2026, 3, 13),  # Friday
    5: (2026, 3, 14),  # Saturday
    6: (2026, 3, 15),  # Sunday
}


def _pkt(weekday: int, hour: int, minute: int) -> datetime:
    """Build a timezone-aware PKT datetime for a given weekday and time."""
    y, m, d = _DATES[weekday]
    return datetime(y, m, d, hour, minute, 0, tzinfo=PKT)


def _status(weekday: int, hour: int, minute: int):
    """Run get_market_status() with a mocked clock."""
    svc = PSXService.__new__(PSXService)  # skip __init__ / Redis
    svc._redis = None
    mock_now = _pkt(weekday, hour, minute)
    with patch("src.services.psx_service.datetime") as mock_dt:
        mock_dt.now.return_value = mock_now
        return svc.get_market_status()


# ---------------------------------------------------------------------------
# Weekend
# ---------------------------------------------------------------------------

class TestWeekend:
    def test_saturday_is_closed(self):
        s = _status(5, 11, 0)
        assert s.is_open is False
        assert s.session == "weekend"

    def test_sunday_is_closed(self):
        s = _status(6, 10, 0)
        assert s.is_open is False
        assert s.session == "weekend"

    def test_saturday_opens_at_is_none(self):
        s = _status(5, 9, 0)
        assert s.opens_at is None


# ---------------------------------------------------------------------------
# Pre-market (09:00–09:14 PKT)
# ---------------------------------------------------------------------------

class TestPreMarket:
    def test_9am_is_pre_market(self):
        s = _status(0, 9, 0)
        assert s.is_open is False
        assert s.session == "pre_market"

    def test_9_14_is_pre_market(self):
        s = _status(0, 9, 14)
        assert s.is_open is False
        assert s.session == "pre_market"

    def test_pre_market_shows_open_time(self):
        s = _status(1, 9, 5)
        assert s.opens_at == "09:15"


# ---------------------------------------------------------------------------
# Market open (09:15–15:30 PKT)
# ---------------------------------------------------------------------------

class TestMarketOpen:
    def test_exactly_at_open(self):
        s = _status(0, 9, 15)
        assert s.is_open is True
        assert s.session == "open"

    def test_midday_open(self):
        s = _status(0, 12, 0)
        assert s.is_open is True
        assert s.session == "open"

    def test_exactly_at_close(self):
        s = _status(0, 15, 30)
        assert s.is_open is True
        assert s.session == "open"

    def test_friday_is_open(self):
        s = _status(4, 11, 0)
        assert s.is_open is True

    def test_open_has_close_time(self):
        s = _status(1, 10, 0)
        assert s.closes_at == "15:30"

    def test_open_message_not_empty(self):
        s = _status(0, 10, 0)
        assert len(s.message) > 0


# ---------------------------------------------------------------------------
# Market closed (after 15:30 PKT, same day)
# ---------------------------------------------------------------------------

class TestMarketClosed:
    def test_just_after_close(self):
        s = _status(0, 15, 31)
        assert s.is_open is False
        assert s.session == "closed"

    def test_evening_is_closed(self):
        s = _status(0, 18, 0)
        assert s.is_open is False
        assert s.session == "closed"

    def test_midnight_is_closed(self):
        s = _status(0, 0, 0)
        assert s.is_open is False
        assert s.session in ("closed", "pre_market")

    def test_closed_opens_at_contains_next_day_hint(self):
        s = _status(0, 17, 0)
        assert s.opens_at is not None   # shows next open time


# ---------------------------------------------------------------------------
# Session string consistency
# ---------------------------------------------------------------------------

class TestSessionValues:
    @pytest.mark.parametrize("weekday,hour,minute,expected_session", [
        (0,  9,  5, "pre_market"),   # 09:05 — inside pre-market window (09:00–09:14)
        (0,  9, 15, "open"),
        (0, 15, 30, "open"),
        (0, 15, 31, "closed"),
        (5, 10,  0, "weekend"),
        (6, 10,  0, "weekend"),
    ])
    def test_session_parametrized(self, weekday, hour, minute, expected_session):
        s = _status(weekday, hour, minute)
        assert s.session == expected_session

    def test_market_status_has_pkt_time(self):
        s = _status(0, 10, 30)
        assert "PKT" in s.current_time_pkt
