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

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # PSX settings
    psx_dps_base_url: str = "https://dps.psx.com.pk"
    psx_cache_ttl_live: int = 60        # seconds — during market hours
    psx_cache_ttl_closed: int = 900     # seconds — after hours

    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/1"   # separate DB from cache
    celery_result_backend: str = "redis://localhost:6379/2"

    # Alert engine settings
    alert_cooldown_minutes: int = 60    # minimum gap between repeated non-one-shot alerts
    alert_check_interval: int = 60      # seconds between alert checker runs
    wa_send_delay_ms: int = 100         # delay between bulk WhatsApp sends (ms)

    class Config:
        env_file = ".env"


settings = Settings()