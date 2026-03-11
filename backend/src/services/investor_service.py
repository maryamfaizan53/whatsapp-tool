"""
Investor Service — CRUD for Investor, Watchlist, Holding, Alert, NotificationLog.

All write operations are synchronous (SQLAlchemy sync session).
The alert checker is designed to be called by the Celery beat scheduler.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.investor import Alert, Holding, Investor, NotificationLog, Watchlist
from ..schemas.investor import (
    AlertCheckResult,
    AlertCreate,
    AlertUpdate,
    HoldingCreate,
    HoldingUpdate,
    InvestorCreate,
    InvestorUpdate,
    PortfolioSummary,
    WatchlistAdd,
)
from ..schemas.psx import StockQuote
from ..services.psx_service import psx_service

logger = logging.getLogger(__name__)
PKT = ZoneInfo("Asia/Karachi")


# ---------------------------------------------------------------------------
# Investor CRUD
# ---------------------------------------------------------------------------

class InvestorService:

    # ---- Investor ----------------------------------------------------------

    def get_by_whatsapp(self, wa_number: str, db: Session) -> Optional[Investor]:
        return (
            db.query(Investor)
            .filter(Investor.whatsapp_number == wa_number, Investor.is_active == True)
            .first()
        )

    def get_by_id(self, investor_id: UUID, db: Session) -> Optional[Investor]:
        return (
            db.query(Investor)
            .filter(Investor.investor_id == investor_id, Investor.is_active == True)
            .first()
        )

    def get_or_create(self, wa_number: str, db: Session) -> tuple[Investor, bool]:
        """
        Returns (investor, created).
        Creates a minimal investor record on first contact; caller runs
        the onboarding flow to fill in remaining fields.
        """
        investor = self.get_by_whatsapp(wa_number, db)
        if investor:
            return investor, False

        investor = Investor(whatsapp_number=wa_number)
        db.add(investor)
        try:
            db.commit()
            db.refresh(investor)
        except IntegrityError:
            db.rollback()
            # Race condition: another request created it first
            investor = self.get_by_whatsapp(wa_number, db)
        return investor, True

    def create(self, data: InvestorCreate, db: Session) -> Investor:
        investor = Investor(
            whatsapp_number=data.whatsapp_number,
            name=data.name,
            preferred_language=data.preferred_language,
        )
        db.add(investor)
        db.commit()
        db.refresh(investor)
        return investor

    def update(self, investor: Investor, data: InvestorUpdate, db: Session) -> Investor:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(investor, field, value)
        db.commit()
        db.refresh(investor)
        return investor

    def complete_onboarding(self, investor: Investor, db: Session) -> Investor:
        investor.is_onboarded = True
        investor.onboarding_step = "complete"
        db.commit()
        db.refresh(investor)
        return investor

    def advance_onboarding(
        self, investor: Investor, step: str, db: Session
    ) -> Investor:
        investor.onboarding_step = step
        db.commit()
        db.refresh(investor)
        return investor

    def deactivate(self, investor: Investor, db: Session) -> None:
        investor.is_active = False
        db.commit()

    # ---- Watchlist ---------------------------------------------------------

    def add_to_watchlist(
        self, investor_id: UUID, data: WatchlistAdd, db: Session
    ) -> tuple[Watchlist, bool]:
        """Returns (item, created). No error if symbol already in watchlist."""
        existing = (
            db.query(Watchlist)
            .filter(
                Watchlist.investor_id == investor_id,
                Watchlist.symbol == data.symbol,
            )
            .first()
        )
        if existing:
            return existing, False

        item = Watchlist(investor_id=investor_id, symbol=data.symbol)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item, True

    def remove_from_watchlist(
        self, investor_id: UUID, symbol: str, db: Session
    ) -> bool:
        item = (
            db.query(Watchlist)
            .filter(
                Watchlist.investor_id == investor_id,
                Watchlist.symbol == symbol.upper(),
            )
            .first()
        )
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    def get_watchlist(self, investor_id: UUID, db: Session) -> List[Watchlist]:
        return (
            db.query(Watchlist)
            .filter(Watchlist.investor_id == investor_id)
            .order_by(Watchlist.added_at)
            .all()
        )

    # ---- Holdings ----------------------------------------------------------

    def add_holding(
        self, investor_id: UUID, data: HoldingCreate, db: Session
    ) -> Holding:
        existing = (
            db.query(Holding)
            .filter(
                Holding.investor_id == investor_id,
                Holding.symbol == data.symbol,
            )
            .first()
        )
        if existing:
            # Update existing position (weighted average price)
            total_qty = existing.quantity + data.quantity
            existing.avg_buy_price = (
                (existing.quantity * existing.avg_buy_price)
                + (data.quantity * data.avg_buy_price)
            ) / total_qty
            existing.quantity = total_qty
            if data.notes:
                existing.notes = data.notes
            db.commit()
            db.refresh(existing)
            return existing

        holding = Holding(
            investor_id=investor_id,
            symbol=data.symbol,
            quantity=data.quantity,
            avg_buy_price=data.avg_buy_price,
            notes=data.notes,
        )
        db.add(holding)
        db.commit()
        db.refresh(holding)
        return holding

    def update_holding(
        self, holding: Holding, data: HoldingUpdate, db: Session
    ) -> Holding:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(holding, field, value)
        db.commit()
        db.refresh(holding)
        return holding

    def remove_holding(self, investor_id: UUID, symbol: str, db: Session) -> bool:
        holding = (
            db.query(Holding)
            .filter(
                Holding.investor_id == investor_id,
                Holding.symbol == symbol.upper(),
            )
            .first()
        )
        if not holding:
            return False
        db.delete(holding)
        db.commit()
        return True

    def get_holdings(self, investor_id: UUID, db: Session) -> List[Holding]:
        return (
            db.query(Holding)
            .filter(Holding.investor_id == investor_id)
            .order_by(Holding.symbol)
            .all()
        )

    def get_portfolio_summary(
        self, investor_id: UUID, db: Session
    ) -> List[PortfolioSummary]:
        """
        Fetch live quotes for all holdings and compute unrealised P&L.
        Returns one PortfolioSummary per holding, sorted by symbol.
        """
        from ..schemas.investor import HoldingResponse

        holdings = self.get_holdings(investor_id, db)
        if not holdings:
            return []

        symbols = [h.symbol for h in holdings]
        quotes: dict[str, StockQuote] = {
            q.symbol: q for q in psx_service.get_multiple_quotes(symbols)
        }

        summaries = []
        for h in holdings:
            quote = quotes.get(h.symbol)
            cost_basis = h.quantity * h.avg_buy_price

            if quote:
                market_value = h.quantity * quote.current_price
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis else None
            else:
                market_value = unrealized_pnl = unrealized_pnl_pct = None

            summaries.append(
                PortfolioSummary(
                    holding=HoldingResponse.model_validate(h),
                    current_price=quote.current_price if quote else None,
                    market_value=market_value,
                    cost_basis=cost_basis,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    day_change=quote.change if quote else None,
                    day_change_pct=quote.change_pct if quote else None,
                )
            )
        return summaries

    def format_portfolio_whatsapp(
        self, summaries: List[PortfolioSummary]
    ) -> str:
        """Build a WhatsApp-ready portfolio message."""
        if not summaries:
            return "Your portfolio is empty. Send 'add ENGRO 100 shares at 290' to add a holding."

        lines = ["*Your Portfolio*", ""]
        total_cost = total_value = 0.0
        has_prices = False

        for s in summaries:
            cost = s.cost_basis
            total_cost += cost
            line = f"*{s.holding.symbol}* — {s.holding.quantity:,.0f} shares @ Rs {s.holding.avg_buy_price:,.2f}"
            if s.current_price is not None:
                has_prices = True
                total_value += s.market_value or 0
                pnl_sign = "+" if (s.unrealized_pnl or 0) >= 0 else ""
                line += (
                    f"\n  Now: Rs {s.current_price:,.2f} | "
                    f"P&L: {pnl_sign}Rs {s.unrealized_pnl:,.2f} "
                    f"({pnl_sign}{s.unrealized_pnl_pct:.2f}%)"
                )
            lines.append(line)

        lines.append("")
        lines.append(f"Cost Basis: Rs {total_cost:,.2f}")
        if has_prices:
            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0
            sign = "+" if total_pnl >= 0 else ""
            lines.append(f"Market Value: Rs {total_value:,.2f}")
            lines.append(
                f"Total P&L: {sign}Rs {total_pnl:,.2f} ({sign}{total_pnl_pct:.2f}%)"
            )
        return "\n".join(lines)

    # ---- Alerts ------------------------------------------------------------

    def create_alert(
        self, investor_id: UUID, data: AlertCreate, db: Session
    ) -> Alert:
        alert = Alert(
            investor_id=investor_id,
            symbol=data.symbol,
            condition=data.condition,
            target_value=data.target_value,
            one_shot=data.one_shot,
            expires_at=data.expires_at,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def update_alert(
        self, alert: Alert, data: AlertUpdate, db: Session
    ) -> Alert:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(alert, field, value)
        db.commit()
        db.refresh(alert)
        return alert

    def delete_alert(self, alert: Alert, db: Session) -> None:
        db.delete(alert)
        db.commit()

    def get_alert(
        self, alert_id: UUID, investor_id: UUID, db: Session
    ) -> Optional[Alert]:
        return (
            db.query(Alert)
            .filter(
                Alert.alert_id == alert_id,
                Alert.investor_id == investor_id,
            )
            .first()
        )

    def get_investor_alerts(
        self, investor_id: UUID, db: Session, active_only: bool = False
    ) -> List[Alert]:
        q = db.query(Alert).filter(Alert.investor_id == investor_id)
        if active_only:
            q = q.filter(Alert.is_active == True)
        return q.order_by(Alert.created_at.desc()).all()

    # ---- Alert checker (called by Celery beat) -----------------------------

    def check_alerts(
        self, db: Session, cooldown_minutes: int = 60
    ) -> List[AlertCheckResult]:
        """
        Evaluate all active alerts against live PSX prices.

        cooldown_minutes: recurring (non-one-shot) alerts cannot re-fire within
        this window after their last trigger. One-shot alerts ignore cooldown
        (they deactivate on first trigger anyway).

        Returns AlertCheckResult for every evaluated alert; caller sends WA
        messages and logs results for triggered ones.
        Expired alerts are deactivated automatically.
        """
        from datetime import timedelta

        now = datetime.now(tz=PKT)
        cooldown_cutoff = now - timedelta(minutes=cooldown_minutes)

        active_alerts: List[Alert] = (
            db.query(Alert)
            .filter(Alert.is_active == True)
            .all()
        )

        if not active_alerts:
            return []

        # Fetch distinct symbols in one batch
        symbols = list({a.symbol for a in active_alerts})
        quotes: dict[str, StockQuote] = {
            q.symbol: q for q in psx_service.get_multiple_quotes(symbols)
        }

        results: List[AlertCheckResult] = []

        for alert in active_alerts:
            # Deactivate expired alerts
            if alert.expires_at and alert.expires_at <= now:
                alert.is_active = False
                db.commit()
                continue

            # Cooldown: skip recurring alerts that fired recently
            if (
                not alert.one_shot
                and alert.last_triggered_at is not None
                and alert.last_triggered_at > cooldown_cutoff
            ):
                continue

            quote = quotes.get(alert.symbol)
            if not quote:
                continue

            triggered, current_val = _evaluate_condition(alert, quote)

            message: Optional[str] = None
            if triggered:
                message = _build_alert_message(alert, quote)
                alert.trigger_count += 1
                alert.last_triggered_at = now
                if alert.one_shot:
                    alert.is_active = False
                db.commit()

            results.append(
                AlertCheckResult(
                    alert_id=alert.alert_id,
                    investor_id=alert.investor_id,
                    symbol=alert.symbol,
                    triggered=triggered,
                    current_value=current_val,
                    target_value=alert.target_value,
                    condition=alert.condition,
                    message=message,
                )
            )

        return results

    # ---- Notification log --------------------------------------------------

    def log_notification(
        self,
        investor_id: UUID,
        notification_type: str,
        message: str,
        db: Session,
        alert_id: Optional[UUID] = None,
        status: str = "pending",
        wa_message_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> NotificationLog:
        log = NotificationLog(
            investor_id=investor_id,
            alert_id=alert_id,
            notification_type=notification_type,
            message=message,
            status=status,
            wa_message_id=wa_message_id,
            error=error,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def update_log_status(
        self,
        log: NotificationLog,
        status: str,
        db: Session,
        wa_message_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> NotificationLog:
        log.status = status
        if wa_message_id:
            log.wa_message_id = wa_message_id
        if error:
            log.error = error
        db.commit()
        db.refresh(log)
        return log

    def get_notification_history(
        self,
        investor_id: UUID,
        db: Session,
        limit: int = 50,
    ) -> List[NotificationLog]:
        return (
            db.query(NotificationLog)
            .filter(NotificationLog.investor_id == investor_id)
            .order_by(NotificationLog.sent_at.desc())
            .limit(limit)
            .all()
        )

    # ---- Investors with morning brief enabled (for Celery) -----------------

    def get_morning_brief_subscribers(self, db: Session) -> List[Investor]:
        return (
            db.query(Investor)
            .filter(
                Investor.is_active == True,
                Investor.morning_brief_enabled == True,
                Investor.notifications_enabled == True,
            )
            .all()
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _evaluate_condition(
    alert: Alert, quote: StockQuote
) -> tuple[bool, Optional[float]]:
    """
    Returns (triggered, current_value).
    current_value is the actual price or pct used in the comparison.
    """
    cond = alert.condition
    target = alert.target_value

    if cond == "above":
        return quote.current_price >= target, quote.current_price
    if cond == "below":
        return quote.current_price <= target, quote.current_price
    if cond == "change_pct_up":
        pct = quote.change_pct or 0.0
        return pct >= target, pct
    if cond == "change_pct_down":
        pct = quote.change_pct or 0.0
        return pct <= -abs(target), pct

    return False, None


def _build_alert_message(alert: Alert, quote: StockQuote) -> str:
    """Compose a WhatsApp-ready alert notification message."""
    direction = "+" if (quote.change or 0) >= 0 else ""
    lines = [
        f"*PSX Alert Triggered*",
        f"Symbol: *{alert.symbol}*",
        f"Current Price: Rs {quote.current_price:,.2f}",
        f"Day Change: {direction}{quote.change or 0:,.2f} ({direction}{quote.change_pct or 0:.2f}%)",
    ]

    if alert.condition == "above":
        lines.append(f"Condition: Price crossed *above* Rs {alert.target_value:,.2f}")
    elif alert.condition == "below":
        lines.append(f"Condition: Price dropped *below* Rs {alert.target_value:,.2f}")
    elif alert.condition == "change_pct_up":
        lines.append(f"Condition: Day gain reached *+{alert.target_value:.1f}%*")
    elif alert.condition == "change_pct_down":
        lines.append(f"Condition: Day loss reached *-{alert.target_value:.1f}%*")

    if alert.one_shot:
        lines.append("_This was a one-time alert and has been deactivated._")
    else:
        lines.append("_Send 'alerts' to manage your alerts._")

    return "\n".join(lines)


# Singleton
investor_service = InvestorService()
