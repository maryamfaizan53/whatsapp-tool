---
id: 5
title: Build Investor and Alert Models
stage: green
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: psx-whatsapp-tool
branch: main
user: 840 G7
command: build investor model and alert model
labels: ["psx", "investor", "alert", "portfolio", "watchlist", "notification"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/models/investor.py
 - backend/src/schemas/investor.py
 - backend/src/services/investor_service.py
 - backend/src/api/investor.py
 - backend/src/main.py
tests:
 - none
---

## Prompt

```text
now build the investor model and alert model
```

## Response

Built full investor data layer across 4 new files and 1 updated file:

**New files:**
- `backend/src/models/investor.py` — 5 SQLAlchemy models: `Investor`, `Watchlist`, `Holding`, `Alert`, `NotificationLog`
- `backend/src/schemas/investor.py` — typed Pydantic schemas with validators for all models including `PortfolioSummary` (live P&L), `AlertCheckResult`, and `AlertResponse.describe()`
- `backend/src/services/investor_service.py` — `InvestorService` singleton covering: get_or_create, CRUD, watchlist, holdings (weighted average price on add), portfolio P&L enrichment, alert CRUD, `check_alerts()` for Celery, notification log CRUD, WhatsApp message formatters
- `backend/src/api/investor.py` — 18 REST endpoints under `/api/investors/`

**Updated:**
- `backend/src/main.py` — registered investor router at `/api/investors`

**Key design decisions:**
- Investor identity = `whatsapp_number` (E.164), verified by Meta — no password
- `Holding.add_holding()` merges positions using weighted average price
- `Alert.check_alerts()` batch-fetches quotes, evaluates conditions, deactivates one-shot alerts on trigger — designed for Celery beat
- 4 alert conditions: above, below, change_pct_up, change_pct_down
- `NotificationLog` is immutable audit trail — every WA message recorded

## Outcome

COMPLETE — investor + alert layer done. Next: intent parser to wire WhatsApp messages to these services.
