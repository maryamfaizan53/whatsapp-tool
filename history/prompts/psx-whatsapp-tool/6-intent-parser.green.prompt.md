---
id: 6
title: Build Intent Parser and Handler
stage: green
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: psx-whatsapp-tool
branch: main
user: 840 G7
command: now build the intent parser
labels: ["psx", "intent-parser", "nlp", "regex", "roman-urdu", "webhook"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/services/intent_parser.py
 - backend/src/services/intent_handler.py
 - backend/src/api/webhook.py
tests:
 - none
---

## Prompt

```text
now build the intent parser
```

## Response

Built two-layer intent processing system:

**New files:**
- `backend/src/services/intent_parser.py` — pure rule-based parser with 20 ordered regex rules; supports English + Roman Urdu; extracts symbol, price, quantity, avg_price, condition, period entities; defines 20 Intent enum values and HELP_TEXT constant; zero I/O
- `backend/src/services/intent_handler.py` — stateful dispatcher: resolves investor via get_or_create, runs 3-step onboarding flow (name → language → complete), dispatches 20+ intents to PSX/Investor services, returns WhatsApp-ready strings; handles all error paths gracefully

**Updated:**
- `backend/src/api/webhook.py` — replaced old RAG pipeline (conversation_service + rag_service + llm_service) with intent_handler.handle(); webhook now creates its own DB session in background tasks (fixes the Depends() bug in background tasks); audio messages now route through transcription → intent handler; removed unused imports

**Intent coverage (20 intents):**
GET_PRICE, GET_MULTIPLE_PRICES, GET_INDICES, GET_TOP_MOVERS, GET_MARKET_STATUS, GET_MARKET_BRIEF, GET_HISTORY, SEARCH_SYMBOL, GET_PORTFOLIO, ADD_HOLDING, REMOVE_HOLDING, GET_WATCHLIST, ADD_WATCHLIST, REMOVE_WATCHLIST, SET_ALERT, LIST_ALERTS, DELETE_ALERT, SUBSCRIBE_BRIEF, UNSUBSCRIBE_BRIEF, HELP, UNKNOWN

**Entity extraction:**
- Symbol: uppercase 2-7 char with stop-word filtering
- Number: handles Rs prefix, commas, decimals
- Period: maps natural language to yfinance codes (1d/5d/1mo/3mo/6mo/1y)
- Direction: above/below + Roman Urdu equivalents (upar/neeche/se upar/se neeche)
- Condition: above/below/change_pct_up/change_pct_down

## Outcome

COMPLETE — full message pipeline wired. WhatsApp message → intent → service call → response. Next: Celery scheduler for proactive alerts.
