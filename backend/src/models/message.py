"""
Message Model for WhatsApp RAG Assistant
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class Message(Base):
    __tablename__ = "messages"

    msg_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conv_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conv_id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'customer', 'business', 'system'
    content = Column(Text, nullable=False)  # Message content
    media_url = Column(String(500), nullable=True)  # URL to voice/image media if applicable
    message_type = Column(String(20), default="text")  # 'text', 'voice', 'image', 'template'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processed_by_rag = Column(Boolean, default=False)  # Whether RAG was used
    confidence_score = Column(Float, default=0.0)  # RAG response confidence
    created_at = Column(DateTime(timezone=True), server_default=func.now())