"""
Pydantic Schemas for PSX (Pakistan Stock Exchange) data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MarketStatus(BaseModel):
    is_open: bool
    session: str                    # "pre_market" | "open" | "closed" | "weekend"
    current_time_pkt: str
    opens_at: Optional[str] = None  # "09:15" or None
    closes_at: Optional[str] = None # "15:30" or None
    message: str                    # Human-readable status string


class StockQuote(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    current_price: float
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    prev_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    source: str = "unknown"         # "psx" | "yfinance" | "cache"
    fetched_at: datetime
    is_live: bool = False

    def change_emoji(self) -> str:
        if self.change is None:
            return ""
        return "+" if self.change >= 0 else "-"

    def format_whatsapp(self) -> str:
        """Return a WhatsApp-ready text block for this quote."""
        direction = "+" if (self.change or 0) >= 0 else ""
        lines = [
            f"*{self.symbol}*" + (f" — {self.company_name}" if self.company_name else ""),
            f"Price:  Rs {self.current_price:,.2f}",
        ]
        if self.change is not None and self.change_pct is not None:
            lines.append(f"Change: {direction}{self.change:,.2f} ({direction}{self.change_pct:.2f}%)")
        if self.open_price:
            lines.append(f"Open:   Rs {self.open_price:,.2f}")
        if self.high_price and self.low_price:
            lines.append(f"H/L:    Rs {self.high_price:,.2f} / Rs {self.low_price:,.2f}")
        if self.volume:
            lines.append(f"Volume: {self.volume:,}")
        lines.append(f"_As of {self.fetched_at.strftime('%d %b %Y %H:%M')} PKT_")
        return "\n".join(lines)


class IndexSummary(BaseModel):
    index_name: str             # "KSE-100", "KSE-30", "KMI-30"
    value: float
    change: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    fetched_at: datetime

    def format_whatsapp(self) -> str:
        direction = "+" if (self.change or 0) >= 0 else ""
        lines = [f"*{self.index_name}*: {self.value:,.2f}"]
        if self.change is not None and self.change_pct is not None:
            lines.append(f"Change: {direction}{self.change:,.2f} ({direction}{self.change_pct:.2f}%)")
        return " | ".join(lines)


class TopMovers(BaseModel):
    gainers: List[StockQuote] = Field(default_factory=list)
    losers: List[StockQuote] = Field(default_factory=list)
    most_active: List[StockQuote] = Field(default_factory=list)
    fetched_at: datetime

    def format_whatsapp(self) -> str:
        sections = []
        if self.gainers:
            g_lines = ["*Top Gainers*"]
            for q in self.gainers[:5]:
                pct = f"+{q.change_pct:.2f}%" if q.change_pct else ""
                g_lines.append(f"  {q.symbol}: Rs {q.current_price:,.2f} ({pct})")
            sections.append("\n".join(g_lines))
        if self.losers:
            l_lines = ["*Top Losers*"]
            for q in self.losers[:5]:
                pct = f"{q.change_pct:.2f}%" if q.change_pct else ""
                l_lines.append(f"  {q.symbol}: Rs {q.current_price:,.2f} ({pct})")
            sections.append("\n".join(l_lines))
        if self.most_active:
            a_lines = ["*Most Active*"]
            for q in self.most_active[:5]:
                vol = f"{q.volume:,}" if q.volume else "N/A"
                a_lines.append(f"  {q.symbol}: {vol} shares")
            sections.append("\n".join(a_lines))
        return "\n\n".join(sections)


class StockSearchResult(BaseModel):
    symbol: str
    company_name: str
    sector: Optional[str] = None


class HistoricalCandle(BaseModel):
    date: str           # ISO date string YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoricalData(BaseModel):
    symbol: str
    period: str         # "1d", "5d", "1mo", "3mo", "6mo", "1y"
    candles: List[HistoricalCandle]
    fetched_at: datetime
