"""
Investor, Watchlist, Holding, Alert, and NotificationLog models for PSX WhatsApp tool.

Identity anchor: investor.whatsapp_number (E.164 format, e.g. +923001234567).
No username/password — WhatsApp number is the verified identity provided by Meta.
"""
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class Investor(Base):
    """
    A registered PSX investor who receives notifications via WhatsApp.
    Created automatically on first inbound message; profile filled in
    during the onboarding conversation flow.
    """
    __tablename__ = "investors"

    investor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)

    # Notification preferences
    preferred_language = Column(String(20), default="en")   # "en" | "ur" | "roman_ur"
    notifications_enabled = Column(Boolean, default=True)
    morning_brief_enabled = Column(Boolean, default=False)
    morning_brief_time = Column(String(5), default="09:15")  # HH:MM PKT

    # Onboarding state — tracks where in the WhatsApp flow the user is
    onboarding_step = Column(String(50), default="new")
    # "new" → "name_asked" → "language_asked" → "complete"
    is_onboarded = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )


class Watchlist(Base):
    """
    Stocks an investor wants to monitor.
    A watchlist entry does not imply ownership — use Holding for that.
    """
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id = Column(
        UUID(as_uuid=True), ForeignKey("investors.investor_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    symbol = Column(String(20), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("investor_id", "symbol", name="uq_watchlist_investor_symbol"),
    )


class Holding(Base):
    """
    A stock position in an investor's self-reported portfolio.
    quantity and avg_buy_price are manually entered — not synced with CDC.
    """
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id = Column(
        UUID(as_uuid=True), ForeignKey("investors.investor_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)           # Number of shares
    avg_buy_price = Column(Float, nullable=False)      # PKR per share
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("investor_id", "symbol", name="uq_holding_investor_symbol"),
    )


class Alert(Base):
    """
    A price or change-percent alert set by an investor on a PSX symbol.

    condition values:
      "above"           — fire when current_price >= target_value (PKR)
      "below"           — fire when current_price <= target_value (PKR)
      "change_pct_up"   — fire when day gain % >= target_value
      "change_pct_down" — fire when day loss % >= target_value (positive number, e.g. 3 = -3%)

    one_shot: if True, alert is deactivated after the first trigger.
    """
    __tablename__ = "alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id = Column(
        UUID(as_uuid=True), ForeignKey("investors.investor_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    symbol = Column(String(20), nullable=False, index=True)
    condition = Column(String(30), nullable=False)     # see docstring above
    target_value = Column(Float, nullable=False)       # price in PKR or percentage
    one_shot = Column(Boolean, default=True)           # deactivate after first trigger
    is_active = Column(Boolean, default=True, index=True)
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )


class NotificationLog(Base):
    """
    Immutable audit log of every WhatsApp message sent to an investor.
    status: "sent" | "failed" | "pending"
    notification_type: "alert" | "morning_brief" | "eod_summary" | "manual" | "onboarding"
    """
    __tablename__ = "notification_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id = Column(
        UUID(as_uuid=True), ForeignKey("investors.investor_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    alert_id = Column(
        UUID(as_uuid=True), ForeignKey("alerts.alert_id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_type = Column(String(30), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    wa_message_id = Column(String(255), nullable=True)  # from WhatsApp API response
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
