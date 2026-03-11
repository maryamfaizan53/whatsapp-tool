"""
PSX (Pakistan Stock Exchange) API Endpoints.

All endpoints are public (no auth required) for the MVP.
In production, add rate limiting and optional auth for premium features.
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional

from ..schemas.psx import (
    HistoricalData,
    IndexSummary,
    MarketStatus,
    StockQuote,
    StockSearchResult,
    TopMovers,
)
from ..services.psx_service import psx_service

router = APIRouter()


# ------------------------------------------------------------------
# Market status
# ------------------------------------------------------------------

@router.get("/status", response_model=MarketStatus, summary="PSX market open/close status")
def get_market_status() -> MarketStatus:
    """
    Returns whether PSX is currently open, the current PKT time,
    and session type (pre_market | open | closed | weekend).
    """
    return psx_service.get_market_status()


# ------------------------------------------------------------------
# Quotes
# ------------------------------------------------------------------

@router.get(
    "/quote/{symbol}",
    response_model=StockQuote,
    summary="Get latest quote for a PSX symbol",
)
def get_quote(symbol: str) -> StockQuote:
    """
    Fetch the latest price, change, volume, and OHLC for a PSX-listed symbol.

    - **symbol**: PSX ticker (e.g. `ENGRO`, `LUCK`, `PSO`)
    """
    quote = psx_service.get_quote(symbol.upper())
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for symbol '{symbol.upper()}'. "
                   "Verify the ticker is PSX-listed and try again.",
        )
    return quote


@router.get(
    "/quotes",
    response_model=List[StockQuote],
    summary="Get quotes for multiple PSX symbols",
)
def get_multiple_quotes(
    symbols: str = Query(
        ...,
        description="Comma-separated list of PSX tickers, e.g. ENGRO,LUCK,PSO",
        example="ENGRO,LUCK,PSO",
    )
) -> List[StockQuote]:
    """
    Batch quote fetch. Returns results only for valid / resolvable symbols.
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one symbol.",
        )
    if len(symbol_list) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 symbols per request.",
        )
    return psx_service.get_multiple_quotes(symbol_list)


# ------------------------------------------------------------------
# Indices
# ------------------------------------------------------------------

@router.get(
    "/indices",
    response_model=List[IndexSummary],
    summary="Get KSE-100, KSE-30, and KMI-30 index values",
)
def get_index_summary() -> List[IndexSummary]:
    """
    Returns current values and day change for all major PSX indices.
    """
    indices = psx_service.get_index_summary()
    if not indices:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Index data is temporarily unavailable. Please try again shortly.",
        )
    return indices


# ------------------------------------------------------------------
# Top movers
# ------------------------------------------------------------------

@router.get(
    "/movers",
    response_model=TopMovers,
    summary="Top gainers, losers, and most active stocks",
)
def get_top_movers(
    limit: int = Query(10, ge=1, le=30, description="Number of stocks per category")
) -> TopMovers:
    """
    Returns top gainers, top losers, and most-actively-traded stocks for the current session.
    """
    movers = psx_service.get_top_movers(limit=limit)
    if not movers:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mover data is temporarily unavailable.",
        )
    return movers


# ------------------------------------------------------------------
# Historical data
# ------------------------------------------------------------------

@router.get(
    "/history/{symbol}",
    response_model=HistoricalData,
    summary="OHLCV historical candles for a PSX symbol",
)
def get_historical_data(
    symbol: str,
    period: str = Query(
        "1mo",
        description="Time period: 1d | 5d | 1mo | 3mo | 6mo | 1y",
        pattern="^(1d|5d|1mo|3mo|6mo|1y)$",
    ),
) -> HistoricalData:
    """
    Returns daily OHLCV candles for the given symbol and period.
    Data is sourced from Yahoo Finance and cached.
    """
    data = psx_service.get_historical_data(symbol.upper(), period)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical data not found for '{symbol.upper()}'.",
        )
    return data


# ------------------------------------------------------------------
# Symbol search
# ------------------------------------------------------------------

@router.get(
    "/search",
    response_model=List[StockSearchResult],
    summary="Search PSX symbols by ticker or company name",
)
def search_symbol(
    q: str = Query(..., min_length=1, description="Ticker or company name fragment")
) -> List[StockSearchResult]:
    """
    Returns up to 10 matching PSX-listed companies.
    """
    return psx_service.search_symbol(q)


# ------------------------------------------------------------------
# WhatsApp-formatted briefing
# ------------------------------------------------------------------

@router.get(
    "/brief",
    response_model=str,
    summary="Full market briefing as a WhatsApp-ready text message",
)
def get_market_brief() -> str:
    """
    Returns a pre-formatted market briefing string ready to send via WhatsApp.
    Includes market status, index values, and top movers.
    """
    return psx_service.format_market_brief()
