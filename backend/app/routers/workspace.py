"""Workspace router for user projects and persisted chat messages."""

from __future__ import annotations

import re
from datetime import datetime, UTC
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.design_parser import ParseDesignErrorResponse, ParseErrorBody
from app.models.workspace import (
    CreateProjectRequest,
    ProjectListResponse,
    ProjectMessagesResponse,
    ProjectRecord,
    RenameProjectRequest,
    WorkspaceGenerateDxfRequest,
    WorkspaceGenerateDxfSuccessResponse,
)
from app.pipeline.intent_to_agent import generate_dxf_from_intent
from app.schemas.design_intent import DesignIntent
from app.services.design_parser.config import OLLAMA_MODEL_ID  # MODEL-FIX: preserve the configured Ollama default when the caller does not supply a local model override
from app.services.design_parser_service import (
    ParseDesignServiceError,
    parse_design_prompt_with_metadata,
)
from app.services.file_token_registry import bind_workspace_guest_cookie, issue_workspace_file_token
from app.services.workspace_storage import (
    add_message,
    create_project,
    delete_project,
    get_project,
    list_project_messages,
    list_projects,
    rename_project,
)
from app.utils.parse_output_storage import save_parse_design_output

logger = get_logger(__name__)
router = APIRouter()
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_LAYOUT_RETRY_CODES = {
    "LAYOUT_PLANNING_FAILED",
    "LAYOUT_VALIDATION_FAILED",
    "INVALID_STRUCTURED_OUTPUT",
}
_LAYOUT_RETRY_MARKER = "Feasibility override for deterministic planner"
_LAYOUT_RETRY_SUFFIX_SOFT = (
    "\n\n"
    "Feasibility override for deterministic planner:\n"
    "- If constraints conflict, prioritize a feasible layout.\n"
    "- Keep all rooms inside the boundary and avoid overlap.\n"
    "- You may relax adjacency wishes and slightly adjust room preferred areas.\n"
    "- Keep the program practical and generate valid geometry."
)
_LAYOUT_RETRY_SUFFIX_HARD = (
    "\n\n"
    "Emergency fallback mode for deterministic planner:\n"
    "- Produce any valid and buildable residential layout that fits the boundary.\n"
    "- Prioritize non-overlap, in-boundary rooms, and geometric validity over strict constraints.\n"
    "- Keep room program intent but you may simplify area targets and adjacency wishes if needed.\n"
    "- Ensure output can be converted to DXF intent without invalid geometry."
)


def _slugify(value: str) -> str:
    slug = _NON_ALNUM_RE.sub("_", value.strip().lower()).strip("_")
    return slug or "project"


def _project_dxf_name(project_name: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{_slugify(project_name)}_{timestamp}.dxf"


def _build_relaxed_prompt(prompt: str, *, hard_mode: bool = False) -> str:
    if _LAYOUT_RETRY_MARKER in prompt:
        return prompt
    suffix = _LAYOUT_RETRY_SUFFIX_HARD if hard_mode else _LAYOUT_RETRY_SUFFIX_SOFT
    return f"{prompt.rstrip()}{suffix}"


def _should_retry_layout(exc: ParseDesignServiceError) -> bool:
    return exc.code in _LAYOUT_RETRY_CODES and 400 <= exc.status_code < 500


async def _parse_with_layout_retry(
    *,
    prompt: str,
    model_choice,
    model_id: str | None,
    recovery_mode,
    request_id: str,
):
    accumulated_details: list[str] = []

    try:
        # Forward the concrete cloud model id through the primary parse attempt.
        result = await parse_design_prompt_with_metadata(
            prompt=prompt,
            model_choice=model_choice,
            model_id=model_id,
            recovery_mode=recovery_mode,
            request_id=request_id,
        )
        return result, prompt, False, False
    except ParseDesignServiceError as first_exc:
        accumulated_details.extend(first_exc.details)
        if not _should_retry_layout(first_exc):
            raise first_exc

        soft_retry_prompt = _build_relaxed_prompt(prompt, hard_mode=False)
        soft_retry_request_id = f"{request_id}_layout_retry_soft"
        logger.warning(
            "request_id=%s event=workspace-layout-retry-soft code=%s reason=%s",
            request_id,
            first_exc.code,
            first_exc.message,
        )
        try:
            # Reuse the same provider/model selection when the relaxed prompt retry runs.
            soft_retry_result = await parse_design_prompt_with_metadata(
                prompt=soft_retry_prompt,
                model_choice=model_choice,
                model_id=model_id,
                recovery_mode=recovery_mode,
                request_id=soft_retry_request_id,
            )
            return soft_retry_result, soft_retry_prompt, True, False
        except ParseDesignServiceError as soft_retry_exc:
            accumulated_details.extend(soft_retry_exc.details)
            if not _should_retry_layout(soft_retry_exc):
                soft_retry_exc.details = accumulated_details
                raise soft_retry_exc from soft_retry_exc

            hard_retry_prompt = _build_relaxed_prompt(prompt, hard_mode=True)
            hard_retry_request_id = f"{request_id}_layout_retry_hard"
            logger.warning(
                "request_id=%s event=workspace-layout-retry-hard code=%s reason=%s",
                request_id,
                soft_retry_exc.code,
                soft_retry_exc.message,
            )
            try:
                # Reuse the same provider/model selection when the emergency retry runs.
                hard_retry_result = await parse_design_prompt_with_metadata(
                    prompt=hard_retry_prompt,
                    model_choice=model_choice,
                    model_id=model_id,
                    recovery_mode=recovery_mode,
                    request_id=hard_retry_request_id,
                )
                return hard_retry_result, hard_retry_prompt, True, True
            except ParseDesignServiceError as hard_retry_exc:
                hard_retry_exc.details = accumulated_details + hard_retry_exc.details
                raise hard_retry_exc from hard_retry_exc


def _error_payload(
    *,
    status_code: int,
    model_used: str,
    provider_used: str,
    failover_triggered: bool,
    latency_ms: float,
    code: str,
    message: str,
    reason: str | None = None,
    violated_rule: str | None = None,
    room: str | None = None,
    details: list[str] | None = None,
) -> JSONResponse:
    payload = ParseDesignErrorResponse(
        success=False,
        model_used=model_used,
        provider_used=provider_used,
        failover_triggered=failover_triggered,
        latency_ms=round(latency_ms, 3),
        error=ParseErrorBody(
            code=code,
            message=message,
            reason=reason,
            violated_rule=violated_rule,
            room=room,
            details=details or [],
        ),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


@router.get("/workspace/projects", response_model=ProjectListResponse)
def workspace_list_projects(
    user_id: str = Query(..., min_length=1, max_length=128),
    response: Response = None,
):
    bind_workspace_guest_cookie(response, user_id)
    try:
        projects = list_projects(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProjectListResponse(projects=[ProjectRecord(**item) for item in projects])


@router.post("/workspace/projects", response_model=ProjectRecord, status_code=201)
def workspace_create_project(request: CreateProjectRequest, response: Response = None):
    bind_workspace_guest_cookie(response, request.user_id)
    try:
        project = create_project(user_id=request.user_id, name=request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProjectRecord(**project)


@router.patch("/workspace/projects/{project_id}", response_model=ProjectRecord)
def workspace_rename_project(project_id: str, request: RenameProjectRequest, response: Response = None):
    bind_workspace_guest_cookie(response, request.user_id)
    try:
        project = rename_project(user_id=request.user_id, project_id=project_id, name=request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRecord(**project)


@router.delete("/workspace/projects/{project_id}")
def workspace_delete_project(
    project_id: str,
    user_id: str = Query(..., min_length=1, max_length=128),
    response: Response = None,
):
    bind_workspace_guest_cookie(response, user_id)
    try:
        deleted = delete_project(user_id=user_id, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}


@router.get("/workspace/projects/{project_id}/messages", response_model=ProjectMessagesResponse)
def workspace_project_messages(
    project_id: str,
    user_id: str = Query(..., min_length=1, max_length=128),
    response: Response = None,
):
    bind_workspace_guest_cookie(response, user_id)
    try:
        project, messages = list_project_messages(user_id=user_id, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectMessagesResponse(project=ProjectRecord(**project), messages=messages)


@router.post(
    "/workspace/projects/{project_id}/generate-dxf",
    response_model=WorkspaceGenerateDxfSuccessResponse,
    responses={
        400: {"model": ParseDesignErrorResponse},
        404: {"model": ParseDesignErrorResponse},
        422: {"model": ParseDesignErrorResponse},
        429: {"model": ParseDesignErrorResponse},
        500: {"model": ParseDesignErrorResponse},
        502: {"model": ParseDesignErrorResponse},
        503: {"model": ParseDesignErrorResponse},
        504: {"model": ParseDesignErrorResponse},
    },
)
async def workspace_generate_dxf(
    project_id: str,
    request: WorkspaceGenerateDxfRequest,
    response: Response = None,
):
    started_at = perf_counter()
    requested_model = request.model.value
    request_id = uuid4().hex
    bind_workspace_guest_cookie(response, request.user_id)

    project = get_project(user_id=request.user_id, project_id=project_id)
    if project is None:
        latency_ms = (perf_counter() - started_at) * 1000
        return _error_payload(
            status_code=404,
            model_used=requested_model,
            provider_used=requested_model,
            failover_triggered=False,
            latency_ms=latency_ms,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    try:
        user_message_id = add_message(
            user_id=request.user_id,
            project_id=project_id,
            role="user",
            text=request.prompt,
        )
    except ValueError as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        return _error_payload(
            status_code=400,
            model_used=requested_model,
            provider_used=requested_model,
            failover_triggered=False,
            latency_ms=latency_ms,
            code="INVALID_WORKSPACE_INPUT",
            message=str(exc),
        )
    except KeyError:
        latency_ms = (perf_counter() - started_at) * 1000
        return _error_payload(
            status_code=404,
            model_used=requested_model,
            provider_used=requested_model,
            failover_triggered=False,
            latency_ms=latency_ms,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    try:
        effective_model_id = request.model_id  # MODEL-FIX: preserve any caller-supplied model_id before provider-specific normalization
        if request.model.value == "ollama":  # MODEL-FIX: resolve local Ollama model selection at the router boundary for generate-dxf
            effective_model_id = request.model_id or OLLAMA_MODEL_ID  # MODEL-FIX: use caller-supplied model_id when provided
        result, effective_prompt, used_layout_retry, used_hard_retry = await _parse_with_layout_retry(
            prompt=request.prompt,
            model_choice=request.model,
            model_id=effective_model_id,
            recovery_mode=request.recovery_mode,
            request_id=request_id,
        )
        model_used = result.model_used
        parsed_data = result.data

        try:
            save_parse_design_output(
                prompt=effective_prompt,
                model_used=model_used,
                parsed_data=parsed_data,
                request_id=request_id,
            )
        except Exception:
            # Parse output persistence is non-critical for workspace flow.
            pass

        try:
            dxf_intent = DesignIntent.model_validate(
                {
                    "boundary": parsed_data.get("boundary", {}),
                    "rooms": parsed_data.get("rooms", []),
                    "openings": parsed_data.get("openings", []),
                }
            )
        except Exception as exc:
            raise ParseDesignServiceError(
                code="DXF_INTENT_INVALID",
                message="Parsed layout could not be converted to DXF intent",
                status_code=422,
                model_used=model_used,
                provider_used=result.provider_used,
                failover_triggered=result.failover_triggered,
                details=[str(exc)],
            ) from exc

        try:
            dxf_path = await run_in_threadpool(generate_dxf_from_intent, dxf_intent)
        except (RuntimeError, ValueError) as exc:
            raise ParseDesignServiceError(
                code="GENERATE_DXF_FAILED",
                message="DXF generation failed",
                status_code=422,
                model_used=model_used,
                provider_used=result.provider_used,
                failover_triggered=result.failover_triggered,
                details=[str(exc)],
            ) from exc

        file_token = issue_workspace_file_token(user_id=request.user_id, absolute_path=dxf_path)
        dxf_name = _project_dxf_name(project["name"])
        assistant_text = (
            f"DXF generated successfully using {model_used}."
            if not used_layout_retry
            else (
                f"DXF generated successfully using {model_used} (recovered with feasibility fallback)."
                if not used_hard_retry
                else f"DXF generated successfully using {model_used} (recovered with emergency fallback)."
            )
        )
        assistant_message_id = add_message(
            user_id=request.user_id,
            project_id=project_id,
            role="assistant",
            text=assistant_text,
            dxf_path=str(dxf_path),
            dxf_name=dxf_name,
            model_used=model_used,
            provider_used=result.provider_used,
        )

        latency_ms = (perf_counter() - started_at) * 1000
        success_payload = WorkspaceGenerateDxfSuccessResponse(
            success=True,
            project_id=project_id,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            model_used=model_used,
            provider_used=result.provider_used,
            failover_triggered=result.failover_triggered,
            self_review_triggered=result.self_review_triggered,
            latency_ms=round(latency_ms, 3),
            file_token=file_token,
            dxf_name=dxf_name,
            data=parsed_data,
            metrics=result.metrics,
        )
        # ITERATIVE-FIX: include the parsed layout at the top level so generate responses can seed iterative edits.
        response_payload = success_payload.model_dump(mode="json")
        # ITERATIVE-FIX: expose only the persisted layout fields the frontend needs for iterative mode activation.
        response_payload["layout"] = {
            "boundary": parsed_data.get("boundary", {}),
            "rooms": parsed_data.get("rooms", []),
            "openings": parsed_data.get("openings", []),
        }
        return JSONResponse(content=response_payload)

    except ParseDesignServiceError as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        detail_line = ""
        if exc.details:
            compact_details = [detail for detail in dict.fromkeys(exc.details) if detail]
            if compact_details:
                detail_preview = " | ".join(compact_details[:3])
                if len(compact_details) > 3:
                    detail_preview = f"{detail_preview} | ...(+{len(compact_details) - 3} more)"
                detail_line = f" | {detail_preview}"
        try:
            add_message(
                user_id=request.user_id,
                project_id=project_id,
                role="error",
                text=f"Generation failed [{exc.code}]: {exc.message}{detail_line}",
                model_used=exc.model_used,
                provider_used=exc.provider_used,
            )
        except Exception:
            pass

        return _error_payload(
            status_code=exc.status_code,
            model_used=exc.model_used or requested_model,
            provider_used=exc.provider_used or exc.model_used or requested_model,
            failover_triggered=exc.failover_triggered,
            latency_ms=latency_ms,
            code=exc.code,
            message=exc.message,
            reason=exc.reason,
            violated_rule=exc.violated_rule,
            room=exc.room,
            details=exc.details,
        )

    except Exception as exc:  # pragma: no cover - safety net
        latency_ms = (perf_counter() - started_at) * 1000
        try:
            add_message(
                user_id=request.user_id,
                project_id=project_id,
                role="error",
                text=f"Generation failed: {exc}",
                model_used=requested_model,
                provider_used=requested_model,
            )
        except Exception:
            pass

        return _error_payload(
            status_code=500,
            model_used=requested_model,
            provider_used=requested_model,
            failover_triggered=False,
            latency_ms=latency_ms,
            code="INTERNAL_ERROR",
            message="Unexpected server error",
            details=[str(exc)],
        )


# Import the iterative endpoint types and service locally so the existing import section stays untouched.
from fastapi import Request

from app.models.iterative_design import IterateRequest, IterateResponse
from app.services.design_parser.diff_orchestrator import run_iterative_design


@router.post(
    "/workspace/{project_id}/iterate",
    response_model=IterateResponse,
    summary="Iterative design — edit existing layout with natural language",
)
async def iterate_design(
    project_id: str,
    body: IterateRequest,
    request: Request,
) -> IterateResponse:
    """
    Accept a natural-language instruction and return an updated layout plus optional DXF preview token.

    This route either starts a brand-new layout when no current layout is supplied,
    or applies a surgical edit to the existing layout using the iterative design engine.
    """

    # Resolve the user scope from the request body first, then fall back to the workspace guest cookie.
    cookie_user_id = request.cookies.get("cadarena_workspace_guest", "guest")
    resolved_user_id = (body.user_id or cookie_user_id or "guest").strip() or "guest"

    # Run the iterative layout pipeline with the project id as the memory and context scope.
    try:
        # Route purely on current_layout presence while still forwarding the selected model for full-parse fallback.
        result = await run_iterative_design(
            user_prompt=body.prompt,
            current_layout=body.current_layout,
            project_id=project_id,
            model_choice=body.model,
            recovery_mode=body.recovery_mode,
        )
    except ParseDesignServiceError as exc:
        details = [detail for detail in exc.details if detail]
        detail_suffix = f" | {' | '.join(details[:3])}" if details else ""
        return IterateResponse(
            layout=body.current_layout or {},
            dxf_path=None,
            preview_token=None,
            intent="NEW_DESIGN",
            is_new_design=body.current_layout is None,
            changed_rooms=[],
            self_review_triggered=False,
            error=[f"[{exc.code}] {exc.message}{detail_suffix}"],
        )
    except Exception as exc:  # pragma: no cover - safety net
        logger.exception("[iterate_design] iterative pipeline failed")
        return IterateResponse(
            layout=body.current_layout or {},
            dxf_path=None,
            preview_token=None,
            intent="NEW_DESIGN",
            is_new_design=body.current_layout is None,
            changed_rooms=[],
            self_review_triggered=False,
            error=[f"[INTERNAL_ERROR] {exc}"],
        )

    # Return iterative failures directly without attempting DXF conversion or token issuance.
    if result.get("error"):
        return IterateResponse(
            layout=result["layout"],
            dxf_path=None,
            preview_token=None,
            intent=result["intent"],
            is_new_design=result["is_new_design"],
            changed_rooms=result["changed_rooms"],
            self_review_triggered=result.get("self_review_triggered", False),
            error=result["error"],
        )

    # Convert the updated layout to a DXF intent, generate the DXF, and register a preview token when possible.
    layout = result["layout"]
    preview_token: str | None = None
    try:
        dxf_intent = DesignIntent.model_validate(
            {
                "boundary": layout.get("boundary", {}),
                "rooms": layout.get("rooms", []),
                "openings": layout.get("openings", []),
            }
        )
        dxf_path = await run_in_threadpool(generate_dxf_from_intent, dxf_intent)
        preview_token = issue_workspace_file_token(
            user_id=resolved_user_id,
            absolute_path=dxf_path,
        )
    except Exception as exc:  # pragma: no cover - safety net for optional DXF generation
        logger.warning("[iterate_design] DXF generation failed: %s", exc)

    # Return the updated layout metadata while never exposing the raw DXF file system path.
    return IterateResponse(
        layout=layout,
        dxf_path=None,
        preview_token=preview_token,
        intent=result["intent"],
        is_new_design=result["is_new_design"],
        changed_rooms=result["changed_rooms"],
        self_review_triggered=result.get("self_review_triggered", False),
    )


from fastapi import Depends

from app.core.auth import AuthenticatedUser, get_current_user


@router.post(
    "/workspace/me/projects/{project_id}/iterate",
    response_model=IterateResponse,
    summary="Iterative design for authenticated users",
)
async def iterate_design_authenticated(
    project_id: str,
    body: IterateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IterateResponse:
    """
    Authenticated iterative design endpoint.
    user_id is resolved from JWT - never from request body.
    """
    from app.services.design_parser.diff_orchestrator import run_iterative_design

    result = await run_iterative_design(
        user_prompt=body.prompt,
        current_layout=body.current_layout,
        project_id=project_id,
    )

    if result.get("error"):
        return IterateResponse(
            layout=result["layout"],
            dxf_path=None,
            preview_token=None,
            intent=result["intent"],
            is_new_design=result["is_new_design"],
            changed_rooms=result["changed_rooms"],
            error=result["error"],
        )

    layout = result["layout"]
    preview_token: str | None = None
    try:
        dxf_intent = DesignIntent.model_validate(
            {
                "boundary": layout.get("boundary", {}),
                "rooms": layout.get("rooms", []),
                "openings": layout.get("openings", []),
            }
        )
        dxf_path = await run_in_threadpool(generate_dxf_from_intent, dxf_intent)
        preview_token = issue_workspace_file_token(
            user_id=current_user.id,
            absolute_path=dxf_path,
        )
    except Exception as exc:
        logger.warning("[iterate_auth] DXF failed: %s", exc)

    return IterateResponse(
        layout=layout,
        dxf_path=None,
        preview_token=preview_token,
        intent=result["intent"],
        is_new_design=result["is_new_design"],
        changed_rooms=result["changed_rooms"],
        self_review_triggered=result.get("self_review_triggered", False),
    )
