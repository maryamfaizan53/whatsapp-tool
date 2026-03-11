"""
Webhook API Endpoints for WhatsApp RAG Assistant
"""
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, status, Depends
from typing import Dict, Any, List
import hashlib
import hmac
from sqlalchemy.orm import Session
from ..services.whatsapp_service import WhatsAppService
from ..services.rag_service import rag_service
from ..services.voice_service import voice_service
from ..services.language_service import language_service
from ..services.llm_service import llm_service
from ..services.conversation_service import conversation_service
from ..database import get_db
from ..config import settings

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
    Process an incoming message in the background
    """
    message_id = message.get("id")
    from_number = message.get("from")
    message_type = message.get("type")
    timestamp = message.get("timestamp")

    # Handle different message types
    if message_type == "text":
        text_content = message.get("text", {}).get("body", "")
        await handle_text_message(from_number, text_content, message_id, timestamp)
    elif message_type == "audio":
        audio = message.get("audio", {})
        await handle_audio_message(from_number, audio, message_id, timestamp)
    elif message_type == "image":
        image = message.get("image", {})
        await handle_image_message(from_number, image, message_id, timestamp)
    else:
        # For other message types, treat as text
        content = message.get("text", {}).get("body", f"Received {message_type} message")
        await handle_text_message(from_number, content, message_id, timestamp)


async def handle_text_message(from_number: str, content: str, message_id: str, timestamp: str, db: Session = Depends(get_db)):
    """
    Handle an incoming text message
    """
    # Get or create conversation
    # For this example, we'll use a fixed business ID
    # In a real implementation, this would come from webhook metadata
    business_id = "default_business_id"  # This should be determined from webhook context
    conversation = conversation_service.get_or_create_conversation(
        business_id, from_number, db
    )

    # Create incoming message record
    conversation_service.create_message(
        conversation_id=str(conversation.conv_id),
        sender_type="customer",
        content=content,
        message_type="text",
        processed_by_rag=False,  # Will be updated after processing
        db=db
    )

    # Detect language
    language_result = language_service.detect_language(content)
    detected_language = language_result["language_code"]

    # Update conversation with detected language
    conversation_service.update_conversation_language(
        str(conversation.conv_id), detected_language, db
    )

    # Process through RAG pipeline
    # For this example, we'll use a default knowledge base
    # In a real implementation, this would be determined by the business
    vector_index_name = f"kb_default"  # Should be retrieved from business config

    rag_result = rag_service.query_knowledge_base(
        vector_index_name=vector_index_name,
        query=content,
        top_k=3
    )

    if rag_result["success"] and rag_result["confidence"] > 0.5:
        # Generate response using LLM with RAG context
        llm_response = llm_service.generate_response(
            query=content,
            context=rag_result["source_nodes"],
            language=detected_language
        )

        final_response = llm_response["response"]
        response_confidence = llm_response["confidence"]
    else:
        # Use fallback response if RAG doesn't provide good results
        fallback_response = llm_service.generate_fallback_response(
            query=content,
            language=detected_language
        )

        final_response = fallback_response["response"]
        response_confidence = fallback_response["confidence"]

    # Create outgoing message record
    conversation_service.create_message(
        conversation_id=str(conversation.conv_id),
        sender_type="system",  # Actually sent by system but representing business
        content=final_response,
        message_type="text",
        processed_by_rag=True,
        confidence_score=response_confidence,
        db=db
    )

    # Send response back to user
    whatsapp_service.send_message(from_number, final_response)


async def handle_audio_message(from_number: str, audio: Dict[str, Any], message_id: str, timestamp: str, db: Session = Depends(get_db)):
    """
    Handle an incoming audio message
    """
    # Get audio media URL
    media_id = audio.get("id")

    # In a real implementation, we would get the media URL from WhatsApp
    # For now, we'll simulate getting the URL
    media_url = f"https://graph.facebook.com/v18.0/{media_id}"  # This is a placeholder

    # Download and transcribe the audio
    transcription_result = voice_service.process_voice_message(media_url)

    if transcription_result["success"]:
        # Get or create conversation
        business_id = "default_business_id"  # Should be determined from webhook context
        conversation = conversation_service.get_or_create_conversation(
            business_id, from_number, db
        )

        # Create incoming message record with audio content
        conversation_service.create_message(
            conversation_id=str(conversation.conv_id),
            sender_type="customer",
            content=transcription_result["text"],
            message_type="voice",
            media_url=media_url,
            processed_by_rag=False,
            db=db
        )

        # Detect language
        language_result = language_service.detect_language(transcription_result["text"])
        detected_language = language_result["language_code"]

        # Update conversation with detected language
        conversation_service.update_conversation_language(
            str(conversation.conv_id), detected_language, db
        )

        # Process through RAG pipeline
        vector_index_name = f"kb_default"  # Should be retrieved from business config
        rag_result = rag_service.query_knowledge_base(
            vector_index_name=vector_index_name,
            query=transcription_result["text"],
            top_k=3
        )

        if rag_result["success"] and rag_result["confidence"] > 0.5:
            # Generate response using LLM with RAG context
            llm_response = llm_service.generate_response(
                query=transcription_result["text"],
                context=rag_result["source_nodes"],
                language=detected_language
            )

            final_response = llm_response["response"]
            response_confidence = llm_response["confidence"]
        else:
            # Use fallback response
            fallback_response = llm_service.generate_fallback_response(
                query=transcription_result["text"],
                language=detected_language
            )

            final_response = fallback_response["response"]
            response_confidence = fallback_response["confidence"]

        # Create outgoing message record
        conversation_service.create_message(
            conversation_id=str(conversation.conv_id),
            sender_type="system",
            content=final_response,
            message_type="text",  # Response is text, even if input was voice
            processed_by_rag=True,
            confidence_score=response_confidence,
            db=db
        )

        # Send response back to user
        whatsapp_service.send_message(from_number, final_response)

    else:
        # Failed to transcribe, send error response
        response = "Sorry, I had trouble understanding your voice message. Could you please send a text message instead?"
        whatsapp_service.send_message(from_number, response)


async def handle_image_message(from_number: str, image: Dict[str, Any], message_id: str, timestamp: str, db: Session = Depends(get_db)):
    """
    Handle an incoming image message
    """
    # Get image media ID
    media_id = image.get("id")

    # Get or create conversation
    business_id = "default_business_id"  # Should be determined from webhook context
    conversation = conversation_service.get_or_create_conversation(
        business_id, from_number, db
    )

    # Create incoming message record for image
    conversation_service.create_message(
        conversation_id=str(conversation.conv_id),
        sender_type="customer",
        content="Image message received",
        message_type="image",
        media_url=f"https://graph.facebook.com/v18.0/{media_id}",  # Placeholder URL
        processed_by_rag=False,
        db=db
    )

    # For now, just acknowledge receipt with a text response
    # In a real implementation, we might use Vision API to analyze the image
    response = "Thanks for your image message. Our team will review it shortly."

    # Create outgoing message record
    conversation_service.create_message(
        conversation_id=str(conversation.conv_id),
        sender_type="system",
        content=response,
        message_type="text",
        processed_by_rag=False,
        confidence_score=0.0,
        db=db
    )

    # Send response back to user
    whatsapp_service.send_message(from_number, response)