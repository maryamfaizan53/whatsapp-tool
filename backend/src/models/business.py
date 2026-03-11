"""
Business Model for WhatsApp RAG Assistant
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class Business(Base):
    __tablename__ = "businesses"

    business_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    whatsapp_phone_number_id = Column(String(255), nullable=True)  # Meta's phone number ID
    whatsapp_access_token = Column(Text, nullable=True)  # Encrypted token
    webhook_url = Column(String(500), nullable=True)  # Configured webhook endpoint
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    hashed_password = Column(String(255), nullable=True)  # Hashed password
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default="free")  # Pricing tier