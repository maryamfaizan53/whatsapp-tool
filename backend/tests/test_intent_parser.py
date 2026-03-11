"""
Unit tests for IntentParser.

Pure function tests — no I/O, no mocks, no database.
Covers all 20 intents with English and Roman Urdu variants,
plus entity extraction (symbol, price, quantity, condition, period).
"""
import pytest
from src.services.intent_parser import Intent, IntentParser

parser = IntentParser()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse(text: str):
    return parser.parse(text)


# ---------------------------------------------------------------------------
# HELP
# ---------------------------------------------------------------------------

class TestHelp:
    def test_help_keyword(self):
        r = parse("help")
        assert r.intent == Intent.HELP

    def test_hi_greeting(self):
        r = parse("hi")
        assert r.intent == Intent.HELP

    def test_salam(self):
        r = parse("salam")
        assert r.intent == Intent.HELP

    def test_commands(self):
        r = parse("commands")
        assert r.intent == Intent.HELP

    def test_question_mark(self):
        r = parse("?")
        assert r.intent == Intent.HELP

    def test_madad(self):
        r = parse("madad chahiye")
        assert r.intent == Intent.HELP


# ---------------------------------------------------------------------------
# GET_PRICE (single symbol)
# ---------------------------------------------------------------------------

class TestGetPrice:
    def test_bare_symbol(self):
        r = parse("ENGRO")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "ENGRO"

    def test_lowercase_symbol(self):
        r = parse("engro")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "ENGRO"

    def test_price_suffix(self):
        r = parse("LUCK price")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "LUCK"

    def test_rate_suffix(self):
        r = parse("PSO rate")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "PSO"

    def test_roman_urdu_ka_rate(self):
        r = parse("ENGRO ka rate")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "ENGRO"

    def test_roman_urdu_kya_hai(self):
        r = parse("OGDC kya hai")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "OGDC"

    def test_price_of_prefix(self):
        r = parse("price of HBL")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "HBL"

    def test_symbol_with_question(self):
        r = parse("NESTLE?")
        assert r.intent == Intent.GET_PRICE
        assert r.symbol == "NESTLE"


# ---------------------------------------------------------------------------
# GET_MULTIPLE_PRICES
# ---------------------------------------------------------------------------

class TestGetMultiplePrices:
    def test_space_separated(self):
        r = parse("ENGRO LUCK PSO")
        assert r.intent == Intent.GET_MULTIPLE_PRICES
        assert set(r.symbols) == {"ENGRO", "LUCK", "PSO"}

    def test_two_symbols(self):
        r = parse("HBL UBL")
        assert r.intent == Intent.GET_MULTIPLE_PRICES
        assert len(r.symbols) == 2

    def test_with_prices_keyword(self):
        r = parse("ENGRO LUCK prices")
        assert r.intent == Intent.GET_MULTIPLE_PRICES
        assert "ENGRO" in r.symbols
        assert "LUCK" in r.symbols

    def test_deduplication(self):
        r = parse("ENGRO ENGRO LUCK")
        assert r.intent == Intent.GET_MULTIPLE_PRICES
        assert r.symbols.count("ENGRO") == 1


# ---------------------------------------------------------------------------
# GET_INDICES
# ---------------------------------------------------------------------------

class TestGetIndices:
    def test_kse100(self):
        r = parse("KSE100")
        assert r.intent == Intent.GET_INDICES

    def test_kse_100_hyphen(self):
        r = parse("KSE-100")
        assert r.intent == Intent.GET_INDICES

    def test_indices_keyword(self):
        r = parse("indices")
        assert r.intent == Intent.GET_INDICES

    def test_index_keyword(self):
        r = parse("index")
        assert r.intent == Intent.GET_INDICES

    def test_kmi30(self):
        r = parse("KMI-30")
        assert r.intent == Intent.GET_INDICES


# ---------------------------------------------------------------------------
# GET_TOP_MOVERS
# ---------------------------------------------------------------------------

class TestGetTopMovers:
    def test_gainers(self):
        r = parse("top gainers")
        assert r.intent == Intent.GET_TOP_MOVERS

    def test_losers(self):
        r = parse("losers")
        assert r.intent == Intent.GET_TOP_MOVERS

    def test_movers(self):
        r = parse("movers")
        assert r.intent == Intent.GET_TOP_MOVERS

    def test_most_active(self):
        r = parse("most active")
        assert r.intent == Intent.GET_TOP_MOVERS


# ---------------------------------------------------------------------------
# GET_MARKET_STATUS
# ---------------------------------------------------------------------------

class TestGetMarketStatus:
    def test_is_market_open(self):
        r = parse("is market open")
        assert r.intent == Intent.GET_MARKET_STATUS

    def test_market_status(self):
        r = parse("market status")
        assert r.intent == Intent.GET_MARKET_STATUS

    def test_market_band_hai(self):
        r = parse("market band hai")
        assert r.intent == Intent.GET_MARKET_STATUS

    def test_market_open_hai(self):
        r = parse("market open hai")
        assert r.intent == Intent.GET_MARKET_STATUS


# ---------------------------------------------------------------------------
# GET_MARKET_BRIEF
# ---------------------------------------------------------------------------

class TestGetMarketBrief:
    def test_bare_market(self):
        r = parse("market")
        assert r.intent == Intent.GET_MARKET_BRIEF

    def test_market_summary(self):
        r = parse("market summary")
        assert r.intent == Intent.GET_MARKET_BRIEF

    def test_market_update(self):
        r = parse("market update")
        assert r.intent == Intent.GET_MARKET_BRIEF

    def test_aaj_ka_market(self):
        r = parse("aaj ka market")
        assert r.intent == Intent.GET_MARKET_BRIEF


# ---------------------------------------------------------------------------
# SEARCH_SYMBOL
# ---------------------------------------------------------------------------

class TestSearchSymbol:
    def test_search_prefix(self):
        r = parse("search engro")
        assert r.intent == Intent.SEARCH_SYMBOL
        assert r.query == "engro"

    def test_find_prefix(self):
        r = parse("find petroleum")
        assert r.intent == Intent.SEARCH_SYMBOL
        assert r.query == "petroleum"

    def test_dhundo(self):
        r = parse("dhundo pakistan")
        assert r.intent == Intent.SEARCH_SYMBOL
        assert r.query == "pakistan"


# ---------------------------------------------------------------------------
# GET_PORTFOLIO
# ---------------------------------------------------------------------------

class TestGetPortfolio:
    def test_portfolio(self):
        r = parse("portfolio")
        assert r.intent == Intent.GET_PORTFOLIO

    def test_mera_portfolio(self):
        r = parse("mera portfolio")
        assert r.intent == Intent.GET_PORTFOLIO

    def test_my_portfolio(self):
        r = parse("my portfolio")
        assert r.intent == Intent.GET_PORTFOLIO

    def test_holdings(self):
        r = parse("my holdings")
        assert r.intent == Intent.GET_PORTFOLIO


# ---------------------------------------------------------------------------
# ADD_HOLDING  —  entity extraction
# ---------------------------------------------------------------------------

class TestAddHolding:
    def test_add_with_at(self):
        r = parse("add ENGRO 100 at 290")
        assert r.intent == Intent.ADD_HOLDING
        assert r.symbol == "ENGRO"
        assert r.quantity == 100.0
        assert r.avg_price == 290.0

    def test_at_symbol(self):
        r = parse("ENGRO 200 @ 310.50")
        assert r.intent == Intent.ADD_HOLDING
        assert r.symbol == "ENGRO"
        assert r.quantity == 200.0
        assert r.avg_price == 310.50

    def test_bought_keyword(self):
        r = parse("bought LUCK 500 at 580")
        assert r.intent == Intent.ADD_HOLDING
        assert r.symbol == "LUCK"
        assert r.quantity == 500.0
        assert r.avg_price == 580.0

    def test_decimal_price(self):
        r = parse("add HBL 50 at 145.75")
        assert r.intent == Intent.ADD_HOLDING
        assert r.avg_price == pytest.approx(145.75)

    def test_price_with_comma(self):
        r = parse("add NESTLE 10 at 6,500")
        assert r.intent == Intent.ADD_HOLDING
        assert r.avg_price == 6500.0


# ---------------------------------------------------------------------------
# REMOVE_HOLDING
# ---------------------------------------------------------------------------

class TestRemoveHolding:
    def test_remove_from_portfolio(self):
        r = parse("remove ENGRO from portfolio")
        assert r.intent == Intent.REMOVE_HOLDING
        assert r.symbol == "ENGRO"


# ---------------------------------------------------------------------------
# WATCHLIST
# ---------------------------------------------------------------------------

class TestWatchlist:
    def test_get_watchlist_bare(self):
        r = parse("watchlist")
        assert r.intent == Intent.GET_WATCHLIST

    def test_get_my_watchlist(self):
        r = parse("my watchlist")
        assert r.intent == Intent.GET_WATCHLIST

    def test_add_watch_shorthand(self):
        r = parse("watch ENGRO")
        assert r.intent == Intent.ADD_WATCHLIST
        assert r.symbol == "ENGRO"

    def test_remove_from_watchlist(self):
        r = parse("remove LUCK from watchlist")
        assert r.intent == Intent.REMOVE_WATCHLIST
        assert r.symbol == "LUCK"


# ---------------------------------------------------------------------------
# SET_ALERT  —  entity extraction
# ---------------------------------------------------------------------------

class TestSetAlert:
    def test_alert_above(self):
        r = parse("alert ENGRO above 300")
        assert r.intent == Intent.SET_ALERT
        assert r.symbol == "ENGRO"
        assert r.condition == "above"
        assert r.price == 300.0

    def test_alert_below(self):
        r = parse("alert LUCK below 500")
        assert r.intent == Intent.SET_ALERT
        assert r.symbol == "LUCK"
        assert r.condition == "below"
        assert r.price == 500.0

    def test_roman_urdu_se_upar(self):
        r = parse("ENGRO 300 se upar hone pe batao")
        assert r.intent == Intent.SET_ALERT
        assert r.symbol == "ENGRO"
        assert r.condition == "above"
        assert r.price == 300.0

    def test_roman_urdu_se_neeche(self):
        r = parse("OGDC 150 se neeche jaye alert")
        assert r.intent == Intent.SET_ALERT
        assert r.symbol == "OGDC"
        assert r.condition == "below"
        assert r.price == 150.0

    def test_alert_decimal_price(self):
        r = parse("alert PSO above 275.50")
        assert r.intent == Intent.SET_ALERT
        assert r.price == pytest.approx(275.50)

    def test_change_pct_alert(self):
        r = parse("alert ENGRO 3% upar")
        assert r.intent == Intent.SET_ALERT
        assert r.condition == "change_pct_up"


# ---------------------------------------------------------------------------
# LIST_ALERTS / DELETE_ALERT
# ---------------------------------------------------------------------------

class TestAlerts:
    def test_list_alerts_bare(self):
        r = parse("alerts")
        assert r.intent == Intent.LIST_ALERTS

    def test_my_alerts(self):
        r = parse("my alerts")
        assert r.intent == Intent.LIST_ALERTS

    def test_delete_alert_with_symbol(self):
        r = parse("delete alert ENGRO")
        assert r.intent == Intent.DELETE_ALERT
        assert r.symbol == "ENGRO"

    def test_remove_alert(self):
        r = parse("alert hatao LUCK")
        assert r.intent == Intent.DELETE_ALERT


# ---------------------------------------------------------------------------
# GET_HISTORY  —  period extraction
# ---------------------------------------------------------------------------

class TestGetHistory:
    def test_one_month(self):
        r = parse("ENGRO history 1mo")
        assert r.intent == Intent.GET_HISTORY
        assert r.symbol == "ENGRO"
        assert r.period == "1mo"

    def test_natural_one_month(self):
        r = parse("LUCK history 1 month")
        assert r.intent == Intent.GET_HISTORY
        assert r.period == "1mo"

    def test_three_months(self):
        r = parse("HBL chart 3mo")
        assert r.intent == Intent.GET_HISTORY
        assert r.period == "3mo"

    def test_one_year(self):
        r = parse("PSO history 1 year")
        assert r.intent == Intent.GET_HISTORY
        assert r.period == "1y"

    def test_default_period_when_missing(self):
        r = parse("ENGRO history")
        assert r.intent == Intent.GET_HISTORY
        assert r.period == "1mo"   # default


# ---------------------------------------------------------------------------
# SUBSCRIBE / UNSUBSCRIBE morning brief
# ---------------------------------------------------------------------------

class TestMorningBrief:
    def test_subscribe(self):
        r = parse("morning brief")
        assert r.intent == Intent.SUBSCRIBE_BRIEF

    def test_subscribe_daily_update(self):
        r = parse("daily update chahiye")
        assert r.intent == Intent.SUBSCRIBE_BRIEF

    def test_unsubscribe_off(self):
        r = parse("morning brief off")
        assert r.intent == Intent.UNSUBSCRIBE_BRIEF

    def test_unsubscribe_stop(self):
        r = parse("daily update stop")
        assert r.intent == Intent.UNSUBSCRIBE_BRIEF


# ---------------------------------------------------------------------------
# UNKNOWN
# ---------------------------------------------------------------------------

class TestUnknown:
    def test_gibberish(self):
        # Use words longer than 7 chars — the parser only extracts 2–7 char tokens
        r = parse("randomlongword anotherrandomlongword")
        assert r.intent == Intent.UNKNOWN

    def test_empty_string(self):
        r = parse("")
        assert r.intent == Intent.UNKNOWN

    def test_only_numbers(self):
        r = parse("12345 67890")
        assert r.intent == Intent.UNKNOWN

    def test_very_long_nonsense(self):
        r = parse("x " * 50)
        assert r.intent == Intent.UNKNOWN


# ---------------------------------------------------------------------------
# Entity extraction edge cases
# ---------------------------------------------------------------------------

class TestEntityExtraction:
    def test_stop_words_not_extracted_as_symbol(self):
        r = parse("HELP")
        assert r.intent == Intent.HELP   # not GET_PRICE

    def test_at_not_extracted_as_symbol(self):
        # "AT" is a stop word — should not be treated as a PSX ticker
        r = parse("add ENGRO 100 at 290")
        assert r.symbol == "ENGRO"
        assert r.symbol != "AT"

    def test_price_with_rs_prefix(self):
        r = parse("alert LUCK above Rs 500")
        assert r.intent == Intent.SET_ALERT
        assert r.price == 500.0

    def test_symbol_case_normalisation(self):
        r = parse("engro ka rate")
        assert r.symbol == "ENGRO"

    def test_period_week(self):
        from src.services.intent_parser import _period
        assert _period("ENGRO history week") == "5d"

    def test_period_year(self):
        from src.services.intent_parser import _period
        assert _period("ek saal ka data") == "1y"

    def test_all_nums_extracts_multiple(self):
        from src.services.intent_parser import _all_nums
        assert _all_nums("100 at 290.50") == [100.0, 290.50]

    def test_syms_deduplication(self):
        from src.services.intent_parser import _syms
        result = _syms("ENGRO ENGRO LUCK")
        assert result.count("ENGRO") == 1
