"""Community Q&A routes for civil and architectural engineering discussions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AuthenticatedUser, get_optional_current_user
from app.models.community import (
    CommunityAnswerRecord,
    CommunityQuestionDetailResponse,
    CommunityQuestionListResponse,
    CommunityQuestionRecord,
    CommunitySort,
    CommunityVoteRequest,
    CreateCommunityAnswerRequest,
    CreateCommunityQuestionRequest,
)
from app.services.community_storage import (
    add_answer,
    create_question,
    get_question,
    list_questions,
    vote_answer,
    vote_question,
)

router = APIRouter(prefix="/community", tags=["community"])


def _resolve_author(
    *,
    requested_name: str | None,
    current_user: AuthenticatedUser | None,
) -> tuple[str | None, str]:
    if current_user is not None:
        return current_user.id, current_user.name

    cleaned = " ".join((requested_name or "").strip().split())
    if not cleaned:
        raise HTTPException(status_code=400, detail="author_name is required")
    return None, cleaned


@router.get("/questions", response_model=CommunityQuestionListResponse)
def community_list_questions(
    query: str | None = Query(default=None, max_length=200),
    tag: str | None = Query(default=None, max_length=32),
    discipline: str | None = Query(default=None, max_length=32),
    sort: CommunitySort = Query(default="active"),
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        questions = list_questions(
            query=query,
            tag=tag,
            discipline=discipline,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CommunityQuestionListResponse(
        questions=[CommunityQuestionRecord(**item) for item in questions]
    )


@router.post(
    "/questions",
    response_model=CommunityQuestionRecord,
    status_code=status.HTTP_201_CREATED,
)
def community_create_question(
    request: CreateCommunityQuestionRequest,
    current_user: AuthenticatedUser | None = Depends(get_optional_current_user),
):
    author_id, author_name = _resolve_author(
        requested_name=request.author_name,
        current_user=current_user,
    )
    try:
        question = create_question(
            title=request.title,
            body=request.body,
            tags=request.tags,
            discipline=request.discipline,
            author_id=author_id,
            author_name=author_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CommunityQuestionRecord(**question)


@router.get("/questions/{question_id}", response_model=CommunityQuestionDetailResponse)
def community_question_detail(question_id: str):
    detail = get_question(question_id=question_id, increment_views=True)
    if detail is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return CommunityQuestionDetailResponse(
        question=CommunityQuestionRecord(**detail["question"]),
        answers=[CommunityAnswerRecord(**item) for item in detail["answers"]],
    )


@router.post(
    "/questions/{question_id}/answers",
    response_model=CommunityAnswerRecord,
    status_code=status.HTTP_201_CREATED,
)
def community_create_answer(
    question_id: str,
    request: CreateCommunityAnswerRequest,
    current_user: AuthenticatedUser | None = Depends(get_optional_current_user),
):
    author_id, author_name = _resolve_author(
        requested_name=request.author_name,
        current_user=current_user,
    )
    try:
        answer = add_answer(
            question_id=question_id,
            body=request.body,
            author_id=author_id,
            author_name=author_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if answer is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return CommunityAnswerRecord(**answer)


@router.post("/questions/{question_id}/vote", response_model=CommunityQuestionRecord)
def community_vote_question(question_id: str, request: CommunityVoteRequest):
    question = vote_question(question_id=question_id, direction=request.direction)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return CommunityQuestionRecord(**question)


@router.post("/answers/{answer_id}/vote", response_model=CommunityAnswerRecord)
def community_vote_answer(answer_id: str, request: CommunityVoteRequest):
    answer = vote_answer(answer_id=answer_id, direction=request.direction)
    if answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return CommunityAnswerRecord(**answer)
