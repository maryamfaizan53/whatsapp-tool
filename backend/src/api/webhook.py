"""
Webhook API Endpoints for PSX WhatsApp Bot.
Incoming WhatsApp messages are routed to the IntentHandler.
"""
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, status
from typing import Dict, Any
import hashlib
import hmac
import logging

from ..services.whatsapp_service import WhatsAppService
from ..services.voice_service import voice_service
from ..services.intent_handler import intent_handler
from ..database import SessionLocal
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
whatsapp_service = WhatsAppService()


@router.get("")
async def verify_webhook(
    request: Request
) -> str:
    """
    Verify the webhook with WhatsApp
    """
    hub_verify_token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')

    if not hub_verify_token or not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameters"
        )

    validated_challenge = whatsapp_service.validate_webhook(hub_verify_token, challenge)

    if validated_challenge:
        return validated_challenge
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid verification token"
        )


@router.post("")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Handle incoming webhook notifications from WhatsApp
    """
    payload = await request.json()

    # Verify webhook signature if required
    signature = request.headers.get('X-Hub-Signature-256')
    if signature and settings.webhook_signature_verification:
        if not verify_signature(payload, signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )

    # Process the webhook payload
    object_field = payload.get("object")
    if object_field != "whatsapp_business_account":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid object field"
        )

    # Process entries
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])

            # Process each message
            for message in messages:
                # Add to background tasks for processing
                background_tasks.add_task(process_message, message, value)

    return {"success": True}


def verify_signature(payload: Any, signature: str) -> bool:
    """
    Verify the signature of the webhook payload
    """
    expected_signature = hmac.new(
        settings.webhook_secret.encode(),
        str(payload).encode(),
        hashlib.sha256
    ).hexdigest()

    return signature.endswith(expected_signature)


async def process_message(message: Dict[str, Any], value: Dict[str, Any]):
    """
    Route an incoming WhatsApp message to the PSX intent handler.
    Runs in a FastAPI background task — creates its own DB session.
    """
    from_number = message.get("from")
    message_type = message.get("type")
    message_id = message.get("id")

    if message_type == "text":
        text_content = message.get("text", {}).get("body", "")
        await handle_text_message(from_number, text_content, message_id)

    elif message_type == "audio":
        audio = message.get("audio", {})
        await handle_audio_message(from_number, audio, message_id)

    else:
        # Images and other types: acknowledge and suggest text
        reply = (
            "I can only process text messages right now.\n"
            "Type *help* to see what I can do."
        )
        whatsapp_service.send_message(from_number, reply)
        if message_id:
            whatsapp_service.mark_message_read(message_id)


async def handle_text_message(from_number: str, content: str, message_id: str):
    """
    Pass the message through the PSX intent handler and reply.
    Opens its own DB session — safe to call from a background task.
    """
    db = SessionLocal()
    try:
        reply = intent_handler.handle(from_number, content, db)
        whatsapp_service.send_message(from_number, reply)
        if message_id:
            whatsapp_service.mark_message_read(message_id)
    except Exception:
        logger.exception("handle_text_message failed for %s", from_number)
        whatsapp_service.send_message(
            from_number,
            "Sorry, something went wrong. Please try again later.",
        )
    finally:
        db.close()


async def handle_audio_message(from_number: str, audio: Dict[str, Any], message_id: str):
    """
    Transcribe voice note via Whisper, then pass transcript to intent handler.
    """
    media_id = audio.get("id")
    media_url = f"https://graph.facebook.com/v18.0/{media_id}"

    transcription = voice_service.process_voice_message(media_url)
    if transcription.get("success") and transcription.get("text"):
        await handle_text_message(from_number, transcription["text"], message_id)
    else:
        whatsapp_service.send_message(
            from_number,
            "Sorry, I couldn't transcribe your voice message. Please send a text message.",
        )
        if message_id:
            whatsapp_service.mark_message_read(message_id)