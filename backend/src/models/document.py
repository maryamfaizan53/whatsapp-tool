"""
Document Model for WhatsApp RAG Assistant
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kb_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.kb_id"), nullable=False)
    filename = Column(String(255), nullable=False)  # Original filename
    source_url = Column(String(500), nullable=True)  # URL if crawled from website
    content_hash = Column(String(255), nullable=True)  # To detect changes
    indexed_chunks = Column(Integer, default=0)  # Number of indexed chunks
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="uploaded")  # 'uploaded', 'processing', 'indexed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())