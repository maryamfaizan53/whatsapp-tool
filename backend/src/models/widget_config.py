"""
Widget Configuration Model for WhatsApp RAG Assistant
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class WidgetConfiguration(Base):
    __tablename__ = "widget_configurations"

    widget_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.business_id"), nullable=False)
    position = Column(String(20), default="bottom-right")  # 'bottom-right', 'bottom-left', 'top-right', 'top-left'
    color_scheme = Column(String(20), default="#25D366")  # WhatsApp green by default
    icon_type = Column(String(50), default="whatsapp")
    pre_filled_message = Column(String(500), default="")
    is_enabled = Column(Boolean, default=True)
    custom_css = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())