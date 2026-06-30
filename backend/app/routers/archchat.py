from __future__ import annotations

from datetime import datetime, timezone
import re
import time
from typing import Any, AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, and_, desc, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthenticatedUser, get_current_user
from app.models.archchat import (
    ArchChatMessageRecord,
    ArchChatThreadRecord,
    CreateThreadResponse,
    EngineeringFindings,
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


_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_GREETING_RE = re.compile(
    r"^(?:hello|hi|hey|good\s+(?:morning|afternoon|evening)|salaam|salam|"
    r"السلام\s+عليكم(?:\s+ورحمة\s+الله(?:\s+وبركاته)?)?|وعليكم\s+السلام|سلام|مرحبا|مرحباً|"
    r"اهلا|أهلا|أهلًا|هاي|هلا|صباح\s+الخير|مساء\s+الخير)"
    r"(?:[\s!,.?؟،]+(?:there|cadarena|how\s+are\s+you|كيف\s+حالك|اخبارك|"
    r"عامل\s+ايه|يا\s+كاد\s*ارينا|عليكم\s+السلام))*[\s!,.?؟،]*$",
    re.IGNORECASE,
)


def _is_greeting(content: str) -> bool:
    """Return True only for a short, standalone greeting."""
    normalized = " ".join(content.strip().split())
    return bool(normalized and len(normalized) <= 100 and _GREETING_RE.fullmatch(normalized))


def _direct_reply(content: str, has_project_files: bool) -> str | None:
    """Handle safe conversational messages before invoking the engineering RAG."""
    is_arabic = bool(_ARABIC_RE.search(content))
    if _is_greeting(content):
        if is_arabic:
            return (
                "أهلًا وسهلًا بك 👋\n\n"
                "أنا **CadArena AI**، جاهز أساعدك في تحليل ملفات مشروعك المعمارية "
                "والإنشائية.\n\n"
                "ارفع ملف المشروع عندما تكون جاهزًا، ثم اكتب سؤالك."
            )
        return (
            "Hello and welcome 👋\n\n"
            "I'm **CadArena AI**, ready to help analyze your architectural and "
            "structural project files.\n\n"
            "Upload a project file when you're ready, then ask your question."
        )

    if has_project_files:
        return None

    if is_arabic:
        return (
            "### أحتاج ملف المشروع أولًا\n\n"
            "حتى تكون الإجابة دقيقة ومبنية على بيانات مشروعك، لن أجيب عن الأسئلة "
            "الهندسية من دون ملف مرفوع.\n\n"
            "ارفع ملف **PDF أو DXF أو IFC أو XLSX/CSV أو صورة**، ثم أرسل سؤالك مرة أخرى."
        )
    return (
        "### Upload a project file first\n\n"
        "To keep the answer accurate and grounded in your project, I can't answer "
        "engineering questions without an uploaded source.\n\n"
        "Upload a **PDF, DXF, IFC, XLSX/CSV, or image**, then send your question again."
    )


def _to_iso(dt: Any) -> str | None:
    if dt is None:
        return None
    if not hasattr(dt, "isoformat"):
        return datetime.now(timezone.utc).isoformat()
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


async def _session_dep() -> AsyncIterator[AsyncSession]:
    try:
        async for s in get_archchat_session():
            yield s
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def _rag_base_url() -> str:
    # Keep consistent with frontend default.
    import os

    return (os.getenv("CADARENA_RAG_API_URL", "") or "http://127.0.0.1:8001").rstrip("/")


@router.get("/threads", response_model=ListThreadsResponse)
async def list_threads(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(_session_dep),
) -> ListThreadsResponse:
    stmt: Select[Any] = (
        select(ArchChatThread)
        .where(ArchChatThread.user_id == current_user.id)
        .order_by(desc(func.coalesce(ArchChatThread.last_message_at, ArchChatThread.created_at)))
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
    direct_reply = _direct_reply(content, body.has_project_files)
    if should_autotitle:
        # Lightweight replies should stay instant even when the local title model is offline.
        thread.title = content[:48].rstrip() if direct_reply is not None else await generate_thread_title(content)

    if direct_reply is not None:
        answer = direct_reply
        sources: list[dict[str, Any]] = []
        agents_used: list[str] = []
        reasoning = ""
        findings = EngineeringFindings()
    else:
        # Only project-grounded engineering questions reach the RAG service.
        filters = dict(body.filters or {})
        # Enforce project-level isolation so that queries only retrieve chunks from this project
        filters["project_id"] = thread_id

        rag_payload: dict[str, Any] = {
            "question": content,
            "top_k": body.top_k,
            "filters": filters,
            "collection": body.collection,
        }
        if body.llm_provider:
            rag_payload["llm_provider"] = body.llm_provider
        if body.llm_model:
            rag_payload["llm_model"] = body.llm_model
        rag_url = f"{_rag_base_url()}/rag/chat"

        rag_start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                rag_resp = await client.post(rag_url, json=rag_payload)
                rag_resp.raise_for_status()
                rag_data = rag_resp.json()
        except Exception as exc:
            rag_latency = (time.perf_counter() - rag_start) * 1000
            logger.error(f"RAG agent pipeline failed after {rag_latency:.2f}ms: {exc}")
            # Fall back to the simpler retrieval query when the agent pipeline is unavailable.
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    rag_resp = await client.post(f"{_rag_base_url()}/rag/query", json=rag_payload)
                    rag_resp.raise_for_status()
                    rag_data = rag_resp.json()
            except Exception as fallback_exc:
                logger.error(f"RAG query fallback failed after {rag_latency:.2f}ms: {fallback_exc}")
                error_msg = ArchChatMessage(thread_id=thread_id, role="error", content="RAG request failed.")
                session.add(error_msg)
                thread.last_message_at = func.now()  # type: ignore[assignment]
                await session.commit()
                raise HTTPException(status_code=502, detail="RAG service request failed") from fallback_exc

        rag_latency = (time.perf_counter() - rag_start) * 1000
        logger.info(f"RAG request completed in {rag_latency:.2f}ms")

        answer = str((rag_data or {}).get("answer") or "").strip() or "No answer returned."
        sources = (rag_data or {}).get("sources") or []
        agents_used = (rag_data or {}).get("agents_used") or []
        reasoning = str((rag_data or {}).get("reasoning") or "").strip()
        raw_findings = (rag_data or {}).get("findings") or {}
        findings = EngineeringFindings(
            key_points=list(raw_findings.get("key_points") or []),
            warnings=list(raw_findings.get("warnings") or []),
            recommendations=list(raw_findings.get("recommendations") or []),
        )

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
        agents_used=agents_used,
        reasoning=reasoning,
        findings=findings,
    )
