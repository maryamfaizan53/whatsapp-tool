"""
Conversation Service for WhatsApp RAG Assistant
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.conversation import Conversation
from ..models.message import Message
from ..models.business import Business


class ConversationService:
    def __init__(self):
        pass

    def get_or_create_conversation(
        self,
        business_id: str,
        customer_whatsapp_id: str,
        db: Session
    ) -> Conversation:
        """
        Get an existing conversation or create a new one
        """
        # Try to find an active conversation
        conversation = db.query(Conversation).filter(
            Conversation.business_id == business_id,
            Conversation.customer_whatsapp_id == customer_whatsapp_id,
            Conversation.status == "active"
        ).first()

        if not conversation:
            # Create a new conversation
            conversation = Conversation(
                business_id=business_id,
                customer_whatsapp_id=customer_whatsapp_id,
                status="active"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        return conversation

    def create_message(
        self,
        conversation_id: str,
        sender_type: str,
        content: str,
        message_type: str = "text",
        media_url: str = None,
        processed_by_rag: bool = False,
        confidence_score: float = 0.0,
        db: Session = None
    ) -> Message:
        """
        Create a new message in a conversation
        """
        message = Message(
            conv_id=conversation_id,
            sender_type=sender_type,
            content=content,
            message_type=message_type,
            media_url=media_url,
            processed_by_rag=processed_by_rag,
            confidence_score=confidence_score
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        # Update the conversation's last message timestamp
        conversation = db.query(Conversation).filter(
            Conversation.conv_id == conversation_id
        ).first()

        if conversation:
            conversation.last_message_at = datetime.utcnow()
            db.commit()

        return message

    def get_conversation_history(
        self,
        conversation_id: str,
        db: Session,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get the message history for a conversation
        """
        messages = db.query(Message).filter(
            Message.conv_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

        return [
            {
                "msg_id": str(msg.msg_id),
                "sender_type": msg.sender_type,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
                "processed_by_rag": msg.processed_by_rag,
                "confidence_score": msg.confidence_score
            }
            for msg in reversed(messages)  # Reverse to get chronological order
        ]

    def get_business_conversations(
        self,
        business_id: str,
        db: Session,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations for a business
        """
        conversations = db.query(Conversation).filter(
            Conversation.business_id == business_id
        ).order_by(Conversation.last_message_at.desc()).limit(limit).all()

        return [
            {
                "conv_id": str(conv.conv_id),
                "customer_whatsapp_id": conv.customer_whatsapp_id,
                "started_at": conv.started_at.isoformat(),
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "status": conv.status,
                "language_code": conv.language_code
            }
            for conv in conversations
        ]

    def close_conversation(
        self,
        conversation_id: str,
        db: Session
    ) -> bool:
        """
        Close a conversation
        """
        conversation = db.query(Conversation).filter(
            Conversation.conv_id == conversation_id
        ).first()

        if conversation:
            conversation.status = "closed"
            conversation.last_message_at = datetime.utcnow()
            db.commit()
            return True

        return False

    def transfer_conversation(
        self,
        conversation_id: str,
        db: Session
    ) -> bool:
        """
        Mark a conversation as transferred to human support
        """
        conversation = db.query(Conversation).filter(
            Conversation.conv_id == conversation_id
        ).first()

        if conversation:
            conversation.status = "transferred"
            conversation.last_message_at = datetime.utcnow()
            db.commit()
            return True

        return False

    def update_conversation_language(
        self,
        conversation_id: str,
        language_code: str,
        db: Session
    ) -> bool:
        """
        Update the language code for a conversation
        """
        conversation = db.query(Conversation).filter(
            Conversation.conv_id == conversation_id
        ).first()

        if conversation:
            conversation.language_code = language_code
            db.commit()
            return True

        return False


# Global instance
conversation_service = ConversationService()