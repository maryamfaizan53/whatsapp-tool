"""
Intent Handler for PSX WhatsApp Bot.

Takes a WhatsApp number + raw message text, resolves the investor,
parses the intent, calls the appropriate service, and returns a
WhatsApp-ready response string.

This is the single entry point called by the webhook background task.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..models.investor import Investor
from ..schemas.investor import (
    AlertCreate,
    HoldingCreate,
    InvestorUpdate,
    WatchlistAdd,
)
from ..services.intent_parser import HELP_TEXT, Intent, IntentParser, ParsedIntent, intent_parser
from ..services.investor_service import investor_service
from ..services.psx_service import psx_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Onboarding step constants (mirrors Investor.onboarding_step values)
# ---------------------------------------------------------------------------
STEP_NEW          = "new"
STEP_NAME_ASKED   = "name_asked"
STEP_LANG_ASKED   = "language_asked"
STEP_COMPLETE     = "complete"

_LANG_OPTIONS = {
    "1": "en",
    "en": "en",
    "english": "en",
    "2": "ur",
    "ur": "ur",
    "urdu": "ur",
    "3": "roman_ur",
    "roman": "roman_ur",
    "roman_ur": "roman_ur",
    "roman urdu": "roman_ur",
}

_WELCOME = (
    "Welcome to *PSX Market Bot*!\n\n"
    "Get live Pakistan Stock Exchange prices, set alerts, and track your portfolio — all on WhatsApp.\n\n"
    "First, what's your name?"
)

_LANG_PROMPT = (
    "Which language do you prefer?\n\n"
    "  1. English\n"
    "  2. اردو (Urdu)\n"
    "  3. Roman Urdu\n\n"
    "Reply with 1, 2, or 3."
)


class IntentHandler:
    """
    Stateful dispatcher: resolves investor → runs onboarding if needed →
    parses intent → calls services → returns WhatsApp message string.
    """

    def handle(self, wa_number: str, text: str, db: Session) -> str:
        """
        Main entry point. Always returns a non-empty string to send back.
        Never raises — all exceptions are caught and a safe fallback is returned.
        """
        try:
            investor, created = investor_service.get_or_create(wa_number, db)

            # ---- Onboarding flow ----------------------------------------
            if not investor.is_onboarded:
                return self._handle_onboarding(investor, text, db)

            # ---- Normal flow: parse intent and dispatch ------------------
            parsed = intent_parser.parse(text)
            logger.info(
                "wa=%s intent=%s symbol=%s",
                wa_number, parsed.intent.value, parsed.symbol,
            )
            return self._dispatch(parsed, investor, db)

        except Exception as exc:
            logger.exception("IntentHandler.handle failed for wa=%s text=%r", wa_number, text)
            return (
                "Sorry, something went wrong on our end. Please try again.\n"
                "Type *help* to see available commands."
            )

    # -----------------------------------------------------------------------
    # Onboarding
    # -----------------------------------------------------------------------

    def _handle_onboarding(self, investor: Investor, text: str, db: Session) -> str:
        step = investor.onboarding_step

        if step == STEP_NEW:
            investor_service.advance_onboarding(investor, STEP_NAME_ASKED, db)
            return _WELCOME

        if step == STEP_NAME_ASKED:
            name = text.strip()[:100]
            investor_service.update(investor, InvestorUpdate(name=name), db)
            investor_service.advance_onboarding(investor, STEP_LANG_ASKED, db)
            return f"Nice to meet you, *{name}*!\n\n{_LANG_PROMPT}"

        if step == STEP_LANG_ASKED:
            lang = _LANG_OPTIONS.get(text.strip().lower())
            if not lang:
                return f"Please reply with 1, 2, or 3.\n\n{_LANG_PROMPT}"
            investor_service.update(investor, InvestorUpdate(preferred_language=lang), db)
            investor_service.complete_onboarding(investor, db)
            return (
                f"You're all set!\n\n{HELP_TEXT}"
            )

        # Fallback — mark complete and proceed
        investor_service.complete_onboarding(investor, db)
        return HELP_TEXT

    # -----------------------------------------------------------------------
    # Dispatch
    # -----------------------------------------------------------------------

    def _dispatch(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        intent = parsed.intent

        if intent == Intent.HELP:
            return HELP_TEXT

        if intent == Intent.GET_PRICE:
            return self._get_price(parsed)

        if intent == Intent.GET_MULTIPLE_PRICES:
            return self._get_multiple_prices(parsed)

        if intent == Intent.GET_INDICES:
            return self._get_indices()

        if intent == Intent.GET_TOP_MOVERS:
            return self._get_movers()

        if intent == Intent.GET_MARKET_STATUS:
            return self._get_market_status()

        if intent == Intent.GET_MARKET_BRIEF:
            return psx_service.format_market_brief()

        if intent == Intent.GET_HISTORY:
            return self._get_history(parsed)

        if intent == Intent.SEARCH_SYMBOL:
            return self._search_symbol(parsed)

        if intent == Intent.GET_PORTFOLIO:
            return self._get_portfolio(investor, db)

        if intent == Intent.ADD_HOLDING:
            return self._add_holding(parsed, investor, db)

        if intent == Intent.REMOVE_HOLDING:
            return self._remove_holding(parsed, investor, db)

        if intent == Intent.GET_WATCHLIST:
            return self._get_watchlist(investor, db)

        if intent == Intent.ADD_WATCHLIST:
            return self._add_watchlist(parsed, investor, db)

        if intent == Intent.REMOVE_WATCHLIST:
            return self._remove_watchlist(parsed, investor, db)

        if intent == Intent.SET_ALERT:
            return self._set_alert(parsed, investor, db)

        if intent == Intent.LIST_ALERTS:
            return self._list_alerts(investor, db)

        if intent == Intent.DELETE_ALERT:
            return self._delete_alert(parsed, investor, db)

        if intent == Intent.SUBSCRIBE_BRIEF:
            return self._toggle_brief(investor, db, enable=True)

        if intent == Intent.UNSUBSCRIBE_BRIEF:
            return self._toggle_brief(investor, db, enable=False)

        # UNKNOWN
        return (
            "I didn't understand that. Type *help* to see available commands.\n\n"
            "Examples:\n"
            "  ENGRO        — get quote\n"
            "  portfolio    — view portfolio\n"
            "  alert ENGRO above 300"
        )

    # -----------------------------------------------------------------------
    # Market data handlers
    # -----------------------------------------------------------------------

    def _get_price(self, parsed: ParsedIntent) -> str:
        sym = parsed.symbol
        if not sym:
            return "Please provide a symbol. Example: *ENGRO*"
        quote = psx_service.get_quote(sym)
        if not quote:
            return (
                f"Could not find data for *{sym}*.\n"
                "Check the ticker or try: search engro"
            )
        return quote.format_whatsapp()

    def _get_multiple_prices(self, parsed: ParsedIntent) -> str:
        if not parsed.symbols:
            return "No symbols found. Example: *ENGRO LUCK PSO*"
        quotes = psx_service.get_multiple_quotes(parsed.symbols)
        if not quotes:
            return "Could not retrieve quotes. Please try again."
        return "\n\n".join(q.format_whatsapp() for q in quotes)

    def _get_indices(self) -> str:
        indices = psx_service.get_index_summary()
        if not indices:
            return "Index data is temporarily unavailable. Please try again."
        lines = ["*Market Indices*", ""]
        lines += [idx.format_whatsapp() for idx in indices]
        status = psx_service.get_market_status()
        lines += ["", f"_{status.message}_"]
        return "\n".join(lines)

    def _get_movers(self) -> str:
        movers = psx_service.get_top_movers(limit=5)
        if not movers:
            return "Mover data is temporarily unavailable. Please try again."
        return movers.format_whatsapp()

    def _get_market_status(self) -> str:
        s = psx_service.get_market_status()
        lines = [
            "*PSX Market Status*",
            s.message,
            f"Current time: {s.current_time_pkt}",
        ]
        if s.opens_at:
            lines.append(f"Opens: {s.opens_at} PKT")
        if s.closes_at:
            lines.append(f"Closes: {s.closes_at} PKT")
        return "\n".join(lines)

    def _get_history(self, parsed: ParsedIntent) -> str:
        sym = parsed.symbol
        period = parsed.period or "1mo"
        if not sym:
            return "Please specify a symbol. Example: *ENGRO history 1mo*"
        data = psx_service.get_historical_data(sym, period)
        if not data or not data.candles:
            return f"No historical data found for *{sym}*."
        candles = data.candles
        first = candles[0]
        last = candles[-1]
        pct_change = ((last.close - first.open) / first.open * 100) if first.open else 0
        sign = "+" if pct_change >= 0 else ""
        lines = [
            f"*{sym}* — {period} history ({len(candles)} sessions)",
            f"Period open:  Rs {first.open:,.2f}",
            f"Period close: Rs {last.close:,.2f}",
            f"Period high:  Rs {max(c.high for c in candles):,.2f}",
            f"Period low:   Rs {min(c.low for c in candles):,.2f}",
            f"Return:       {sign}{pct_change:.2f}%",
        ]
        return "\n".join(lines)

    def _search_symbol(self, parsed: ParsedIntent) -> str:
        query = parsed.query or ""
        results = psx_service.search_symbol(query)
        if not results:
            return f"No PSX symbols found matching '{query}'."
        lines = [f"*Search results for '{query}'*", ""]
        for r in results:
            line = f"  *{r.symbol}* — {r.company_name}"
            if r.sector:
                line += f" ({r.sector})"
            lines.append(line)
        lines.append("\nSend the ticker symbol to get its price.")
        return "\n".join(lines)

    # -----------------------------------------------------------------------
    # Portfolio handlers
    # -----------------------------------------------------------------------

    def _get_portfolio(self, investor: Investor, db: Session) -> str:
        summaries = investor_service.get_portfolio_summary(investor.investor_id, db)
        return investor_service.format_portfolio_whatsapp(summaries)

    def _add_holding(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        sym = parsed.symbol
        qty = parsed.quantity
        avg_p = parsed.avg_price

        if not sym:
            return (
                "Please specify the symbol, quantity, and price.\n"
                "Example: *add ENGRO 100 at 290*"
            )
        if qty is None or avg_p is None:
            return (
                f"I need quantity and price for *{sym}*.\n"
                f"Example: *add {sym} 100 at 290*"
            )

        holding = investor_service.add_holding(
            investor.investor_id,
            HoldingCreate(symbol=sym, quantity=qty, avg_buy_price=avg_p),
            db,
        )
        cost = holding.quantity * holding.avg_buy_price
        return (
            f"*{sym}* position updated in your portfolio.\n"
            f"Shares: {holding.quantity:,.0f}\n"
            f"Avg price: Rs {holding.avg_buy_price:,.2f}\n"
            f"Cost basis: Rs {cost:,.2f}"
        )

    def _remove_holding(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        sym = parsed.symbol
        if not sym:
            return "Which stock should I remove? Example: *remove ENGRO from portfolio*"
        removed = investor_service.remove_holding(investor.investor_id, sym, db)
        if not removed:
            return f"*{sym}* was not found in your portfolio."
        return f"*{sym}* has been removed from your portfolio."

    # -----------------------------------------------------------------------
    # Watchlist handlers
    # -----------------------------------------------------------------------

    def _get_watchlist(self, investor: Investor, db: Session) -> str:
        items = investor_service.get_watchlist(investor.investor_id, db)
        if not items:
            return (
                "Your watchlist is empty.\n"
                "Add a stock: *watch ENGRO*"
            )
        symbols = [i.symbol for i in items]
        quotes = psx_service.get_multiple_quotes(symbols)
        quote_map = {q.symbol: q for q in quotes}

        lines = ["*Your Watchlist*", ""]
        for item in items:
            q = quote_map.get(item.symbol)
            if q:
                sign = "+" if (q.change or 0) >= 0 else ""
                lines.append(
                    f"*{item.symbol}*: Rs {q.current_price:,.2f} "
                    f"({sign}{q.change_pct or 0:.2f}%)"
                )
            else:
                lines.append(f"*{item.symbol}*: price unavailable")
        return "\n".join(lines)

    def _add_watchlist(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        sym = parsed.symbol
        if not sym:
            return "Which stock should I watch? Example: *watch ENGRO*"
        _, created = investor_service.add_to_watchlist(
            investor.investor_id, WatchlistAdd(symbol=sym), db
        )
        if not created:
            return f"*{sym}* is already in your watchlist."
        return f"*{sym}* added to your watchlist. I'll show it with live prices when you type *watchlist*."

    def _remove_watchlist(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        sym = parsed.symbol
        if not sym:
            return "Which stock should I remove from the watchlist? Example: *remove ENGRO from watchlist*"
        removed = investor_service.remove_from_watchlist(investor.investor_id, sym, db)
        if not removed:
            return f"*{sym}* was not found in your watchlist."
        return f"*{sym}* removed from your watchlist."

    # -----------------------------------------------------------------------
    # Alert handlers
    # -----------------------------------------------------------------------

    def _set_alert(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        sym = parsed.symbol
        target = parsed.price
        condition = parsed.condition or "above"

        if not sym or target is None:
            return (
                "To set an alert, I need a symbol, direction, and price.\n"
                "Examples:\n"
                "  *alert ENGRO above 300*\n"
                "  *alert LUCK below 250*"
            )

        alert = investor_service.create_alert(
            investor.investor_id,
            AlertCreate(symbol=sym, condition=condition, target_value=target),
            db,
        )

        direction_txt = {
            "above":           f"rises above Rs {target:,.2f}",
            "below":           f"drops below Rs {target:,.2f}",
            "change_pct_up":   f"gains +{target:.1f}% in a day",
            "change_pct_down": f"loses -{target:.1f}% in a day",
        }.get(condition, f"hits {target}")

        return (
            f"Alert set for *{sym}*.\n"
            f"I'll notify you when {sym} {direction_txt}.\n"
            f"_This is a one-time alert. Type *alerts* to manage._"
        )

    def _list_alerts(self, investor: Investor, db: Session) -> str:
        alerts = investor_service.get_investor_alerts(
            investor.investor_id, db, active_only=False
        )
        if not alerts:
            return (
                "You have no alerts.\n"
                "Set one: *alert ENGRO above 300*"
            )
        lines = [f"*Your Alerts* ({len(alerts)} total)", ""]
        for a in alerts:
            from ..schemas.investor import AlertResponse
            ar = AlertResponse.model_validate(a)
            status = "ACTIVE" if a.is_active else "inactive"
            lines.append(f"[{status}] {ar.describe()}")
        lines.append("\nTo delete: *delete alert ENGRO*")
        return "\n".join(lines)

    def _delete_alert(self, parsed: ParsedIntent, investor: Investor, db: Session) -> str:
        sym = parsed.symbol
        alerts = investor_service.get_investor_alerts(
            investor.investor_id, db, active_only=True
        )
        if sym:
            matching = [a for a in alerts if a.symbol == sym]
        else:
            matching = alerts

        if not matching:
            msg = f"No active alerts found" + (f" for *{sym}*" if sym else "") + "."
            return msg

        # Delete all matching (or all active if no symbol)
        for a in matching:
            investor_service.delete_alert(a, db)

        label = f"for *{sym}*" if sym else "(all active)"
        return f"Deleted {len(matching)} alert(s) {label}."

    # -----------------------------------------------------------------------
    # Notification settings
    # -----------------------------------------------------------------------

    def _toggle_brief(self, investor: Investor, db: Session, enable: bool) -> str:
        investor_service.update(
            investor,
            InvestorUpdate(morning_brief_enabled=enable, notifications_enabled=True if enable else None),
            db,
        )
        if enable:
            return (
                "Morning brief enabled!\n"
                f"You'll receive a daily market update at {investor.morning_brief_time} PKT.\n"
                "To change time, contact support."
            )
        return "Morning brief disabled. You can re-enable it anytime: *morning brief*"


# Singleton
intent_handler = IntentHandler()
