"""
PSX (Pakistan Stock Exchange) Data Service.

Data source priority per operation:
  1. Redis cache (fast, short TTL)
  2. PSX Data Portal public API (primary live source)
  3. Yahoo Finance via yfinance (reliable fallback for quotes/history)

Market hours: Monday–Friday, 09:15–15:30 PKT (UTC+5).
"""
import json
import logging
from datetime import datetime, time as dtime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import redis
import requests
import yfinance as yf

from ..config import settings
from ..schemas.psx import (
    HistoricalCandle,
    HistoricalData,
    IndexSummary,
    MarketStatus,
    StockQuote,
    StockSearchResult,
    TopMovers,
)

logger = logging.getLogger(__name__)

PKT = ZoneInfo("Asia/Karachi")

# Market session boundaries (PKT)
_MARKET_OPEN = dtime(9, 15)
_MARKET_CLOSE = dtime(15, 30)
_PRE_OPEN = dtime(9, 0)

# Yahoo Finance symbol mappings
_YF_INDICES: Dict[str, str] = {
    "KSE-100": "^KSE100",
    "KSE-30": "^KSE30",
    "KMI-30": "^KMI30",
}

# PSX DPS public base URL (no auth required for summary endpoints)
_DPS_BASE = "https://dps.psx.com.pk"

# Cache TTL seconds
_TTL_LIVE = 60          # 1 minute during market hours
_TTL_CLOSED = 900       # 15 minutes when market is closed
_TTL_STATIC = 3600      # 1 hour for mostly-static data (company info, symbol list)


class PSXService:
    """
    Central service for all PSX market data.

    All public methods return typed schema objects and never raise — errors
    are logged and None / empty collections are returned to the caller.
    """

    def __init__(self) -> None:
        self._redis: Optional[redis.Redis] = None
        self._init_redis()

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    def _init_redis(self) -> None:
        try:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception as exc:
            logger.warning("Redis unavailable — caching disabled: %s", exc)
            self._redis = None

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            logger.debug("Cache read error for %s: %s", key, exc)
            return None

    def _cache_set(self, key: str, data: Any, ttl: int) -> None:
        if not self._redis:
            return
        try:
            self._redis.setex(key, ttl, json.dumps(data, default=str))
        except Exception as exc:
            logger.debug("Cache write error for %s: %s", key, exc)

    def _ttl(self) -> int:
        """Return the appropriate TTL based on current market state."""
        return _TTL_LIVE if self.get_market_status().is_open else _TTL_CLOSED

    # ------------------------------------------------------------------
    # Market status
    # ------------------------------------------------------------------

    def get_market_status(self) -> MarketStatus:
        """
        Return current PSX market status based on PKT clock.
        Does not hit any external API — purely time-based.
        Note: does not account for PSX public holidays.
        """
        now = datetime.now(tz=PKT)
        current_time = now.time()
        weekday = now.weekday()  # 0=Monday … 6=Sunday

        if weekday >= 5:
            return MarketStatus(
                is_open=False,
                session="weekend",
                current_time_pkt=now.strftime("%H:%M PKT"),
                opens_at=None,
                closes_at=None,
                message="PSX is closed on weekends. Market reopens Monday at 09:15 PKT.",
            )

        if _MARKET_OPEN <= current_time <= _MARKET_CLOSE:
            return MarketStatus(
                is_open=True,
                session="open",
                current_time_pkt=now.strftime("%H:%M PKT"),
                opens_at="09:15",
                closes_at="15:30",
                message=f"PSX is OPEN. Closes at 15:30 PKT.",
            )

        if _PRE_OPEN <= current_time < _MARKET_OPEN:
            return MarketStatus(
                is_open=False,
                session="pre_market",
                current_time_pkt=now.strftime("%H:%M PKT"),
                opens_at="09:15",
                closes_at="15:30",
                message="PSX pre-opening session. Market opens at 09:15 PKT.",
            )

        return MarketStatus(
            is_open=False,
            session="closed",
            current_time_pkt=now.strftime("%H:%M PKT"),
            opens_at="09:15 (next trading day)",
            closes_at=None,
            message="PSX is CLOSED. Showing last traded prices.",
        )

    # ------------------------------------------------------------------
    # Single stock quote
    # ------------------------------------------------------------------

    def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Fetch the latest quote for a PSX-listed symbol.
        Returns None if the symbol is invalid or data is unavailable.
        """
        symbol = symbol.upper().strip()
        cache_key = f"psx:quote:{symbol}"

        cached = self._cache_get(cache_key)
        if cached:
            cached["fetched_at"] = datetime.fromisoformat(cached["fetched_at"])
            return StockQuote(**cached)

        quote = self._fetch_from_dps_quote(symbol) or self._fetch_from_yfinance(symbol)

        if quote:
            self._cache_set(cache_key, quote.model_dump(), self._ttl())

        return quote

    def get_multiple_quotes(self, symbols: List[str]) -> List[StockQuote]:
        """Batch quote fetch — returns results for symbols that resolve."""
        results = []
        for sym in symbols:
            q = self.get_quote(sym)
            if q:
                results.append(q)
        return results

    # ------------------------------------------------------------------
    # Index summary
    # ------------------------------------------------------------------

    def get_index_summary(self) -> List[IndexSummary]:
        """
        Return current values for KSE-100, KSE-30, and KMI-30.
        Tries PSX DPS first, falls back to Yahoo Finance.
        """
        cache_key = "psx:indices"
        cached = self._cache_get(cache_key)
        if cached:
            return [
                IndexSummary(**{**item, "fetched_at": datetime.fromisoformat(item["fetched_at"])})
                for item in cached
            ]

        indices = self._fetch_indices_from_dps() or self._fetch_indices_from_yfinance()

        if indices:
            self._cache_set(cache_key, [i.model_dump() for i in indices], self._ttl())

        return indices or []

    # ------------------------------------------------------------------
    # Top movers
    # ------------------------------------------------------------------

    def get_top_movers(self, limit: int = 10) -> Optional[TopMovers]:
        """
        Return top gainers, losers, and most-active stocks.
        Primarily sourced from PSX DPS; yfinance does not expose this.
        """
        cache_key = f"psx:movers:{limit}"
        cached = self._cache_get(cache_key)
        if cached:
            now = datetime.fromisoformat(cached["fetched_at"])

            def _parse_quotes(lst: list) -> List[StockQuote]:
                return [
                    StockQuote(**{**q, "fetched_at": datetime.fromisoformat(q["fetched_at"])})
                    for q in lst
                ]

            return TopMovers(
                gainers=_parse_quotes(cached.get("gainers", [])),
                losers=_parse_quotes(cached.get("losers", [])),
                most_active=_parse_quotes(cached.get("most_active", [])),
                fetched_at=now,
            )

        movers = self._fetch_top_movers_from_dps(limit)

        if movers:
            self._cache_set(cache_key, movers.model_dump(), self._ttl())

        return movers

    # ------------------------------------------------------------------
    # Historical data
    # ------------------------------------------------------------------

    def get_historical_data(
        self, symbol: str, period: str = "1mo"
    ) -> Optional[HistoricalData]:
        """
        Return OHLCV candles for a symbol.
        period: "1d" | "5d" | "1mo" | "3mo" | "6mo" | "1y"
        """
        symbol = symbol.upper().strip()
        valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y"}
        if period not in valid_periods:
            period = "1mo"

        cache_key = f"psx:history:{symbol}:{period}"
        cached = self._cache_get(cache_key)
        if cached:
            cached["fetched_at"] = datetime.fromisoformat(cached["fetched_at"])
            return HistoricalData(**cached)

        data = self._fetch_history_yfinance(symbol, period)

        if data:
            # Historical data changes less often — cache longer
            self._cache_set(cache_key, data.model_dump(), _TTL_CLOSED)

        return data

    # ------------------------------------------------------------------
    # Symbol search
    # ------------------------------------------------------------------

    def search_symbol(self, query: str) -> List[StockSearchResult]:
        """
        Simple in-memory search over the known symbol list.
        For a production system, wire this to a database full-text search.
        """
        query = query.upper().strip()
        cache_key = "psx:symbol_list"

        symbol_list: Optional[List[Dict]] = self._cache_get(cache_key)
        if not symbol_list:
            symbol_list = self._fetch_symbol_list_from_dps()
            if symbol_list:
                self._cache_set(cache_key, symbol_list, _TTL_STATIC)

        if not symbol_list:
            return []

        results = []
        for item in symbol_list:
            sym = item.get("symbol", "")
            name = item.get("company_name", "")
            if query in sym.upper() or query in name.upper():
                results.append(
                    StockSearchResult(
                        symbol=sym,
                        company_name=name,
                        sector=item.get("sector"),
                    )
                )
        return results[:10]

    # ------------------------------------------------------------------
    # WhatsApp message formatters
    # ------------------------------------------------------------------

    def format_market_brief(self) -> str:
        """
        Build a complete market briefing message suitable for WhatsApp.
        Combines market status + index summary + top movers.
        """
        lines: List[str] = []

        status = self.get_market_status()
        lines.append(f"*PSX Market Update*")
        lines.append(status.message)
        lines.append(f"Time: {status.current_time_pkt}")
        lines.append("")

        indices = self.get_index_summary()
        if indices:
            lines.append("*Indices*")
            for idx in indices:
                lines.append(idx.format_whatsapp())
            lines.append("")

        movers = self.get_top_movers(limit=5)
        if movers:
            lines.append(movers.format_whatsapp())

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private: PSX DPS fetchers
    # ------------------------------------------------------------------

    def _fetch_from_dps_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Try to fetch a single quote from PSX DPS public endpoint.
        PSX DPS returns JSON for market prices.
        """
        try:
            resp = requests.get(
                f"{_DPS_BASE}/prices",
                params={"symbol": symbol},
                timeout=5,
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            # DPS response structure (best-effort parse):
            # {"symbol": "ENGRO", "ldcp": 290.5, "open": 291, "high": 295,
            #  "low": 288, "current": 292.1, "volume": 1234567, "change": 1.6, "changep": 0.55}
            if not data or "current" not in data:
                return None

            current = float(data.get("current") or data.get("ldcp", 0))
            prev_close = float(data.get("ldcp", 0))
            change = current - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0

            return StockQuote(
                symbol=symbol,
                company_name=data.get("name"),
                current_price=current,
                open_price=_safe_float(data.get("open")),
                high_price=_safe_float(data.get("high")),
                low_price=_safe_float(data.get("low")),
                prev_close=prev_close,
                change=_safe_float(data.get("change"), change),
                change_pct=_safe_float(data.get("changep"), change_pct),
                volume=_safe_int(data.get("volume")),
                market_cap=_safe_float(data.get("mktcap")),
                source="psx",
                fetched_at=datetime.now(tz=PKT),
                is_live=self.get_market_status().is_open,
            )
        except Exception as exc:
            logger.debug("DPS quote fetch failed for %s: %s", symbol, exc)
            return None

    def _fetch_indices_from_dps(self) -> Optional[List[IndexSummary]]:
        """Fetch KSE index values from PSX DPS summary endpoint."""
        try:
            resp = requests.get(
                f"{_DPS_BASE}/summary",
                timeout=5,
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            # DPS summary structure (best-effort):
            # {"indices": [{"name": "KSE100", "current": 86420.5, "change": 123.4, "changep": 0.14}]}
            raw_indices = data.get("indices") or data.get("data") or []
            if not raw_indices:
                return None

            name_map = {
                "KSE100": "KSE-100",
                "KSE30": "KSE-30",
                "KMI30": "KMI-30",
                "KSE-100": "KSE-100",
                "KSE-30": "KSE-30",
                "KMI-30": "KMI-30",
            }
            results = []
            now = datetime.now(tz=PKT)
            for item in raw_indices:
                raw_name = item.get("name", "")
                canonical = name_map.get(raw_name.replace(" ", "").upper())
                if not canonical:
                    continue
                results.append(
                    IndexSummary(
                        index_name=canonical,
                        value=float(item.get("current", 0)),
                        change=_safe_float(item.get("change")),
                        change_pct=_safe_float(item.get("changep")),
                        volume=_safe_int(item.get("volume")),
                        fetched_at=now,
                    )
                )
            return results if results else None
        except Exception as exc:
            logger.debug("DPS indices fetch failed: %s", exc)
            return None

    def _fetch_top_movers_from_dps(self, limit: int) -> Optional[TopMovers]:
        """Fetch top gainers/losers/active from PSX DPS."""
        try:
            now = datetime.now(tz=PKT)

            def _fetch_category(category: str) -> List[StockQuote]:
                try:
                    resp = requests.get(
                        f"{_DPS_BASE}/market/top",
                        params={"type": category, "limit": limit},
                        timeout=5,
                        headers={"Accept": "application/json"},
                    )
                    if resp.status_code != 200:
                        return []
                    items = resp.json() or []
                    return [_dps_item_to_quote(item, now, self.get_market_status().is_open) for item in items if item]
                except Exception:
                    return []

            gainers = _fetch_category("gainers")
            losers = _fetch_category("losers")
            active = _fetch_category("active")

            if not gainers and not losers and not active:
                return None

            return TopMovers(
                gainers=gainers,
                losers=losers,
                most_active=active,
                fetched_at=now,
            )
        except Exception as exc:
            logger.debug("DPS top movers fetch failed: %s", exc)
            return None

    def _fetch_symbol_list_from_dps(self) -> Optional[List[Dict]]:
        """Fetch the master list of all PSX-listed symbols from DPS."""
        try:
            resp = requests.get(
                f"{_DPS_BASE}/symbols",
                timeout=10,
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            symbols = data if isinstance(data, list) else data.get("data", [])
            return [
                {
                    "symbol": item.get("symbol") or item.get("code", ""),
                    "company_name": item.get("name") or item.get("company", ""),
                    "sector": item.get("sector"),
                }
                for item in symbols
                if item.get("symbol") or item.get("code")
            ]
        except Exception as exc:
            logger.debug("DPS symbol list fetch failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Private: Yahoo Finance fetchers (fallback)
    # ------------------------------------------------------------------

    def _fetch_from_yfinance(self, symbol: str) -> Optional[StockQuote]:
        """
        Fetch a single quote via Yahoo Finance using the .KA suffix convention.
        e.g., ENGRO -> ENGRO.KA
        """
        yf_symbol = f"{symbol}.KA"
        try:
            ticker = yf.Ticker(yf_symbol)
            # fast_info is lightweight; no heavy metadata call
            fi = ticker.fast_info
            hist = ticker.history(period="2d", auto_adjust=True)

            if hist.empty:
                logger.debug("yfinance: no history for %s", yf_symbol)
                return None

            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest

            current_price = float(latest["Close"])
            prev_close = float(prev["Close"])
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0.0

            company_name: Optional[str] = None
            try:
                company_name = ticker.info.get("longName") or ticker.info.get("shortName")
            except Exception:
                pass

            return StockQuote(
                symbol=symbol,
                company_name=company_name,
                current_price=current_price,
                open_price=_safe_float(latest.get("Open")),
                high_price=_safe_float(latest.get("High")),
                low_price=_safe_float(latest.get("Low")),
                prev_close=prev_close,
                change=change,
                change_pct=change_pct,
                volume=_safe_int(latest.get("Volume")),
                market_cap=_safe_float(getattr(fi, "market_cap", None)),
                source="yfinance",
                fetched_at=datetime.now(tz=PKT),
                is_live=self.get_market_status().is_open,
            )
        except Exception as exc:
            logger.debug("yfinance quote fetch failed for %s: %s", yf_symbol, exc)
            return None

    def _fetch_indices_from_yfinance(self) -> Optional[List[IndexSummary]]:
        """Fetch KSE index values from Yahoo Finance as fallback."""
        results = []
        now = datetime.now(tz=PKT)
        for name, yf_sym in _YF_INDICES.items():
            try:
                ticker = yf.Ticker(yf_sym)
                hist = ticker.history(period="2d", auto_adjust=True)
                if hist.empty:
                    continue
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest
                value = float(latest["Close"])
                prev_val = float(prev["Close"])
                change = value - prev_val
                change_pct = (change / prev_val * 100) if prev_val else 0.0
                results.append(
                    IndexSummary(
                        index_name=name,
                        value=value,
                        change=change,
                        change_pct=change_pct,
                        volume=_safe_int(latest.get("Volume")),
                        fetched_at=now,
                    )
                )
            except Exception as exc:
                logger.debug("yfinance index fetch failed for %s: %s", yf_sym, exc)
        return results if results else None

    def _fetch_history_yfinance(
        self, symbol: str, period: str
    ) -> Optional[HistoricalData]:
        """Fetch OHLCV history via Yahoo Finance."""
        yf_symbol = f"{symbol}.KA"
        try:
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=period, auto_adjust=True)
            if hist.empty:
                return None

            candles = [
                HistoricalCandle(
                    date=str(idx.date()),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
                for idx, row in hist.iterrows()
            ]

            return HistoricalData(
                symbol=symbol,
                period=period,
                candles=candles,
                fetched_at=datetime.now(tz=PKT),
            )
        except Exception as exc:
            logger.debug("yfinance history fetch failed for %s: %s", yf_symbol, exc)
            return None


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _dps_item_to_quote(
    item: Dict[str, Any], fetched_at: datetime, is_live: bool
) -> StockQuote:
    """Convert a raw DPS API item dict into a StockQuote."""
    symbol = item.get("symbol") or item.get("code", "UNKNOWN")
    current = _safe_float(item.get("current") or item.get("ldcp"), 0.0)
    prev_close = _safe_float(item.get("ldcp"), current)
    change = current - (prev_close or 0)
    change_pct = (change / prev_close * 100) if prev_close else 0.0
    return StockQuote(
        symbol=symbol,
        company_name=item.get("name"),
        current_price=current or 0.0,
        open_price=_safe_float(item.get("open")),
        high_price=_safe_float(item.get("high")),
        low_price=_safe_float(item.get("low")),
        prev_close=prev_close,
        change=_safe_float(item.get("change"), change),
        change_pct=_safe_float(item.get("changep"), change_pct),
        volume=_safe_int(item.get("volume")),
        market_cap=_safe_float(item.get("mktcap")),
        source="psx",
        fetched_at=fetched_at,
        is_live=is_live,
    )


# Singleton
psx_service = PSXService()
