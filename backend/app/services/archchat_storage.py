"""
ArchChat Postgres storage (threads + messages).

This is intentionally isolated from the existing SQLite workspace DB so the
main backend can keep its current persistence while ArchChat can scale on
Postgres for production.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, AsyncIterator
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def archchat_database_url() -> str:
    """
    Unified Postgres DB URL for backend persistence.
    """
    unified = os.getenv("CADARENA_DATABASE_URL", "").strip()
    if unified:
        return unified
    return os.getenv("CADARENA_ARCHCHAT_DATABASE_URL", "").strip()


def _to_async_database_url(url: str) -> str:
    """
    Normalize DB URL for SQLAlchemy AsyncEngine.
    Accepts sync-style URLs from backend env and rewrites to asyncpg.
    """
    normalized = (url or "").strip()
    if normalized.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + normalized[len("postgresql+psycopg2://") :]
    if normalized.startswith("postgresql://"):
        return "postgresql+asyncpg://" + normalized[len("postgresql://") :]
    return normalized


@dataclass(frozen=True)
class ArchChatStore:
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]


_STORE: ArchChatStore | None = None


class Base(DeclarativeBase):
    pass


class ArchChatThread(Base):
    __tablename__ = "archchat_threads"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list["ArchChatMessage"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ArchChatMessage(Base):
    __tablename__ = "archchat_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    thread_id: Mapped[str] = mapped_column(String(32), ForeignKey("archchat_threads.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user|assistant|system|error
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    rag_sources: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON, nullable=True)

    thread: Mapped[ArchChatThread] = relationship(back_populates="messages")


Index("idx_archchat_threads_user_last", ArchChatThread.user_id, ArchChatThread.last_message_at)
Index("idx_archchat_messages_thread_created", ArchChatMessage.thread_id, ArchChatMessage.created_at)


async def init_archchat_store() -> None:
    """
    Initialize the Postgres engine and create tables (best-effort).

    If CADARENA_ARCHCHAT_DATABASE_URL is not set, the store stays disabled.
    """
    global _STORE
    if _STORE is not None:
        return

    url = archchat_database_url()
    if not url:
        logger.warning("ArchChat DB disabled: CADARENA_ARCHCHAT_DATABASE_URL is not set.")
        return

    engine = create_async_engine(_to_async_database_url(url), pool_pre_ping=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    _STORE = ArchChatStore(engine=engine, sessionmaker=sessionmaker)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def is_archchat_store_enabled() -> bool:
    return _STORE is not None


async def get_archchat_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that yields an AsyncSession.
    Raises a runtime error when store is disabled so routers can map it to 503.
    """
    if _STORE is None:
        raise RuntimeError("ArchChat database is not configured.")
    async with _STORE.sessionmaker() as session:
        yield session

