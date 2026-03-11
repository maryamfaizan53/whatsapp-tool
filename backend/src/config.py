"""
Configuration Settings for WhatsApp RAG Assistant
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # App settings
    app_name: str = "WhatsApp RAG Assistant API"
    debug: bool = False
    secret_key: str  # Should be set in environment

    # Database settings
    database_url: str

    # WhatsApp API settings
    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str

    # Vector database settings
    pinecone_api_key: str
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # LLM settings
    openai_api_key: str
    llm_model: str = "gpt-4-turbo"

    # Whisper settings for STT
    whisper_api_key: str

    # CORS settings
    allowed_origins: List[str] = ["*"]

    # Encryption settings
    encryption_key: str

    # Webhook settings
    webhook_secret: str = ""
    webhook_signature_verification: bool = False
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()