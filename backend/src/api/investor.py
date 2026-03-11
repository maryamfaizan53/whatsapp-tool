"""
Investor API Endpoints — Registration, Watchlist, Portfolio, Alerts, Notification History.

Auth is intentionally minimal for MVP: investor_id passed in path.
In production, add JWT or phone-OTP middleware.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.investor import Alert, Holding, Investor
from ..schemas.investor import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    HoldingCreate,
    HoldingResponse,
    HoldingUpdate,
    InvestorCreate,
    InvestorResponse,
    InvestorUpdate,
    NotificationLogResponse,
    PortfolioSummary,
    WatchlistAdd,
    WatchlistItem,
)
from ..services.investor_service import investor_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def _get_investor_or_404(investor_id: UUID, db: Session) -> Investor:
    inv = investor_service.get_by_id(investor_id, db)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investor not found")
    return inv


def _get_alert_or_404(alert_id: UUID, investor_id: UUID, db: Session) -> Alert:
    alert = investor_service.get_alert(alert_id, investor_id, db)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


# ---------------------------------------------------------------------------
# Investor registration & profile
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=InvestorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new investor",
)
def register_investor(data: InvestorCreate, db: Session = Depends(get_db)) -> Investor:
    """
    Register a new investor by WhatsApp number.
    Returns 409 if the number is already registered.
    """
    existing = investor_service.get_by_whatsapp(data.whatsapp_number, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"WhatsApp number {data.whatsapp_number} is already registered.",
        )
    return investor_service.create(data, db)


@router.get(
    "/lookup",
    response_model=InvestorResponse,
    summary="Look up investor by WhatsApp number",
)
def lookup_by_whatsapp(
    wa_number: str = Query(..., description="E.164 format, e.g. +923001234567"),
    db: Session = Depends(get_db),
) -> Investor:
    inv = investor_service.get_by_whatsapp(wa_number, db)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investor not found")
    return inv


@router.get(
    "/{investor_id}",
    response_model=InvestorResponse,
    summary="Get investor profile",
)
def get_investor(investor_id: UUID, db: Session = Depends(get_db)) -> Investor:
    return _get_investor_or_404(investor_id, db)


@router.patch(
    "/{investor_id}",
    response_model=InvestorResponse,
    summary="Update investor profile / notification preferences",
)
def update_investor(
    investor_id: UUID, data: InvestorUpdate, db: Session = Depends(get_db)
) -> Investor:
    inv = _get_investor_or_404(investor_id, db)
    return investor_service.update(inv, data, db)


@router.delete(
    "/{investor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate investor account",
)
def deactivate_investor(investor_id: UUID, db: Session = Depends(get_db)) -> None:
    inv = _get_investor_or_404(investor_id, db)
    investor_service.deactivate(inv, db)


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

@router.get(
    "/{investor_id}/watchlist",
    response_model=List[WatchlistItem],
    summary="Get investor's watchlist",
)
def get_watchlist(investor_id: UUID, db: Session = Depends(get_db)) -> list:
    _get_investor_or_404(investor_id, db)
    return investor_service.get_watchlist(investor_id, db)


@router.post(
    "/{investor_id}/watchlist",
    response_model=WatchlistItem,
    status_code=status.HTTP_201_CREATED,
    summary="Add a symbol to watchlist",
)
def add_to_watchlist(
    investor_id: UUID, data: WatchlistAdd, db: Session = Depends(get_db)
) -> object:
    _get_investor_or_404(investor_id, db)
    item, created = investor_service.add_to_watchlist(investor_id, data, db)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{data.symbol} is already in the watchlist.",
        )
    return item


@router.delete(
    "/{investor_id}/watchlist/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a symbol from watchlist",
)
def remove_from_watchlist(
    investor_id: UUID, symbol: str, db: Session = Depends(get_db)
) -> None:
    _get_investor_or_404(investor_id, db)
    removed = investor_service.remove_from_watchlist(investor_id, symbol, db)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{symbol.upper()} not found in watchlist.",
        )


# ---------------------------------------------------------------------------
# Portfolio (Holdings)
# ---------------------------------------------------------------------------

@router.get(
    "/{investor_id}/portfolio",
    response_model=List[PortfolioSummary],
    summary="Get portfolio with live P&L",
)
def get_portfolio(investor_id: UUID, db: Session = Depends(get_db)) -> list:
    """
    Returns all holdings enriched with live PSX prices and unrealised P&L.
    If live prices are unavailable, `current_price` and P&L fields will be null.
    """
    _get_investor_or_404(investor_id, db)
    return investor_service.get_portfolio_summary(investor_id, db)


@router.get(
    "/{investor_id}/portfolio/message",
    response_model=str,
    summary="Portfolio as a WhatsApp-ready text message",
)
def get_portfolio_message(investor_id: UUID, db: Session = Depends(get_db)) -> str:
    _get_investor_or_404(investor_id, db)
    summaries = investor_service.get_portfolio_summary(investor_id, db)
    return investor_service.format_portfolio_whatsapp(summaries)


@router.post(
    "/{investor_id}/portfolio",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or update a holding",
)
def add_holding(
    investor_id: UUID, data: HoldingCreate, db: Session = Depends(get_db)
) -> Holding:
    """
    If the symbol already exists in the portfolio, quantity is added and
    the average buy price is recalculated (weighted average).
    """
    _get_investor_or_404(investor_id, db)
    return investor_service.add_holding(investor_id, data, db)


@router.patch(
    "/{investor_id}/portfolio/{symbol}",
    response_model=HoldingResponse,
    summary="Update quantity or avg buy price for a holding",
)
def update_holding(
    investor_id: UUID,
    symbol: str,
    data: HoldingUpdate,
    db: Session = Depends(get_db),
) -> Holding:
    _get_investor_or_404(investor_id, db)
    holding = (
        db.query(Holding)
        .filter(
            Holding.investor_id == investor_id,
            Holding.symbol == symbol.upper(),
        )
        .first()
    )
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{symbol.upper()} not found in portfolio.",
        )
    return investor_service.update_holding(holding, data, db)


@router.delete(
    "/{investor_id}/portfolio/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a holding from portfolio",
)
def remove_holding(
    investor_id: UUID, symbol: str, db: Session = Depends(get_db)
) -> None:
    _get_investor_or_404(investor_id, db)
    removed = investor_service.remove_holding(investor_id, symbol, db)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{symbol.upper()} not found in portfolio.",
        )


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@router.get(
    "/{investor_id}/alerts",
    response_model=List[AlertResponse],
    summary="List investor's price alerts",
)
def list_alerts(
    investor_id: UUID,
    active_only: bool = Query(False, description="Only return active alerts"),
    db: Session = Depends(get_db),
) -> list:
    _get_investor_or_404(investor_id, db)
    return investor_service.get_investor_alerts(investor_id, db, active_only=active_only)


@router.post(
    "/{investor_id}/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new price alert",
)
def create_alert(
    investor_id: UUID, data: AlertCreate, db: Session = Depends(get_db)
) -> Alert:
    """
    Conditions:
    - **above**: fires when `current_price >= target_value` (PKR)
    - **below**: fires when `current_price <= target_value` (PKR)
    - **change_pct_up**: fires when day gain% >= target_value
    - **change_pct_down**: fires when day loss% >= target_value (magnitude)
    """
    _get_investor_or_404(investor_id, db)
    return investor_service.create_alert(investor_id, data, db)


@router.patch(
    "/{investor_id}/alerts/{alert_id}",
    response_model=AlertResponse,
    summary="Update a price alert",
)
def update_alert(
    investor_id: UUID,
    alert_id: UUID,
    data: AlertUpdate,
    db: Session = Depends(get_db),
) -> Alert:
    _get_investor_or_404(investor_id, db)
    alert = _get_alert_or_404(alert_id, investor_id, db)
    return investor_service.update_alert(alert, data, db)


@router.delete(
    "/{investor_id}/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a price alert",
)
def delete_alert(
    investor_id: UUID, alert_id: UUID, db: Session = Depends(get_db)
) -> None:
    _get_investor_or_404(investor_id, db)
    alert = _get_alert_or_404(alert_id, investor_id, db)
    investor_service.delete_alert(alert, db)


# ---------------------------------------------------------------------------
# Notification history
# ---------------------------------------------------------------------------

@router.get(
    "/{investor_id}/notifications",
    response_model=List[NotificationLogResponse],
    summary="Get notification history for an investor",
)
def get_notifications(
    investor_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list:
    _get_investor_or_404(investor_id, db)
    return investor_service.get_notification_history(investor_id, db, limit=limit)
