"""Authenticated workspace routes that infer user_id from JWT."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthenticatedUser, get_current_user
from app.models.workspace import (
    CreateProjectForCurrentUserRequest,
    ProjectListResponse,
    ProjectMessagesResponse,
    ProjectRecord,
    RenameProjectForCurrentUserRequest,
    WorkspaceGenerateDxfForCurrentUserRequest,
    WorkspaceGenerateDxfRequest,
    WorkspaceGenerateDxfSuccessResponse,
)
from app.routers.workspace import workspace_generate_dxf
from app.services.workspace_storage import (
    create_project,
    delete_project,
    list_project_messages,
    list_projects,
    rename_project,
)

router = APIRouter(prefix="/workspace/me", tags=["workspace-auth"])


@router.get("/projects", response_model=ProjectListResponse)
def me_list_projects(current_user: AuthenticatedUser = Depends(get_current_user)):
    projects = list_projects(user_id=current_user.id)
    return ProjectListResponse(projects=[ProjectRecord(**item) for item in projects])


@router.post("/projects", response_model=ProjectRecord, status_code=201)
def me_create_project(
    request: CreateProjectForCurrentUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        project = create_project(user_id=current_user.id, name=request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProjectRecord(**project)


@router.patch("/projects/{project_id}", response_model=ProjectRecord)
def me_rename_project(
    project_id: str,
    request: RenameProjectForCurrentUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        project = rename_project(user_id=current_user.id, project_id=project_id, name=request.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRecord(**project)


@router.delete("/projects/{project_id}")
def me_delete_project(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    deleted = delete_project(user_id=current_user.id, project_id=project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}


@router.get("/projects/{project_id}/messages", response_model=ProjectMessagesResponse)
def me_project_messages(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    project, messages = list_project_messages(user_id=current_user.id, project_id=project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectMessagesResponse(project=ProjectRecord(**project), messages=messages)


@router.post(
    "/projects/{project_id}/generate-dxf",
    response_model=WorkspaceGenerateDxfSuccessResponse,
)
async def me_generate_dxf(
    project_id: str,
    request: WorkspaceGenerateDxfForCurrentUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    # Hydrate the authenticated request into the shared guest-compatible shape, including cloud model ids.
    hydrated_request = WorkspaceGenerateDxfRequest(
        user_id=current_user.id,
        prompt=request.prompt,
        model=request.model,
        model_id=request.model_id,
        recovery_mode=request.recovery_mode,
    )
    return await workspace_generate_dxf(project_id, hydrated_request)
