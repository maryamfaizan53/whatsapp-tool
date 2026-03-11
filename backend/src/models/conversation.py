"""
Conversation Model for WhatsApp RAG Assistant
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    conv_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.business_id"), nullable=False)
    customer_whatsapp_id = Column(String(255), nullable=False)  # Customer's WhatsApp ID
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String(20), default="active")  # 'active', 'closed', 'transferred'
    language_code = Column(String(10), default="en")  # Detected language
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())