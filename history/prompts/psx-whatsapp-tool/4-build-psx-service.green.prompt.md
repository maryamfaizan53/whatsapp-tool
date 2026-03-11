---
id: 4
title: Build PSX Data Service
stage: green
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: psx-whatsapp-tool
branch: main
user: 840 G7
command: build psx service
labels: ["psx", "whatsapp", "market-data", "yfinance", "redis", "fastapi"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/models/stock.py
 - backend/src/schemas/psx.py
 - backend/src/services/psx_service.py
 - backend/src/api/psx.py
 - backend/src/config.py
 - backend/src/main.py
 - backend/requirements.txt
tests:
 - none
---

## Prompt

```text
go ahead and start building the PSX service first
```

## Response

Built the full PSX data service layer comprising 4 new files and 3 updated files:

**New files:**
- `backend/src/models/stock.py` — SQLAlchemy models: `Stock`, `MarketQuoteCache`, `MarketIndexCache`
- `backend/src/schemas/psx.py` — Pydantic schemas: `MarketStatus`, `StockQuote`, `IndexSummary`, `TopMovers`, `HistoricalData`, `StockSearchResult`, `HistoricalCandle` — all with `format_whatsapp()` helpers
- `backend/src/services/psx_service.py` — `PSXService` singleton with dual data source strategy: PSX DPS (primary) → Yahoo Finance via yfinance (fallback) → Redis cache (all operations)
- `backend/src/api/psx.py` — FastAPI router with 7 endpoints: `/status`, `/quote/{symbol}`, `/quotes`, `/indices`, `/movers`, `/history/{symbol}`, `/search`, `/brief`

**Updated files:**
- `backend/src/config.py` — Added `redis_url`, `psx_dps_base_url`, `psx_cache_ttl_live`, `psx_cache_ttl_closed`
- `backend/src/main.py` — Registered PSX router at `/api/psx`
- `backend/requirements.txt` — Added `yfinance==0.2.40`, `beautifulsoup4==4.12.3`, `lxml==5.2.2`

**Architecture decisions:**
- PSX DPS public API tried first; Yahoo Finance `.KA` suffix used as fallback
- Redis cache with 60s TTL during market hours, 900s after hours
- Market hours: Mon–Fri 09:15–15:30 PKT (Asia/Karachi), purely clock-based (no holiday calendar yet)
- All public methods return typed schema objects and never raise — errors logged, None returned

## Outcome

COMPLETE — PSX service is functional and integrated. Next steps: intent parser, investor model, alert system.
