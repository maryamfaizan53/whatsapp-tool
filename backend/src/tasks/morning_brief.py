"""
Celery task: send_morning_briefs

Fires at 09:15 PKT (04:15 UTC) Mon–Fri via Celery beat.

Sends a full market briefing to every investor who has opted in.
Message includes: market status, KSE-100/30/KMI-30 indices,
top 5 gainers and losers from the previous session.

Flow:
  1. Build the market brief string once (all subscribers get same message)
  2. Load all morning-brief subscribers
  3. Send + log for each investor (with inter-send delay)
  4. Return delivery summary
"""
import logging
import time
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

from ..celery_app import celery_app
from ..config import settings
from ..database import SessionLocal
from ..services.investor_service import investor_service
from ..services.psx_service import psx_service
from ..services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)
whatsapp = WhatsAppService()
PKT = ZoneInfo("Asia/Karachi")


@celery_app.task(
    name="src.tasks.morning_brief.send_morning_briefs",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    ignore_result=False,
)
def send_morning_briefs(self) -> Dict[str, Any]:
    """
    Generate a morning market brief and broadcast it to all opted-in investors.
    """
    now_pkt = datetime.now(tz=PKT)
    db = SessionLocal()
    sent = 0
    failed = 0

    try:
        subscribers = investor_service.get_morning_brief_subscribers(db)
        if not subscribers:
            logger.info("Morning brief: no subscribers, nothing to send.")
            return {"sent": 0, "failed": 0, "subscribers": 0}

        # Build brief once — same for all
        brief = _build_morning_brief(now_pkt)

        for investor in subscribers:
            if sent + failed > 0:
                time.sleep(settings.wa_send_delay_ms / 1000)

            wa_resp = whatsapp.send_message(investor.whatsapp_number, brief)
            wa_msg_id = wa_resp.get("messages", [{}])[0].get("id")
            success = "messages" in wa_resp

            investor_service.log_notification(
                investor_id=investor.investor_id,
                notification_type="morning_brief",
                message=brief,
                db=db,
                status="sent" if success else "failed",
                wa_message_id=wa_msg_id,
                error=str(wa_resp) if not success else None,
            )

            if success:
                sent += 1
            else:
                failed += 1
                logger.warning(
                    "Morning brief failed for investor=%s resp=%s",
                    investor.investor_id, wa_resp,
                )

    except Exception as exc:
        logger.exception("send_morning_briefs task failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()

    summary = {
        "date": now_pkt.strftime("%Y-%m-%d"),
        "subscribers": sent + failed,
        "sent": sent,
        "failed": failed,
    }
    logger.info("Morning brief complete: %s", summary)
    return summary


def _build_morning_brief(now: datetime) -> str:
    """Compose the full morning brief message."""
    date_str = now.strftime("%A, %d %b %Y")
    lines = [
        f"*Good morning! PSX Market Brief*",
        f"_{date_str}_",
        "",
    ]

    # Market status
    status = psx_service.get_market_status()
    lines.append(status.message)
    lines.append("")

    # Index values
    indices = psx_service.get_index_summary()
    if indices:
        lines.append("*Indices*")
        for idx in indices:
            lines.append(idx.format_whatsapp())
        lines.append("")

    # Top movers (5 per category)
    movers = psx_service.get_top_movers(limit=5)
    if movers:
        if movers.gainers:
            lines.append("*Top Gainers*")
            for q in movers.gainers[:5]:
                sign = "+" if (q.change_pct or 0) >= 0 else ""
                lines.append(
                    f"  {q.symbol}: Rs {q.current_price:,.2f} ({sign}{q.change_pct or 0:.2f}%)"
                )
            lines.append("")
        if movers.losers:
            lines.append("*Top Losers*")
            for q in movers.losers[:5]:
                lines.append(
                    f"  {q.symbol}: Rs {q.current_price:,.2f} ({q.change_pct or 0:.2f}%)"
                )
            lines.append("")

    lines.append("_Send *help* to see all commands._")
    return "\n".join(lines)
