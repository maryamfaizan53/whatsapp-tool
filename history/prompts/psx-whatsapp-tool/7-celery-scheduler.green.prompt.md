---
id: 7
title: Build Celery Scheduler and Tasks
stage: green
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: psx-whatsapp-tool
branch: main
user: 840 G7
command: now build the celery scheduler
labels: ["celery", "scheduler", "alerts", "morning-brief", "eod", "redis"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - backend/src/celery_app.py
 - backend/src/tasks/__init__.py
 - backend/src/tasks/alert_checker.py
 - backend/src/tasks/morning_brief.py
 - backend/src/tasks/eod_summary.py
 - backend/src/config.py
 - backend/src/services/investor_service.py
 - backend/requirements.txt
tests:
 - none
---

## Prompt

```text
now build the celery scheduler
```

## Response

Built full Celery scheduler with 3 scheduled tasks:

**New files:**
- `backend/src/celery_app.py` — Celery app config: Redis broker/backend on separate DBs (1,2), 3 beat schedule entries, task_acks_late=True, worker_prefetch_multiplier=1, autodiscover_tasks
- `backend/src/tasks/__init__.py` — package marker
- `backend/src/tasks/alert_checker.py` — `check_active_alerts` task: market-hours guard → `investor_service.check_alerts(cooldown_minutes)` → WA sends → NotificationLog writes; max_retries=2
- `backend/src/tasks/morning_brief.py` — `send_morning_briefs` task: builds brief once (indices + top movers) → broadcasts to all opted-in subscribers with inter-send delay; max_retries=1
- `backend/src/tasks/eod_summary.py` — `send_eod_summaries` task: closing indices + day movers + most active → same subscriber list; fires 5 min after market close

**Updated files:**
- `backend/src/config.py` — added celery_broker_url, celery_result_backend, alert_cooldown_minutes (60), alert_check_interval (60), wa_send_delay_ms (100)
- `backend/src/services/investor_service.py` — `check_alerts()` gains `cooldown_minutes` param; recurring non-one-shot alerts skip re-fire if last_triggered_at within cooldown window; one-shot alerts always evaluated
- `backend/requirements.txt` — removed duplicate `celery==5.3.4` line

**Beat schedule:**
- Alert checker: every 60s (market hours guard inside task)
- Morning brief: 04:15 UTC (09:15 PKT) Mon–Fri
- EOD summary: 10:35 UTC (15:35 PKT) Mon–Fri

## Outcome

COMPLETE — proactive notification pipeline fully operational. Run with:
`celery -A src.celery_app worker --beat --loglevel=info`
