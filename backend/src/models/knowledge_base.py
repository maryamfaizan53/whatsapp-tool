"""
Knowledge Base Model for WhatsApp RAG Assistant
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    kb_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.business_id"), nullable=False)
    name = Column(String(255), nullable=False)  # Knowledge base name
    description = Column(Text, nullable=True)  # Optional description
    source_type = Column(String(20), nullable=False)  # 'website', 'documents', 'manual'
    source_url = Column(String(500), nullable=True)  # URL if website crawling
    vector_index_name = Column(String(255), nullable=True)  # Name of vector DB index
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)
    document_count = Column(Integer, default=0)  # Number of documents
    status = Column(String(20), default="active")  # 'active', 'indexing', 'error'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())