from __future__ import annotations

from datetime import datetime
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, and_, desc, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthenticatedUser, get_current_user
from app.models.archchat import (
    ArchChatMessageRecord,
    ArchChatThreadRecord,
    CreateThreadResponse,
    ListThreadsResponse,
    RenameThreadRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.archchat_storage import (
    ArchChatMessage,
    ArchChatThread,
    get_archchat_session,
    is_archchat_store_enabled,
)
from app.core.logging import get_logger
from app.services.archchat_title import generate_thread_title

logger = get_logger(__name__)
router = APIRouter(prefix="/archchat", tags=["archchat"])


def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def _thread_record(thread: ArchChatThread) -> ArchChatThreadRecord:
    return ArchChatThreadRecord(
        id=thread.id,
        title=thread.title,
        created_at=_to_iso(thread.created_at) or "",
        updated_at=_to_iso(thread.updated_at) or "",
        last_message_at=_to_iso(thread.last_message_at),
    )


def _message_record(msg: ArchChatMessage) -> ArchChatMessageRecord:
    return ArchChatMessageRecord(
        id=msg.id,
        role=msg.role,  # type: ignore[arg-type]
        content=msg.content,
        created_at=_to_iso(msg.created_at) or "",
        rag_sources=msg.rag_sources,
    )


async def _session_dep() -> AsyncSession:
    try:
        async for s in get_archchat_session():
            return s
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ArchChat store unavailable")


def _rag_base_url() -> str:
    # Keep consistent with frontend default.
    import os

    return (os.getenv("CADARENA_RAG_API_URL", "") or "http://localhost:8001").rstrip("/")


@router.get("/threads", response_model=ListThreadsResponse)
async def list_threads(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> ListThreadsResponse:
    stmt: Select[Any] = (
        select(ArchChatThread)
        .where(ArchChatThread.user_id == current_user.id)
        .order_by(desc(func.coalesce(ArchChatThread.last_message_at, ArchChatThread.updated_at)))
        .limit(200)
    )
    threads = (await session.execute(stmt)).scalars().all()
    return ListThreadsResponse(threads=[_thread_record(t) for t in threads])


@router.post("/threads", response_model=CreateThreadResponse, status_code=201)
async def create_thread(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> CreateThreadResponse:
    thread = ArchChatThread(user_id=current_user.id, title="New chat")
    session.add(thread)
    await session.commit()
    await session.refresh(thread)
    return CreateThreadResponse(thread=_thread_record(thread))


@router.patch("/threads/{thread_id}", response_model=ArchChatThreadRecord)
async def rename_thread(
    thread_id: str,
    body: RenameThreadRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> ArchChatThreadRecord:
    title = body.title.strip()
    # Use database-side "now" to keep ordering stable.
    stmt = (
        update(ArchChatThread)
        .where(and_(ArchChatThread.id == thread_id, ArchChatThread.user_id == current_user.id))
        .values(title=title, updated_at=func.now())
        .returning(ArchChatThread)
    )
    result = await session.execute(stmt)
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    await session.commit()
    return _thread_record(thread)


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> dict[str, bool]:
    stmt = delete(ArchChatThread).where(
        and_(ArchChatThread.id == thread_id, ArchChatThread.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    await session.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"success": True}


@router.get("/threads/{thread_id}/messages", response_model=list[ArchChatMessageRecord])
async def list_messages(
    thread_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> list[ArchChatMessageRecord]:
    # Ensure ownership.
    thread = (
        await session.execute(
            select(ArchChatThread).where(
                and_(ArchChatThread.id == thread_id, ArchChatThread.user_id == current_user.id)
            )
        )
    ).scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    msgs = (
        await session.execute(
            select(ArchChatMessage)
            .where(ArchChatMessage.thread_id == thread_id)
            .order_by(ArchChatMessage.created_at.asc())
        )
    ).scalars().all()
    return [_message_record(m) for m in msgs]


@router.post("/threads/{thread_id}/messages", response_model=SendMessageResponse)
async def send_message(
    thread_id: str,
    body: SendMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> SendMessageResponse:
    # Ensure ownership.
    thread = (
        await session.execute(
            select(ArchChatThread).where(
                and_(ArchChatThread.id == thread_id, ArchChatThread.user_id == current_user.id)
            )
        )
    ).scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content must not be empty")

    # Persist user message.
    user_msg = ArchChatMessage(thread_id=thread_id, role="user", content=content)
    session.add(user_msg)

    # Auto-title if still default and this is first user message.
    existing_user_count = (
        await session.execute(
            select(func.count(ArchChatMessage.id)).where(
                and_(ArchChatMessage.thread_id == thread_id, ArchChatMessage.role == "user")
            )
        )
    ).scalar_one()
    should_autotitle = (existing_user_count == 0) and (thread.title.strip().lower() in {"new chat", ""})
    if should_autotitle:
        thread.title = await generate_thread_title(content)

    # Call RAG service.
    rag_payload: dict[str, Any] = {
        "question": content,
        "top_k": body.top_k,
        "filters": body.filters or {},
        "collection": body.collection,
    }
    if body.llm_provider:
        rag_payload["llm_provider"] = body.llm_provider
    if body.llm_model:
        rag_payload["llm_model"] = body.llm_model
    rag_url = f"{_rag_base_url()}/rag/query"
    
    rag_start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            rag_resp = await client.post(rag_url, json=rag_payload)
            rag_resp.raise_for_status()
            rag_data = rag_resp.json()
    except Exception as exc:
        rag_latency = (time.perf_counter() - rag_start) * 1000
        logger.error(f"RAG request failed after {rag_latency:.2f}ms: {exc}")
        # Persist error message to history.
        error_msg = ArchChatMessage(thread_id=thread_id, role="error", content="RAG request failed.")
        session.add(error_msg)
        thread.last_message_at = func.now()  # type: ignore[assignment]
        await session.commit()
        raise HTTPException(status_code=502, detail="RAG service request failed") from exc

    rag_latency = (time.perf_counter() - rag_start) * 1000
    logger.info(f"RAG request completed in {rag_latency:.2f}ms")

    answer = str((rag_data or {}).get("answer") or "").strip() or "No answer returned."
    sources = (rag_data or {}).get("sources") or []

    assistant_msg = ArchChatMessage(
        thread_id=thread_id,
        role="assistant",
        content=answer,
        rag_sources=sources,
    )
    session.add(assistant_msg)

    # Update thread timestamps.
    thread.last_message_at = func.now()  # type: ignore[assignment]
    thread.updated_at = func.now()  # type: ignore[assignment]

    await session.commit()
    await session.refresh(thread)
    await session.refresh(user_msg)
    await session.refresh(assistant_msg)

    return SendMessageResponse(
        user_message=_message_record(user_msg),
        assistant_message=_message_record(assistant_msg),
        sources=sources,
        thread=_thread_record(thread),
    )

