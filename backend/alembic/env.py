"""
Alembic environment configuration for the PSX WhatsApp Bot.

- Reads DATABASE_URL from src.config.settings (no credentials in alembic.ini).
- Imports every model module so SQLAlchemy registers all tables with Base.metadata
  before autogenerate compares against the live schema.
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Make `src` importable when running `alembic` from the backend/ directory
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# Set required env vars for Settings before importing src modules
# (keeps alembic runnable without a full .env present)
# ---------------------------------------------------------------------------
_REQUIRED_DEFAULTS = {
    "SECRET_KEY": "alembic-placeholder-key",
    "WHATSAPP_ACCESS_TOKEN": "placeholder",
    "WHATSAPP_PHONE_NUMBER_ID": "placeholder",
    "WHATSAPP_VERIFY_TOKEN": "placeholder",
    "PINECONE_API_KEY": "placeholder",
    "OPENAI_API_KEY": "placeholder",
    "WHISPER_API_KEY": "placeholder",
    "ENCRYPTION_KEY": "placeholder",
}
for _k, _v in _REQUIRED_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

# ---------------------------------------------------------------------------
# Import Base and ALL model modules (registers tables with Base.metadata)
# ---------------------------------------------------------------------------
from src.db.base import Base                    # noqa: E402

# Original RAG-chatbot models
from src.models.business import Business                         # noqa: F401,E402
from src.models.conversation import Conversation                 # noqa: F401,E402
from src.models.document import Document                         # noqa: F401,E402
from src.models.knowledge_base import KnowledgeBase              # noqa: F401,E402
from src.models.message import Message                           # noqa: F401,E402
from src.models.widget_config import WidgetConfiguration         # noqa: F401,E402

# PSX investor / market models
from src.models.stock import MarketIndexCache, MarketQuoteCache, Stock  # noqa: F401,E402
from src.models.investor import (                                # noqa: F401,E402
    Alert, Holding, Investor, NotificationLog, Watchlist,
)

from src.config import settings                 # noqa: E402

# ---------------------------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------------------------
config = context.config

# Point Alembic at the application DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (emit SQL to stdout/file).
    Useful for generating SQL scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (connect and apply directly).
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
