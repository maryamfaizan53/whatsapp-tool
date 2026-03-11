"""
Celery task: check_active_alerts

Runs every 60 seconds (configurable via settings.alert_check_interval).
Exits immediately if PSX market is not open — no wasted DB/API calls at night.

Flow:
  1. Guard: market open? → exit early if not
  2. investor_service.check_alerts()  ← evaluates all active alerts with cooldown
  3. For each triggered result: send WhatsApp notification + write NotificationLog
  4. Returns a summary dict (stored in Celery result backend for monitoring)
"""
import logging
import time
from typing import Any, Dict

from ..celery_app import celery_app
from ..config import settings
from ..database import SessionLocal
from ..services.investor_service import investor_service
from ..services.psx_service import psx_service
from ..services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)
whatsapp = WhatsAppService()


@celery_app.task(
    name="src.tasks.alert_checker.check_active_alerts",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    ignore_result=False,
)
def check_active_alerts(self) -> Dict[str, Any]:
    """
    Evaluate all active PSX price alerts and dispatch WhatsApp notifications
    for those that have triggered.
    """
    # ----------------------------------------------------------------
    # Guard: only run during market hours (PSX Mon–Fri 09:15–15:30 PKT)
    # ----------------------------------------------------------------
    status = psx_service.get_market_status()
    if not status.is_open:
        logger.debug("Alert checker skipped — market is %s", status.session)
        return {"skipped": True, "reason": status.session}

    db = SessionLocal()
    sent = 0
    failed = 0
    evaluated = 0

    try:
        results = investor_service.check_alerts(
            db, cooldown_minutes=settings.alert_cooldown_minutes
        )
        evaluated = len(results)

        for result in results:
            if not result.triggered or not result.message:
                continue

            # Throttle bulk sends to respect WA rate limits
            if sent > 0:
                time.sleep(settings.wa_send_delay_ms / 1000)

            # Look up investor WhatsApp number
            investor = investor_service.get_by_id(result.investor_id, db)
            if not investor or not investor.notifications_enabled:
                continue

            # Send WhatsApp message
            wa_resp = whatsapp.send_message(investor.whatsapp_number, result.message)
            wa_msg_id = wa_resp.get("messages", [{}])[0].get("id")
            success = "messages" in wa_resp

            # Write notification log
            investor_service.log_notification(
                investor_id=result.investor_id,
                notification_type="alert",
                message=result.message,
                db=db,
                alert_id=result.alert_id,
                status="sent" if success else "failed",
                wa_message_id=wa_msg_id,
                error=str(wa_resp) if not success else None,
            )

            if success:
                sent += 1
                logger.info(
                    "Alert sent: investor=%s symbol=%s condition=%s",
                    result.investor_id, result.symbol, result.condition,
                )
            else:
                failed += 1
                logger.warning(
                    "Alert WA send failed: investor=%s resp=%s",
                    result.investor_id, wa_resp,
                )

    except Exception as exc:
        logger.exception("check_active_alerts task failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()

    summary = {
        "skipped": False,
        "market_session": status.session,
        "evaluated": evaluated,
        "triggered": sent + failed,
        "sent": sent,
        "failed": failed,
    }
    logger.info("Alert check complete: %s", summary)
    return summary
