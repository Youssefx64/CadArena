import asyncio
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import types

import pytest
from fastapi.responses import JSONResponse

from app.core.auth import AuthenticatedUser
from app.models.design_parser import ParseDesignModel
from app.models.workspace import (
    WorkspaceGenerateDxfForCurrentUserRequest,
    WorkspaceGenerateDxfRequest,
)

_langchain_engine_stub = types.ModuleType("app.services.langchain_engine")


class _StubCadArenaLangChainEngine:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    async def extract_diff(self, *args, **kwargs) -> dict:
        return {}

    def clear_memory(self, *args, **kwargs) -> None:
        return None


_langchain_engine_stub.CadArenaLangChainEngine = _StubCadArenaLangChainEngine
sys.modules.setdefault("app.services.langchain_engine", _langchain_engine_stub)

from app.routers import workspace as workspace_module
from app.routers import workspace_auth as workspace_auth_module


def _sample_parsed_layout() -> dict:
    return {
        "boundary": {"width": 10.0, "height": 8.0},
        "rooms": [
            {
                "name": "Living Room",
                "room_type": "living",
                "width": 4.0,
                "height": 4.0,
                "origin": {"x": 0.0, "y": 0.0},
            }
        ],
        "walls": [
            {
                "room_name": "Living Room",
                "wall": "bottom",
                "start": {"x": 0.0, "y": 0.0},
                "end": {"x": 4.0, "y": 0.0},
                "thickness": 0.2,
            },
            {
                "room_name": "Living Room",
                "wall": "top",
                "start": {"x": 0.0, "y": 4.0},
                "end": {"x": 4.0, "y": 4.0},
                "thickness": 0.2,
            },
            {
                "room_name": "Living Room",
                "wall": "left",
                "start": {"x": 0.0, "y": 0.0},
                "end": {"x": 0.0, "y": 4.0},
                "thickness": 0.2,
            },
            {
                "room_name": "Living Room",
                "wall": "right",
                "start": {"x": 4.0, "y": 0.0},
                "end": {"x": 4.0, "y": 4.0},
                "thickness": 0.2,
            },
        ],
        "openings": [
            {
                "type": "door",
                "room_name": "Living Room",
                "wall": "bottom",
                "cut_start": {"x": 1.0, "y": 0.0},
                "cut_end": {"x": 2.0, "y": 0.0},
                "hinge": "left",
                "swing": "in",
            }
        ],
    }


def _sample_metrics() -> dict:
    return {
        "area_balance": 0.91,
        "zoning": 0.92,
        "circulation": 0.93,
        "daylight": 0.94,
        "structural": 0.95,
        "furniture": 0.96,
        "efficiency": 0.97,
        "total_score": 0.98,
        "selected_topology": "single_room",
    }


def _install_generate_dxf_success_stubs(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    parsed_layout = _sample_parsed_layout()
    issued_user_ids: list[str] = []
    message_ids = iter(("user-msg-1", "assistant-msg-1"))

    monkeypatch.setattr(workspace_module, "get_project", lambda **_: {"name": "Unit Test Project"})

    def _fake_add_message(**_: object) -> str:
        return next(message_ids)

    async def _fake_parse_with_layout_retry(**_: object):
        return (
            SimpleNamespace(
                model_used="qwen2.5:7b-instruct",
                provider_used="ollama",
                failover_triggered=False,
                self_review_triggered=False,
                data=parsed_layout,
                metrics=_sample_metrics(),
            ),
            "Design a compact house",
            False,
            False,
        )

    async def _fake_run_in_threadpool(func, *args, **kwargs):
        assert callable(func)
        assert args
        assert args[0].model_dump()["boundary"]["width"] == 10.0
        return Path("/tmp/generated-layout.dxf")

    def _fake_issue_workspace_file_token(*, user_id: str, absolute_path) -> str:
        issued_user_ids.append(user_id)
        assert Path(absolute_path) == Path("/tmp/generated-layout.dxf")
        return f"workspace-token-{user_id}"

    monkeypatch.setattr(workspace_module, "add_message", _fake_add_message)
    monkeypatch.setattr(workspace_module, "_parse_with_layout_retry", _fake_parse_with_layout_retry)
    monkeypatch.setattr(workspace_module, "save_parse_design_output", lambda **_: None)
    monkeypatch.setattr(workspace_module, "run_in_threadpool", _fake_run_in_threadpool)
    monkeypatch.setattr(workspace_module, "issue_workspace_file_token", _fake_issue_workspace_file_token)
    monkeypatch.setattr(workspace_module, "_project_dxf_name", lambda _: "unit_test_project.dxf")

    return {
        "parsed_layout": parsed_layout,
        "issued_user_ids": issued_user_ids,
    }


def test_workspace_generate_dxf_returns_top_level_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _install_generate_dxf_success_stubs(monkeypatch)

    response = asyncio.run(
        workspace_module.workspace_generate_dxf(
            "project-1",
            WorkspaceGenerateDxfRequest(
                user_id="guest-1",
                prompt="Design a compact house",
                model=ParseDesignModel.OLLAMA,
            ),
        )
    )

    payload = json.loads(response.body)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert payload["file_token"] == "workspace-token-guest-1"
    assert payload["dxf_name"] == "unit_test_project.dxf"
    assert payload["data"]["walls"] == fixtures["parsed_layout"]["walls"]
    assert payload["layout"] == {
        "boundary": fixtures["parsed_layout"]["boundary"],
        "rooms": fixtures["parsed_layout"]["rooms"],
        "openings": fixtures["parsed_layout"]["openings"],
    }
    assert "walls" not in payload["layout"]
    assert fixtures["issued_user_ids"] == ["guest-1"]


def test_me_generate_dxf_inherits_top_level_layout_from_shared_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures = _install_generate_dxf_success_stubs(monkeypatch)

    response = asyncio.run(
        workspace_auth_module.me_generate_dxf(
            "project-2",
            WorkspaceGenerateDxfForCurrentUserRequest(
                prompt="Design a compact house",
                model=ParseDesignModel.OLLAMA,
            ),
            AuthenticatedUser(
                id="auth-1",
                name="Planner",
                email="planner@example.com",
                created_at="2026-04-02T00:00:00Z",
            ),
        )
    )

    payload = json.loads(response.body)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert payload["file_token"] == "workspace-token-auth-1"
    assert payload["layout"]["rooms"] == fixtures["parsed_layout"]["rooms"]
    assert payload["layout"]["openings"] == fixtures["parsed_layout"]["openings"]
    assert "walls" not in payload["layout"]
    assert fixtures["issued_user_ids"] == ["auth-1"]
