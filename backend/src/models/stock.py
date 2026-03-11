"""
Stock and Market Data Models for PSX (Pakistan Stock Exchange)
"""
from sqlalchemy import Column, String, Float, BigInteger, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..db.base import Base


class Stock(Base):
    """Master list of all PSX-listed companies."""
    __tablename__ = "stocks"

    symbol = Column(String(20), primary_key=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True)
    listing_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class MarketQuoteCache(Base):
    """
    Last-known quote for each symbol, refreshed by the PSX service.
    Acts as a DB-level cache that survives Redis restarts.
    """
    __tablename__ = "market_quote_cache"

    symbol = Column(String(20), primary_key=True)
    company_name = Column(String(255), nullable=True)
    current_price = Column(Float, nullable=False)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    prev_close = Column(Float, nullable=True)
    change = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    market_cap = Column(Float, nullable=True)
    source = Column(String(50), nullable=True)   # "psx" | "yfinance"
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MarketIndexCache(Base):
    """Last-known value for KSE-100, KSE-30, KMI-30."""
    __tablename__ = "market_index_cache"

    index_name = Column(String(50), primary_key=True)   # e.g. "KSE-100"
    value = Column(Float, nullable=False)
    change = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
