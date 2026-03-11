"""initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-03-12

Creates the complete database schema in dependency order:

  Original RAG-chatbot tables:
    businesses → knowledge_bases → documents
    businesses → conversations → messages
    businesses → widget_configurations

  PSX investor / market tables:
    stocks
    market_quote_cache
    market_index_cache
    investors → watchlists
    investors → holdings
    investors → alerts → notification_logs
                         ↑
                   investors (also FK)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # businesses
    # ----------------------------------------------------------------
    op.create_table(
        "businesses",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("whatsapp_phone_number_id", sa.String(255), nullable=True),
        sa.Column("whatsapp_access_token", sa.Text, nullable=True),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("subscription_tier", sa.String(50), server_default="free"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ----------------------------------------------------------------
    # knowledge_bases
    # ----------------------------------------------------------------
    op.create_table(
        "knowledge_bases",
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.business_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("vector_index_name", sa.String(255), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_knowledge_bases_business_id", "knowledge_bases", ["business_id"])

    # ----------------------------------------------------------------
    # documents
    # ----------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("doc_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "kb_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_bases.kb_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("content_hash", sa.String(255), nullable=True),
        sa.Column("indexed_chunks", sa.Integer, server_default="0"),
        sa.Column(
            "upload_date",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("status", sa.String(20), server_default="uploaded"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_documents_kb_id", "documents", ["kb_id"])

    # ----------------------------------------------------------------
    # conversations
    # ----------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("conv_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.business_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("customer_whatsapp_id", sa.String(255), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("language_code", sa.String(10), server_default="en"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_conversations_business_id", "conversations", ["business_id"])

    # ----------------------------------------------------------------
    # messages
    # ----------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column("msg_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conv_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.conv_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("media_url", sa.String(500), nullable=True),
        sa.Column("message_type", sa.String(20), server_default="text"),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("processed_by_rag", sa.Boolean, server_default=sa.text("false")),
        sa.Column("confidence_score", sa.Float, server_default="0.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_messages_conv_id", "messages", ["conv_id"])

    # ----------------------------------------------------------------
    # widget_configurations
    # ----------------------------------------------------------------
    op.create_table(
        "widget_configurations",
        sa.Column("widget_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.business_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.String(20), server_default="bottom-right"),
        sa.Column("color_scheme", sa.String(20), server_default="#25D366"),
        sa.Column("icon_type", sa.String(50), server_default="whatsapp"),
        sa.Column("pre_filled_message", sa.String(500), server_default=""),
        sa.Column("is_enabled", sa.Boolean, server_default=sa.text("true")),
        sa.Column("custom_css", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ================================================================
    # PSX market data tables
    # ================================================================

    # ----------------------------------------------------------------
    # stocks  (master symbol list)
    # ----------------------------------------------------------------
    op.create_table(
        "stocks",
        sa.Column("symbol", sa.String(20), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("listing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ----------------------------------------------------------------
    # market_quote_cache
    # ----------------------------------------------------------------
    op.create_table(
        "market_quote_cache",
        sa.Column("symbol", sa.String(20), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("current_price", sa.Float, nullable=False),
        sa.Column("open_price", sa.Float, nullable=True),
        sa.Column("high_price", sa.Float, nullable=True),
        sa.Column("low_price", sa.Float, nullable=True),
        sa.Column("prev_close", sa.Float, nullable=True),
        sa.Column("change", sa.Float, nullable=True),
        sa.Column("change_pct", sa.Float, nullable=True),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column("market_cap", sa.Float, nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ----------------------------------------------------------------
    # market_index_cache
    # ----------------------------------------------------------------
    op.create_table(
        "market_index_cache",
        sa.Column("index_name", sa.String(50), primary_key=True),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("change", sa.Float, nullable=True),
        sa.Column("change_pct", sa.Float, nullable=True),
        sa.Column("volume", sa.BigInteger, nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ================================================================
    # PSX investor tables
    # ================================================================

    # ----------------------------------------------------------------
    # investors
    # ----------------------------------------------------------------
    op.create_table(
        "investors",
        sa.Column("investor_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "whatsapp_number", sa.String(20), nullable=False, unique=True
        ),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("preferred_language", sa.String(20), server_default="en"),
        sa.Column(
            "notifications_enabled", sa.Boolean, server_default=sa.text("true")
        ),
        sa.Column(
            "morning_brief_enabled", sa.Boolean, server_default=sa.text("false")
        ),
        sa.Column("morning_brief_time", sa.String(5), server_default="09:15"),
        sa.Column("onboarding_step", sa.String(50), server_default="new"),
        sa.Column(
            "is_onboarded", sa.Boolean, server_default=sa.text("false")
        ),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_investors_whatsapp_number", "investors", ["whatsapp_number"], unique=True
    )

    # ----------------------------------------------------------------
    # watchlists
    # ----------------------------------------------------------------
    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.investor_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "investor_id", "symbol", name="uq_watchlist_investor_symbol"
        ),
    )
    op.create_index("ix_watchlists_investor_id", "watchlists", ["investor_id"])

    # ----------------------------------------------------------------
    # holdings
    # ----------------------------------------------------------------
    op.create_table(
        "holdings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.investor_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("avg_buy_price", sa.Float, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "investor_id", "symbol", name="uq_holding_investor_symbol"
        ),
    )
    op.create_index("ix_holdings_investor_id", "holdings", ["investor_id"])

    # ----------------------------------------------------------------
    # alerts
    # ----------------------------------------------------------------
    op.create_table(
        "alerts",
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.investor_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("condition", sa.String(30), nullable=False),
        sa.Column("target_value", sa.Float, nullable=False),
        sa.Column("one_shot", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("trigger_count", sa.Integer, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_alerts_investor_id", "alerts", ["investor_id"])
    op.create_index("ix_alerts_symbol", "alerts", ["symbol"])
    op.create_index("ix_alerts_is_active", "alerts", ["is_active"])

    # ----------------------------------------------------------------
    # notification_logs
    # ----------------------------------------------------------------
    op.create_table(
        "notification_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.investor_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alerts.alert_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notification_type", sa.String(30), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("wa_message_id", sa.String(255), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_notification_logs_investor_id", "notification_logs", ["investor_id"]
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("notification_logs")
    op.drop_table("alerts")
    op.drop_table("holdings")
    op.drop_table("watchlists")
    op.drop_table("investors")
    op.drop_table("market_index_cache")
    op.drop_table("market_quote_cache")
    op.drop_table("stocks")
    op.drop_table("widget_configurations")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("documents")
    op.drop_table("knowledge_bases")
    op.drop_table("businesses")
