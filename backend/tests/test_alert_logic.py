"""
Unit tests for alert evaluation logic and cooldown behaviour.

Tests private helpers _evaluate_condition() and _build_alert_message()
directly — no database, no WhatsApp API, no HTTP.

Also tests the cooldown branch of InvestorService.check_alerts()
using mocked DB + quotes.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from src.services.investor_service import (
    _build_alert_message,
    _evaluate_condition,
)
from src.schemas.psx import StockQuote

PKT = ZoneInfo("Asia/Karachi")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _quote(
    symbol: str = "ENGRO",
    price: float = 300.0,
    change: float = 5.0,
    change_pct: float = 1.7,
) -> StockQuote:
    return StockQuote(
        symbol=symbol,
        current_price=price,
        change=change,
        change_pct=change_pct,
        fetched_at=datetime.now(tz=PKT),
        source="test",
    )


def _alert(
    condition: str = "above",
    target: float = 300.0,
    one_shot: bool = True,
    last_triggered: datetime | None = None,
) -> MagicMock:
    a = MagicMock()
    a.alert_id = uuid4()
    a.investor_id = uuid4()
    a.symbol = "ENGRO"
    a.condition = condition
    a.target_value = target
    a.one_shot = one_shot
    a.last_triggered_at = last_triggered
    a.trigger_count = 0
    a.expires_at = None
    a.is_active = True
    return a


# ---------------------------------------------------------------------------
# _evaluate_condition — "above"
# ---------------------------------------------------------------------------

class TestConditionAbove:
    def test_triggers_when_price_equals_target(self):
        triggered, val = _evaluate_condition(_alert("above", 300.0), _quote(price=300.0))
        assert triggered is True
        assert val == pytest.approx(300.0)

    def test_triggers_when_price_exceeds_target(self):
        triggered, _ = _evaluate_condition(_alert("above", 290.0), _quote(price=295.0))
        assert triggered is True

    def test_does_not_trigger_when_below_target(self):
        triggered, _ = _evaluate_condition(_alert("above", 310.0), _quote(price=305.0))
        assert triggered is False

    def test_returns_current_price_as_value(self):
        _, val = _evaluate_condition(_alert("above", 290.0), _quote(price=295.0))
        assert val == pytest.approx(295.0)


# ---------------------------------------------------------------------------
# _evaluate_condition — "below"
# ---------------------------------------------------------------------------

class TestConditionBelow:
    def test_triggers_when_price_equals_target(self):
        triggered, _ = _evaluate_condition(_alert("below", 250.0), _quote(price=250.0))
        assert triggered is True

    def test_triggers_when_price_is_lower(self):
        triggered, _ = _evaluate_condition(_alert("below", 250.0), _quote(price=245.0))
        assert triggered is True

    def test_does_not_trigger_when_above_target(self):
        triggered, _ = _evaluate_condition(_alert("below", 250.0), _quote(price=255.0))
        assert triggered is False


# ---------------------------------------------------------------------------
# _evaluate_condition — "change_pct_up"
# ---------------------------------------------------------------------------

class TestConditionChangePctUp:
    def test_triggers_when_gain_equals_target(self):
        q = _quote(change_pct=3.0)
        triggered, val = _evaluate_condition(_alert("change_pct_up", 3.0), q)
        assert triggered is True
        assert val == pytest.approx(3.0)

    def test_triggers_when_gain_exceeds_target(self):
        q = _quote(change_pct=5.2)
        triggered, _ = _evaluate_condition(_alert("change_pct_up", 3.0), q)
        assert triggered is True

    def test_does_not_trigger_when_gain_below_target(self):
        q = _quote(change_pct=1.5)
        triggered, _ = _evaluate_condition(_alert("change_pct_up", 3.0), q)
        assert triggered is False

    def test_does_not_trigger_on_negative_change(self):
        q = _quote(change_pct=-2.0)
        triggered, _ = _evaluate_condition(_alert("change_pct_up", 3.0), q)
        assert triggered is False


# ---------------------------------------------------------------------------
# _evaluate_condition — "change_pct_down"
# ---------------------------------------------------------------------------

class TestConditionChangePctDown:
    def test_triggers_when_loss_meets_target_magnitude(self):
        q = _quote(change_pct=-3.0)
        triggered, val = _evaluate_condition(_alert("change_pct_down", 3.0), q)
        assert triggered is True
        assert val == pytest.approx(-3.0)

    def test_triggers_when_loss_exceeds_magnitude(self):
        q = _quote(change_pct=-5.0)
        triggered, _ = _evaluate_condition(_alert("change_pct_down", 3.0), q)
        assert triggered is True

    def test_does_not_trigger_on_small_loss(self):
        q = _quote(change_pct=-1.0)
        triggered, _ = _evaluate_condition(_alert("change_pct_down", 3.0), q)
        assert triggered is False

    def test_does_not_trigger_on_positive_change(self):
        q = _quote(change_pct=2.0)
        triggered, _ = _evaluate_condition(_alert("change_pct_down", 3.0), q)
        assert triggered is False


# ---------------------------------------------------------------------------
# _evaluate_condition — unknown condition (defensive)
# ---------------------------------------------------------------------------

class TestUnknownCondition:
    def test_unknown_condition_does_not_trigger(self):
        triggered, val = _evaluate_condition(_alert("invalid_condition", 100.0), _quote())
        assert triggered is False
        assert val is None


# ---------------------------------------------------------------------------
# _build_alert_message  —  content checks
# ---------------------------------------------------------------------------

class TestBuildAlertMessage:
    def test_contains_symbol(self):
        msg = _build_alert_message(_alert("above", 300.0), _quote(symbol="ENGRO"))
        assert "ENGRO" in msg

    def test_contains_target_price(self):
        msg = _build_alert_message(_alert("above", 300.0), _quote())
        assert "300" in msg

    def test_above_direction_in_message(self):
        msg = _build_alert_message(_alert("above", 300.0), _quote())
        assert "above" in msg.lower()

    def test_below_direction_in_message(self):
        msg = _build_alert_message(_alert("below", 250.0), _quote(price=245.0))
        assert "below" in msg.lower()

    def test_change_pct_up_in_message(self):
        msg = _build_alert_message(_alert("change_pct_up", 3.0), _quote())
        assert "3.0" in msg or "3%" in msg or "gain" in msg.lower()

    def test_one_shot_note_present(self):
        msg = _build_alert_message(_alert("above", 300.0, one_shot=True), _quote())
        assert "one-time" in msg.lower() or "deactivated" in msg.lower()

    def test_message_is_non_empty_string(self):
        msg = _build_alert_message(_alert("below", 200.0), _quote())
        assert isinstance(msg, str)
        assert len(msg) > 20


# ---------------------------------------------------------------------------
# Cooldown logic inside check_alerts()
# ---------------------------------------------------------------------------

class TestAlertCooldown:
    """
    These tests verify that check_alerts() skips non-one-shot alerts that
    were triggered within the cooldown window, and evaluates those outside it.
    Uses a mock DB session and mock psx_service.
    """

    def _make_service(self):
        from src.services.investor_service import InvestorService
        return InvestorService()

    def test_recently_triggered_recurring_alert_is_skipped(self):
        svc = self._make_service()
        now = datetime.now(tz=PKT)

        # Alert triggered 5 minutes ago — within 60-min cooldown
        recent_alert = _alert("above", 290.0, one_shot=False, last_triggered=now - timedelta(minutes=5))
        recent_alert.expires_at = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [recent_alert]

        with patch("src.services.investor_service.psx_service") as mock_psx:
            mock_psx.get_multiple_quotes.return_value = [_quote(price=300.0)]
            results = svc.check_alerts(mock_db, cooldown_minutes=60)

        # Alert should be skipped — no result returned for it
        assert all(r.alert_id != recent_alert.alert_id for r in results)

    def test_cooldown_expired_recurring_alert_is_evaluated(self):
        svc = self._make_service()
        now = datetime.now(tz=PKT)

        # Alert triggered 90 minutes ago — outside 60-min cooldown
        old_alert = _alert("above", 290.0, one_shot=False, last_triggered=now - timedelta(minutes=90))
        old_alert.symbol = "ENGRO"
        old_alert.expires_at = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [old_alert]

        with patch("src.services.investor_service.psx_service") as mock_psx:
            mock_psx.get_multiple_quotes.return_value = [_quote(symbol="ENGRO", price=300.0)]
            results = svc.check_alerts(mock_db, cooldown_minutes=60)

        assert len(results) == 1
        assert results[0].triggered is True

    def test_one_shot_alert_ignores_cooldown(self):
        """One-shot alerts have no last_triggered_at until they fire,
        so cooldown should never block them."""
        svc = self._make_service()

        # one_shot=True, never triggered before
        fresh_alert = _alert("above", 290.0, one_shot=True, last_triggered=None)
        fresh_alert.symbol = "ENGRO"
        fresh_alert.expires_at = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [fresh_alert]

        with patch("src.services.investor_service.psx_service") as mock_psx:
            mock_psx.get_multiple_quotes.return_value = [_quote(symbol="ENGRO", price=300.0)]
            results = svc.check_alerts(mock_db, cooldown_minutes=60)

        assert len(results) == 1
        assert results[0].triggered is True

    def test_expired_alert_is_deactivated_and_skipped(self):
        svc = self._make_service()
        now = datetime.now(tz=PKT)

        expired_alert = _alert("above", 290.0)
        expired_alert.expires_at = now - timedelta(hours=1)  # expired 1h ago
        expired_alert.symbol = "ENGRO"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [expired_alert]

        with patch("src.services.investor_service.psx_service") as mock_psx:
            mock_psx.get_multiple_quotes.return_value = [_quote(price=300.0)]
            results = svc.check_alerts(mock_db, cooldown_minutes=60)

        # Alert should be deactivated
        assert expired_alert.is_active is False
        # No triggered result for the expired alert
        triggered = [r for r in results if r.triggered]
        assert len(triggered) == 0

    def test_no_active_alerts_returns_empty_list(self):
        svc = self._make_service()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = svc.check_alerts(mock_db)
        assert results == []
