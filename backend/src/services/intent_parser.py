"""
Intent Parser for PSX WhatsApp Bot.

Pure parsing layer — no I/O, no database, no service calls.
Takes raw WhatsApp message text and returns a ParsedIntent.

Supports:
  - English commands
  - Roman Urdu (transliterated Urdu written in Latin script)
  - Mixed / code-switching (e.g. "ENGRO ka price batao")

Strategy: ordered regex rules, most specific first.
Each rule tries to match and extract entities; first match wins.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Intent enum
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    # Market data
    GET_PRICE           = "get_price"
    GET_MULTIPLE_PRICES = "get_multiple_prices"
    GET_INDICES         = "get_indices"
    GET_TOP_MOVERS      = "get_top_movers"
    GET_MARKET_STATUS   = "get_market_status"
    GET_MARKET_BRIEF    = "get_market_brief"
    GET_HISTORY         = "get_history"
    SEARCH_SYMBOL       = "search_symbol"

    # Portfolio
    GET_PORTFOLIO       = "get_portfolio"
    ADD_HOLDING         = "add_holding"
    REMOVE_HOLDING      = "remove_holding"

    # Watchlist
    GET_WATCHLIST       = "get_watchlist"
    ADD_WATCHLIST       = "add_watchlist"
    REMOVE_WATCHLIST    = "remove_watchlist"

    # Alerts
    SET_ALERT           = "set_alert"
    LIST_ALERTS         = "list_alerts"
    DELETE_ALERT        = "delete_alert"

    # Notifications / settings
    SUBSCRIBE_BRIEF     = "subscribe_morning_brief"
    UNSUBSCRIBE_BRIEF   = "unsubscribe_morning_brief"

    # Meta
    HELP                = "help"
    UNKNOWN             = "unknown"


# ---------------------------------------------------------------------------
# ParsedIntent dataclass
# ---------------------------------------------------------------------------

@dataclass
class ParsedIntent:
    intent: Intent
    raw_text: str
    confidence: float = 1.0

    # Extracted entities
    symbol: Optional[str] = None        # single PSX ticker, e.g. "ENGRO"
    symbols: List[str] = field(default_factory=list)  # multiple tickers
    price: Optional[float] = None       # target price in PKR
    quantity: Optional[float] = None    # number of shares
    avg_price: Optional[float] = None   # average buy price for ADD_HOLDING
    condition: Optional[str] = None     # "above"|"below"|"change_pct_up"|"change_pct_down"
    period: Optional[str] = None        # yfinance period string: "1d","5d","1mo","3mo","6mo","1y"
    query: Optional[str] = None         # free-text search query

    def __repr__(self) -> str:
        parts = [f"intent={self.intent.value}"]
        if self.symbol:
            parts.append(f"symbol={self.symbol}")
        if self.symbols:
            parts.append(f"symbols={self.symbols}")
        if self.price is not None:
            parts.append(f"price={self.price}")
        if self.quantity is not None:
            parts.append(f"qty={self.quantity}")
        if self.condition:
            parts.append(f"condition={self.condition}")
        if self.period:
            parts.append(f"period={self.period}")
        return f"ParsedIntent({', '.join(parts)})"


# ---------------------------------------------------------------------------
# Keyword banks (English + Roman Urdu)
# ---------------------------------------------------------------------------

# Words that introduce a price query
_PRICE_TRIGGERS = (
    r"price|rate|kimat|qeemat|kya hai|ka bhav|bhav|value|worth|kitna hai|"
    r"kitni hai|current|live|today"
)

# Words that indicate "watchlist"
_WATCHLIST_TRIGGERS = r"watchlist|watch list|watch|nazr|nazar"

# Words that indicate "portfolio" / holdings
_PORTFOLIO_TRIGGERS = r"portfolio|holdings?|positions?|mera portfolio|my portfolio|my stocks|meri holdings"

# Words indicating "market overall"
_MARKET_TRIGGERS = r"market|bazar|baazar|stock market"

# Words indicating "index / indices"
_INDEX_TRIGGERS = r"ind(?:ex|ices)|kse[\s\-]?(?:100|30)|kmi[\s\-]?30|kse100|kse30|kmi30"

# Words indicating "top movers"
_MOVER_TRIGGERS = r"(?:top\s+)?(?:gainers?|losers?|movers?|winners?|decliners?|aktif|active|most active)"

# Direction words for alerts
_ABOVE_WORDS = r"above|upar|cross|crosses|exceed|se upar|se zyada|zyada|barh|barhe"
_BELOW_WORDS = r"below|neeche|under|fall|falls|drop|drops|se neeche|se kam|kam|gir|gire"

# Words indicating "add" action
_ADD_WORDS = r"add|buy|bought|kharida|kharid|purchase|purchased|liya|le liya|shamil"

# Words indicating "remove" action
_REMOVE_WORDS = r"remove|delete|hata|hatao|nikalo|nikaal|band karo|cancel"

# History / chart words
_HISTORY_TRIGGERS = r"history|hist|chart|graph|data|trend|pichla|last|previous"

# Alert words
_ALERT_WORDS = r"alert|notify|notification|batao|inform|remind|yaad dilao|signal"

# Morning brief
_BRIEF_WORDS = r"morning\s+brief|daily\s+update|subah\s+ka\s+update|daily\s+brief|morning\s+update|roz\s+ka\s+update"

# Help words
_HELP_WORDS = r"help|madad|commands?|menu|kya kar sakte|what can|guide|tutorial|start|shuru"


# ---------------------------------------------------------------------------
# Entity extraction helpers
# ---------------------------------------------------------------------------

# PSX tickers: 2–7 uppercase letters.
# We normalise input to uppercase before matching.
_SYMBOL_PAT = re.compile(r"\b([A-Z]{2,7})\b")

# Numbers: optional commas, optional decimal  (e.g. "1,234.56" or "290")
_NUM_PAT = re.compile(r"(?:rs\.?\s*)?(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)

# Common non-ticker uppercase words to exclude from symbol extraction
_STOP_WORDS = frozenset({
    # English articles / prepositions / conjunctions
    "THE", "AND", "FOR", "FROM", "WITH", "WHEN", "THEN", "THIS", "THAT",
    "WILL", "HAVE", "HAS", "HAD", "ARE", "WAS", "WERE", "BEEN", "BEING",
    "OF", "A", "AN", "TO", "BY", "AS", "IF", "IS",
    # English action / UI words
    "ADD", "GET", "SET", "PUT", "BUY", "SELL", "TOP", "LAST", "NEXT",
    "OPEN", "CLOSE", "HIGH", "LOW", "SEND", "SHOW", "LIST",
    "MY", "ME", "US", "IT",
    # Index names / system abbreviations (NOT PSX tickers)
    "KSE", "KMI", "PSX", "STT", "NIT",
    # Currency / units
    "RS", "PKR", "AT", "OR", "ON", "IN", "UP", "OK", "YES", "NO",
    # Time words
    "DAY", "WEEK", "MONTH", "YEAR", "DAILY", "BRIEF",
    # Common intent keywords (should not be treated as tickers)
    "HELP", "INFO", "PRICE", "RATE", "ALERT", "WATCH", "REMOVE", "DELETE",
    # Roman Urdu particles frequently embedded in commands
    "KA", "KI", "KE", "KY", "KYA", "HA", "HAI", "HO", "SE", "PE",
    "KO", "HI", "BHI", "JO", "YEH", "WO", "AP", "AUR", "YA",
})

_PERIOD_MAP = {
    # Match both yfinance shorthand ("1d", "5d") and natural language
    r"1\s*d(?:ay)?|today|aaj":                      "1d",
    r"5\s*d(?:ays?)?|week|hafta":                   "5d",
    r"1\s*mo(?:nth)?|ek\s*mahina":                  "1mo",
    r"3\s*mo(?:nths?)?|teen\s*mahine":              "3mo",
    r"6\s*mo(?:nths?)?|chhe\s*mahine":              "6mo",
    r"1\s*y(?:ear)?|ek\s*saal|(?<!\d)year(?!\w)":  "1y",
}


def _num(text: str) -> Optional[float]:
    """Extract the first number from text (strips commas)."""
    m = _NUM_PAT.search(text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _all_nums(text: str) -> List[float]:
    return [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def _sym(text: str) -> Optional[str]:
    """Extract the first valid PSX symbol from text."""
    for m in _SYMBOL_PAT.finditer(text.upper()):
        token = m.group(1)
        if token not in _STOP_WORDS and len(token) >= 2:
            return token
    return None


def _syms(text: str) -> List[str]:
    """Extract all valid PSX symbols from text (deduped, order-preserving)."""
    seen = set()
    results = []
    for m in _SYMBOL_PAT.finditer(text.upper()):
        token = m.group(1)
        if token not in _STOP_WORDS and token not in seen:
            seen.add(token)
            results.append(token)
    return results


def _period(text: str) -> Optional[str]:
    """Map natural language period to yfinance period code."""
    lower = text.lower()
    for pattern, code in _PERIOD_MAP.items():
        if re.search(pattern, lower):
            return code
    return None


def _direction(text: str) -> Optional[str]:
    """Detect alert direction from text."""
    lower = text.lower()
    if re.search(_ABOVE_WORDS, lower):
        return "above"
    if re.search(_BELOW_WORDS, lower):
        return "below"
    return None


# ---------------------------------------------------------------------------
# Intent Parser
# ---------------------------------------------------------------------------

class IntentParser:
    """
    Stateless, rule-based intent parser.
    All methods are pure functions — no I/O.
    """

    def parse(self, text: str) -> ParsedIntent:
        """
        Parse raw WhatsApp message text into a ParsedIntent.
        Rules are tried in order; first match wins.
        """
        text = text.strip()
        norm = text.lower()
        up = text.upper()

        # ----------------------------------------------------------------
        # 1. HELP
        # ----------------------------------------------------------------
        if re.search(rf"^(?:{_HELP_WORDS})\b", norm) or norm in ("?", "hi", "hello", "salam", "assalam"):
            return ParsedIntent(intent=Intent.HELP, raw_text=text)

        # ----------------------------------------------------------------
        # 2. SUBSCRIBE / UNSUBSCRIBE morning brief
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_BRIEF_WORDS})", norm):
            unsubscribe = re.search(
                r"off|stop|band|disable|unsubscribe|nahi chahiye|mat bhejo|cancel", norm
            )
            intent = Intent.UNSUBSCRIBE_BRIEF if unsubscribe else Intent.SUBSCRIBE_BRIEF
            return ParsedIntent(intent=intent, raw_text=text)

        # ----------------------------------------------------------------
        # 3. MARKET STATUS
        # ----------------------------------------------------------------
        if re.search(
            rf"(?:{_MARKET_TRIGGERS})\s*(?:open|close|band|khula|status|chal raha|hai kya|abhi)|"
            r"is market|market kab|when.*market",
            norm,
        ):
            return ParsedIntent(intent=Intent.GET_MARKET_STATUS, raw_text=text)

        # ----------------------------------------------------------------
        # 4. TOP MOVERS
        # ----------------------------------------------------------------
        if re.search(rf"^(?:{_MOVER_TRIGGERS})", norm) or re.search(
            rf"(?:{_MOVER_TRIGGERS})", norm
        ):
            return ParsedIntent(intent=Intent.GET_TOP_MOVERS, raw_text=text)

        # ----------------------------------------------------------------
        # 5. INDICES
        # ----------------------------------------------------------------
        if re.search(rf"^(?:{_INDEX_TRIGGERS})", norm) or re.search(
            rf"(?:{_INDEX_TRIGGERS})", norm
        ):
            return ParsedIntent(intent=Intent.GET_INDICES, raw_text=text)

        # ----------------------------------------------------------------
        # 6. MARKET BRIEF (full summary)
        # ----------------------------------------------------------------
        if re.search(
            r"^(?:market|bazar)\s*$|market\s+(?:summary|update|brief|overview|aaj|today)|"
            r"aaj\s+ka\s+market|full\s+update|complete\s+update",
            norm,
        ):
            return ParsedIntent(intent=Intent.GET_MARKET_BRIEF, raw_text=text)

        # ----------------------------------------------------------------
        # 7. SEARCH SYMBOL
        # ----------------------------------------------------------------
        m = re.match(r"^(?:search|find|dhundo|talash)\s+(.+)$", norm)
        if m:
            return ParsedIntent(
                intent=Intent.SEARCH_SYMBOL,
                raw_text=text,
                query=m.group(1).strip(),
            )

        # ----------------------------------------------------------------
        # 8. DELETE ALERT
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_REMOVE_WORDS}|delete).*alert|alert.*(?:{_REMOVE_WORDS})", norm):
            sym = _sym(text)
            return ParsedIntent(intent=Intent.DELETE_ALERT, raw_text=text, symbol=sym)

        # ----------------------------------------------------------------
        # 9. LIST ALERTS
        # ----------------------------------------------------------------
        if re.search(
            r"^(?:alerts?|my alerts?|mera alerts?|meri alerts?)\s*$|"
            r"(?:show|list|dekhao)\s+(?:my\s+)?alerts?",
            norm,
        ):
            return ParsedIntent(intent=Intent.LIST_ALERTS, raw_text=text)

        # ----------------------------------------------------------------
        # 10. SET ALERT
        #
        # Patterns (English):
        #   "alert ENGRO above 300"
        #   "alert me when ENGRO above 300"
        #   "set alert ENGRO below 250"
        #   "notify me if ENGRO drops below 250"
        #
        # Patterns (Roman Urdu):
        #   "ENGRO 300 se upar hone pe batao"
        #   "ENGRO jab 250 se neeche jaye alert"
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_ALERT_WORDS})", norm) and _sym(text):
            sym = _sym(text)
            nums = _all_nums(text)
            direction = _direction(text)
            if not direction:
                direction = "above"     # default when direction is ambiguous
            target = nums[0] if nums else None
            if sym and target is not None:
                cond = direction  # "above" or "below"
                # Check for change-% alerts: "3% upar" / "gain of 3%"
                if re.search(r"%|percent|فیصد", norm):
                    cond = "change_pct_up" if direction == "above" else "change_pct_down"
                return ParsedIntent(
                    intent=Intent.SET_ALERT,
                    raw_text=text,
                    symbol=sym,
                    price=target,
                    condition=cond,
                )

        # ----------------------------------------------------------------
        # 11. REMOVE FROM WATCHLIST
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_REMOVE_WORDS}).+(?:{_WATCHLIST_TRIGGERS})|"
                     rf"(?:{_WATCHLIST_TRIGGERS}).+(?:{_REMOVE_WORDS})", norm):
            sym = _sym(text)
            return ParsedIntent(intent=Intent.REMOVE_WATCHLIST, raw_text=text, symbol=sym)

        # ----------------------------------------------------------------
        # 12. ADD TO WATCHLIST
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_WATCHLIST_TRIGGERS})", norm) and re.search(
            rf"(?:{_ADD_WORDS}|^watch\b)", norm
        ):
            sym = _sym(text)
            return ParsedIntent(intent=Intent.ADD_WATCHLIST, raw_text=text, symbol=sym)

        # Single "watch SYMBOL" shorthand
        m = re.match(r"^watch\s+([A-Za-z]{2,7})\s*$", norm)
        if m:
            return ParsedIntent(
                intent=Intent.ADD_WATCHLIST,
                raw_text=text,
                symbol=m.group(1).upper(),
            )

        # ----------------------------------------------------------------
        # 13. GET WATCHLIST
        # ----------------------------------------------------------------
        if re.search(
            rf"^(?:my\s+)?(?:{_WATCHLIST_TRIGGERS})\s*$|"
            rf"(?:show|list|dekhao)\s+(?:my\s+)?(?:{_WATCHLIST_TRIGGERS})",
            norm,
        ):
            return ParsedIntent(intent=Intent.GET_WATCHLIST, raw_text=text)

        # ----------------------------------------------------------------
        # 14. REMOVE HOLDING
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_REMOVE_WORDS}).+(?:{_PORTFOLIO_TRIGGERS})|"
                     rf"(?:{_PORTFOLIO_TRIGGERS}).+(?:{_REMOVE_WORDS})|"
                     rf"(?:{_REMOVE_WORDS})\s+[A-Za-z]{{2,7}}\s+(?:from\s+)?portfolio",
                     norm):
            sym = _sym(text)
            return ParsedIntent(intent=Intent.REMOVE_HOLDING, raw_text=text, symbol=sym)

        # ----------------------------------------------------------------
        # 15. ADD HOLDING
        #
        # Patterns:
        #   "add ENGRO 100 at 290"
        #   "add ENGRO 100 shares at 290"
        #   "bought ENGRO 100 at 290"
        #   "ENGRO 100 @ 290"
        #   "ENGRO 100 290"     (qty then price, no keyword)
        # ----------------------------------------------------------------
        holding_m = re.search(
            r"([A-Za-z]{2,7})\s+(\d[\d,]*(?:\.\d+)?)\s*(?:shares?\s+)?(?:at|@|kharida|bought|pe|for|=)\s*"
            r"(?:rs\.?\s*)?(\d[\d,]*(?:\.\d+)?)",
            text,
            re.IGNORECASE,
        )
        if holding_m or (re.search(rf"(?:{_ADD_WORDS})", norm) and len(_all_nums(text)) >= 2 and _sym(text)):
            if holding_m:
                sym = holding_m.group(1).upper()
                qty = float(holding_m.group(2).replace(",", ""))
                avg_p = float(holding_m.group(3).replace(",", ""))
            else:
                sym = _sym(text)
                nums = _all_nums(text)
                qty, avg_p = nums[0], nums[1]
            return ParsedIntent(
                intent=Intent.ADD_HOLDING,
                raw_text=text,
                symbol=sym,
                quantity=qty,
                avg_price=avg_p,
            )

        # ----------------------------------------------------------------
        # 16. GET PORTFOLIO
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_PORTFOLIO_TRIGGERS})", norm):
            return ParsedIntent(intent=Intent.GET_PORTFOLIO, raw_text=text)

        # ----------------------------------------------------------------
        # 17. GET HISTORY
        #
        # "ENGRO 1 month history" / "LUCK chart 3mo" / "PSO history"
        # ----------------------------------------------------------------
        if re.search(rf"(?:{_HISTORY_TRIGGERS})", norm) and _sym(text):
            sym = _sym(text)
            per = _period(text) or "1mo"
            return ParsedIntent(
                intent=Intent.GET_HISTORY,
                raw_text=text,
                symbol=sym,
                period=per,
            )

        # ----------------------------------------------------------------
        # 18. MULTIPLE PRICES — comma/space-separated symbols
        #
        # "ENGRO LUCK PSO"  /  "ENGRO, LUCK, PSO prices"
        # ----------------------------------------------------------------
        all_syms = _syms(text)
        if len(all_syms) >= 2:
            return ParsedIntent(
                intent=Intent.GET_MULTIPLE_PRICES,
                raw_text=text,
                symbols=all_syms,
            )

        # ----------------------------------------------------------------
        # 19. SINGLE PRICE
        #
        # "ENGRO" / "ENGRO price" / "ENGRO ka rate" / "price of ENGRO"
        # ----------------------------------------------------------------
        if all_syms:
            sym = all_syms[0]
            return ParsedIntent(
                intent=Intent.GET_PRICE,
                raw_text=text,
                symbol=sym,
            )

        # ----------------------------------------------------------------
        # 20. UNKNOWN
        # ----------------------------------------------------------------
        return ParsedIntent(
            intent=Intent.UNKNOWN,
            raw_text=text,
            confidence=0.0,
        )


# ---------------------------------------------------------------------------
# Help menu text (returned by handler, defined here to stay with the parser)
# ---------------------------------------------------------------------------

HELP_TEXT = """\
*PSX WhatsApp Bot — Commands*

*Prices*
  ENGRO           — get latest quote
  ENGRO LUCK PSO  — multiple quotes

*Indices*
  indices / KSE100  — KSE-100, KSE-30, KMI-30

*Market*
  market status    — is PSX open?
  market           — full market brief
  gainers          — top gainers
  losers           — top losers

*Portfolio*
  portfolio                          — P&L summary
  add ENGRO 100 at 290               — add holding
  remove ENGRO from portfolio        — remove holding

*Watchlist*
  watch ENGRO                        — add to watchlist
  watchlist                          — show watchlist
  remove ENGRO from watchlist        — remove from watchlist

*Alerts*
  alert ENGRO above 300              — price alert
  alert ENGRO below 250              — price alert
  alerts                             — list my alerts
  delete alert ENGRO                 — remove alert

*History*
  ENGRO history 1mo                  — OHLCV chart data

*Notifications*
  morning brief                      — enable daily market brief
  morning brief off                  — disable

Type *help* anytime to see this menu.\
"""


# Singleton
intent_parser = IntentParser()
