"""
Celery application and beat schedule for the PSX WhatsApp Bot.

Workers:
  celery -A src.celery_app worker --loglevel=info --concurrency=2

Beat (scheduler — run exactly one instance):
  celery -A src.celery_app beat --loglevel=info

Both can be combined for development:
  celery -A src.celery_app worker --beat --loglevel=info

All times are UTC. PSX trades Mon–Fri 09:15–15:30 PKT (= 04:15–10:30 UTC).
"""
from celery import Celery
from celery.schedules import crontab

from .config import settings

celery_app = Celery("psx_bot")

celery_app.conf.update(
    # Transport
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,

    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Time
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_acks_late=True,           # task acked only after completion
    worker_prefetch_multiplier=1,  # one task at a time per worker thread
    task_reject_on_worker_lost=True,

    # Result expiry (keep results for 1 hour only)
    result_expires=3600,

    # Beat schedule
    beat_schedule={
        # ----------------------------------------------------------------
        # Alert checker — runs every 60 s; task guards market hours internally
        # ----------------------------------------------------------------
        "check-active-alerts": {
            "task": "src.tasks.alert_checker.check_active_alerts",
            "schedule": settings.alert_check_interval,   # default 60 s
            "options": {"expires": 55},  # discard if not started within 55 s
        },

        # ----------------------------------------------------------------
        # Morning brief — 09:15 PKT = 04:15 UTC, Mon–Fri
        # ----------------------------------------------------------------
        "send-morning-briefs": {
            "task": "src.tasks.morning_brief.send_morning_briefs",
            "schedule": crontab(hour=4, minute=15, day_of_week="mon-fri"),
        },

        # ----------------------------------------------------------------
        # End-of-day summary — 15:35 PKT = 10:35 UTC, Mon–Fri
        # (5 min after market close to let final prices settle)
        # ----------------------------------------------------------------
        "send-eod-summaries": {
            "task": "src.tasks.eod_summary.send_eod_summaries",
            "schedule": crontab(hour=10, minute=35, day_of_week="mon-fri"),
        },
    },
)

# Auto-discover tasks in src/tasks/
celery_app.autodiscover_tasks(["src.tasks"])
