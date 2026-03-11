"""
Authentication Schemas for WhatsApp RAG Assistant
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class BusinessCreate(BaseModel):
    name: str
    email: str
    password: str


class BusinessResponse(BaseModel):
    business_id: str
    name: str
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None