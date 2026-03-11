"""
Celery task: send_eod_summaries

Fires at 15:35 PKT (10:35 UTC) Mon–Fri — 5 minutes after market close.

Sends an end-of-day recap to all morning-brief subscribers.
Message includes: day's index performance, top gainers/losers,
and a prompt to check their portfolio.

Flow:
  1. Build EOD summary string once
  2. Load all morning-brief subscribers (they double as EOD recipients)
  3. Send + log for each investor
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
    name="src.tasks.eod_summary.send_eod_summaries",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    ignore_result=False,
)
def send_eod_summaries(self) -> Dict[str, Any]:
    """
    Generate an end-of-day market summary and broadcast to opted-in investors.
    """
    now_pkt = datetime.now(tz=PKT)
    db = SessionLocal()
    sent = 0
    failed = 0

    try:
        subscribers = investor_service.get_morning_brief_subscribers(db)
        if not subscribers:
            logger.info("EOD summary: no subscribers.")
            return {"sent": 0, "failed": 0, "subscribers": 0}

        summary_msg = _build_eod_summary(now_pkt)

        for investor in subscribers:
            if sent + failed > 0:
                time.sleep(settings.wa_send_delay_ms / 1000)

            wa_resp = whatsapp.send_message(investor.whatsapp_number, summary_msg)
            wa_msg_id = wa_resp.get("messages", [{}])[0].get("id")
            success = "messages" in wa_resp

            investor_service.log_notification(
                investor_id=investor.investor_id,
                notification_type="eod_summary",
                message=summary_msg,
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
                    "EOD summary failed for investor=%s resp=%s",
                    investor.investor_id, wa_resp,
                )

    except Exception as exc:
        logger.exception("send_eod_summaries task failed")
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
    logger.info("EOD summary complete: %s", summary)
    return summary


def _build_eod_summary(now: datetime) -> str:
    """Compose the end-of-day recap message."""
    date_str = now.strftime("%A, %d %b %Y")
    lines = [
        f"*PSX Market Closed — End of Day*",
        f"_{date_str}_",
        "",
        "PSX trading session has ended for the day.",
        "",
    ]

    # Final index values
    indices = psx_service.get_index_summary()
    if indices:
        lines.append("*Closing Indices*")
        for idx in indices:
            direction = "+" if (idx.change or 0) >= 0 else ""
            lines.append(
                f"  *{idx.index_name}*: {idx.value:,.2f} "
                f"({direction}{idx.change_pct or 0:.2f}%)"
            )
        lines.append("")

    # Day's movers
    movers = psx_service.get_top_movers(limit=5)
    if movers:
        if movers.gainers:
            lines.append("*Top Gainers Today*")
            for q in movers.gainers[:5]:
                sign = "+" if (q.change_pct or 0) >= 0 else ""
                lines.append(
                    f"  {q.symbol}: Rs {q.current_price:,.2f} ({sign}{q.change_pct or 0:.2f}%)"
                )
            lines.append("")

        if movers.losers:
            lines.append("*Top Losers Today*")
            for q in movers.losers[:5]:
                lines.append(
                    f"  {q.symbol}: Rs {q.current_price:,.2f} ({q.change_pct or 0:.2f}%)"
                )
            lines.append("")

        if movers.most_active:
            lines.append("*Most Active*")
            for q in movers.most_active[:3]:
                vol = f"{q.volume:,}" if q.volume else "N/A"
                lines.append(f"  {q.symbol}: {vol} shares")
            lines.append("")

    lines.append("_Send *portfolio* to check your P&L._")
    lines.append("_PSX reopens tomorrow at 09:15 PKT._")
    return "\n".join(lines)
