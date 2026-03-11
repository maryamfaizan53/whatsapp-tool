"""
Root conftest — sets required env vars BEFORE any src module is imported,
so Pydantic Settings doesn't raise on missing required fields.
"""
import os
import sys
from pathlib import Path

# Make `src` importable from the `backend/` root
sys.path.insert(0, str(Path(__file__).parent))

# Dummy values for all required Settings fields
_DEFAULTS = {
    "SECRET_KEY": "test-secret-key-32-chars-minimum!!",
    "DATABASE_URL": "sqlite:///./test.db",
    "WHATSAPP_ACCESS_TOKEN": "test-wa-token",
    "WHATSAPP_PHONE_NUMBER_ID": "123456789",
    "WHATSAPP_VERIFY_TOKEN": "test-verify-token",
    "PINECONE_API_KEY": "test-pinecone-key",
    "OPENAI_API_KEY": "test-openai-key",
    "WHISPER_API_KEY": "test-whisper-key",
    "ENCRYPTION_KEY": "test-encryption-key",
    "REDIS_URL": "redis://localhost:6379/0",
}

for key, value in _DEFAULTS.items():
    os.environ.setdefault(key, value)
