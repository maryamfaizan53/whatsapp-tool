"""
Pydantic schemas for Investor, Watchlist, Holding, Alert, and NotificationLog.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Investor
# ---------------------------------------------------------------------------

VALID_LANGUAGES = {"en", "ur", "roman_ur"}
VALID_ONBOARDING_STEPS = {"new", "name_asked", "language_asked", "complete"}


class InvestorCreate(BaseModel):
    """Minimal data required to register a new investor."""
    whatsapp_number: str = Field(
        ...,
        description="E.164 format, e.g. +923001234567",
        examples=["+923001234567"],
    )
    name: Optional[str] = None
    preferred_language: str = "en"

    @field_validator("whatsapp_number")
    @classmethod
    def validate_wa_number(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("+"):
            raise ValueError("whatsapp_number must be in E.164 format starting with '+'")
        digits = v[1:]
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise ValueError("whatsapp_number contains invalid characters or wrong length")
        return v

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in VALID_LANGUAGES:
            raise ValueError(f"preferred_language must be one of {VALID_LANGUAGES}")
        return v


class InvestorUpdate(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    morning_brief_enabled: Optional[bool] = None
    morning_brief_time: Optional[str] = Field(
        None, pattern=r"^\d{2}:\d{2}$", description="HH:MM in PKT"
    )

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LANGUAGES:
            raise ValueError(f"preferred_language must be one of {VALID_LANGUAGES}")
        return v


class InvestorResponse(BaseModel):
    investor_id: UUID
    whatsapp_number: str
    name: Optional[str]
    preferred_language: str
    notifications_enabled: bool
    morning_brief_enabled: bool
    morning_brief_time: str
    is_onboarded: bool
    onboarding_step: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="PSX ticker, e.g. ENGRO")

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


class WatchlistItem(BaseModel):
    id: UUID
    investor_id: UUID
    symbol: str
    added_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Holding (Portfolio)
# ---------------------------------------------------------------------------

class HoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: float = Field(..., gt=0, description="Number of shares held")
    avg_buy_price: float = Field(..., gt=0, description="Average buy price in PKR per share")
    notes: Optional[str] = None

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    avg_buy_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class HoldingResponse(BaseModel):
    id: UUID
    investor_id: UUID
    symbol: str
    quantity: float
    avg_buy_price: float
    notes: Optional[str]
    added_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    """Enriched holding with live price data for P&L calculation."""
    holding: HoldingResponse
    current_price: Optional[float]
    market_value: Optional[float]       # quantity × current_price
    cost_basis: float                   # quantity × avg_buy_price
    unrealized_pnl: Optional[float]     # market_value − cost_basis
    unrealized_pnl_pct: Optional[float] # unrealized_pnl / cost_basis × 100
    day_change: Optional[float]         # price change today
    day_change_pct: Optional[float]


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------

AlertCondition = Literal["above", "below", "change_pct_up", "change_pct_down"]

CONDITION_DESCRIPTIONS = {
    "above":           "Fires when price rises above target (PKR)",
    "below":           "Fires when price falls below target (PKR)",
    "change_pct_up":   "Fires when day gain % >= target (e.g. 3 = +3%)",
    "change_pct_down": "Fires when day loss % >= target (e.g. 3 = -3%)",
}


class AlertCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    condition: AlertCondition
    target_value: float = Field(..., gt=0)
    one_shot: bool = Field(True, description="Deactivate after first trigger")
    expires_at: Optional[datetime] = None

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


class AlertUpdate(BaseModel):
    target_value: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    one_shot: Optional[bool] = None
    expires_at: Optional[datetime] = None


class AlertResponse(BaseModel):
    alert_id: UUID
    investor_id: UUID
    symbol: str
    condition: str
    target_value: float
    one_shot: bool
    is_active: bool
    trigger_count: int
    last_triggered_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    def describe(self) -> str:
        """Human-readable description of the alert condition."""
        desc = CONDITION_DESCRIPTIONS.get(self.condition, self.condition)
        if self.condition in ("above", "below"):
            return f"{self.symbol} {self.condition} Rs {self.target_value:,.2f}"
        return f"{self.symbol} day change {'+' if 'up' in self.condition else '-'}{self.target_value:.1f}%"


class AlertCheckResult(BaseModel):
    """Result of checking a single alert against live market data."""
    alert_id: UUID
    investor_id: UUID
    symbol: str
    triggered: bool
    current_value: Optional[float]    # price or change_pct at check time
    target_value: float
    condition: str
    message: Optional[str] = None     # WhatsApp message to send if triggered


# ---------------------------------------------------------------------------
# Notification Log
# ---------------------------------------------------------------------------

class NotificationLogResponse(BaseModel):
    log_id: UUID
    investor_id: UUID
    alert_id: Optional[UUID]
    notification_type: str
    message: str
    status: str
    wa_message_id: Optional[str]
    error: Optional[str]
    sent_at: datetime

    model_config = {"from_attributes": True}
