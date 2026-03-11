"""
Dashboard API Endpoints for WhatsApp RAG Assistant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..database import get_db
from ..models.business import Business
from ..models.conversation import Conversation
from ..services.auth_service import get_current_business
from ..services.widget_service import widget_service
from ..services.conversation_service import conversation_service
from ..schemas.widget import WidgetConfigUpdate, WidgetConfigResponse

router = APIRouter()


@router.get("/widget-config", response_model=WidgetConfigResponse)
def get_widget_configuration(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Get the widget configuration for the current business."""
    widget_config = widget_service.get_widget_configuration(
        str(current_business.business_id), db
    )

    return WidgetConfigResponse(
        widget_id=str(widget_config.widget_id),
        position=widget_config.position,
        color_scheme=widget_config.color_scheme,
        icon_type=widget_config.icon_type,
        pre_filled_message=widget_config.pre_filled_message,
        is_enabled=widget_config.is_enabled
    )


@router.put("/widget-config", response_model=WidgetConfigResponse)
def update_widget_configuration(
    config_data: WidgetConfigUpdate,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Update the widget configuration for the current business."""
    updated_config = widget_service.update_widget_configuration(
        str(current_business.business_id),
        config_data.dict(exclude_unset=True),
        db
    )

    return WidgetConfigResponse(
        widget_id=str(updated_config.widget_id),
        position=updated_config.position,
        color_scheme=updated_config.color_scheme,
        icon_type=updated_config.icon_type,
        pre_filled_message=updated_config.pre_filled_message,
        is_enabled=updated_config.is_enabled
    )


@router.get("/widget-config/generate")
def generate_widget_code(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Generate the embeddable widget code for the current business."""
    widget_code = widget_service.generate_widget_code(
        str(current_business.business_id), db
    )

    return widget_code


@router.get("/analytics/conversations")
def get_conversation_analytics(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Get conversation statistics for the current business."""
    # Get all conversations for the business
    conversations = conversation_service.get_business_conversations(
        str(current_business.business_id), db
    )

    # Calculate analytics
    total_conversations = len(conversations)

    # For demo purposes, returning placeholder values
    # In a real implementation, this would calculate actual metrics
    analytics = {
        "total_conversations": total_conversations,
        "avg_response_time": 1.5,  # Placeholder in seconds
        "languages_used": {
            "en": 60,
            "es": 20,
            "fr": 10,
            "other": 10
        },
        "resolution_rate": 85.5,  # Percentage
        "active_conversations": sum(1 for conv in conversations if conv["status"] == "active")
    }

    return analytics


@router.get("/conversations")
def get_conversations(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Get conversation history for the current business."""
    conversations = conversation_service.get_business_conversations(
        str(current_business.business_id), db
    )

    return {"conversations": conversations}


@router.get("/conversations/{conv_id}/messages")
def get_conversation_messages(
    conv_id: str,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Get messages for a specific conversation."""
    # Verify that the conversation belongs to the current business
    conversation = db.query(Conversation).filter(
        Conversation.conv_id == conv_id,
        Conversation.business_id == current_business.business_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = conversation_service.get_conversation_history(conv_id, db)

    return {"messages": messages}