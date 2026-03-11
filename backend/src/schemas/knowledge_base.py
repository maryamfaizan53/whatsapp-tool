"""
Knowledge Base Schemas for WhatsApp RAG Assistant
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str  # 'website', 'documents', 'manual'
    source_url: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    kb_id: str
    name: str
    description: Optional[str]
    source_type: str
    source_url: Optional[str]
    document_count: int
    status: str

    class Config:
        from_attributes = True