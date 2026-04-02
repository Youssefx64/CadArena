import asyncio
import sys
from types import SimpleNamespace
from types import ModuleType

import pytest

from app.models.design_parser import ParseDesignModel, RecoveryMode

fake_langchain_engine = ModuleType("app.services.langchain_engine")


class _StubCadArenaLangChainEngine:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs


fake_langchain_engine.CadArenaLangChainEngine = _StubCadArenaLangChainEngine
sys.modules.setdefault("app.services.langchain_engine", fake_langchain_engine)

from app.services.design_parser import diff_orchestrator


def _sample_layout() -> dict:
    return {
        "boundary": {"width": 10.0, "height": 10.0},
        "rooms": [
            {
                "name": "Kitchen",
                "room_type": "kitchen",
                "width": 3.0,
                "height": 2.5,
                "origin": {"x": 0.0, "y": 0.0},
            },
            {
                "name": "Bedroom",
                "room_type": "bedroom",
                "width": 3.0,
                "height": 3.0,
                "origin": {"x": 3.2, "y": 0.0},
            },
        ],
        "walls": [],
        "openings": [],
    }


def test_run_iterative_design_uses_full_parse_for_new_design(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing current layout should bypass diff extraction and run a fresh parse."""

    class FakeEngine:
        def __init__(self) -> None:
            self.cleared: list[str] = []

        def clear_memory(self, project_id: str) -> None:
            self.cleared.append(project_id)

    fake_engine = FakeEngine()
    parsed_layout = {
        "boundary": {"width": 12.0, "height": 10.0},
        "rooms": [],
        "walls": [],
        "openings": [],
    }
    captured: dict[str, object] = {}

    async def _fake_parse_design_prompt_with_metadata(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(data=parsed_layout, self_review_triggered=True)

    monkeypatch.setattr(diff_orchestrator, "_resolve_langchain_engine", lambda _model: fake_engine)
    monkeypatch.setattr(
        diff_orchestrator,
        "parse_design_prompt_with_metadata",
        _fake_parse_design_prompt_with_metadata,
    )

    result = asyncio.run(
        diff_orchestrator.run_iterative_design(
            user_prompt="Design a compact house",
            current_layout=None,
            project_id="project-1",
            model_choice=ParseDesignModel.HUGGINGFACE,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert result["layout"] == parsed_layout
    assert result["intent"] == "NEW_DESIGN"
    assert result["is_new_design"] is True
    assert result["changed_rooms"] == []
    assert result["self_review_triggered"] is True
    assert fake_engine.cleared == ["project-1"]
    assert captured["model_choice"] == ParseDesignModel.HUGGINGFACE


def test_run_iterative_design_falls_back_to_full_parse_after_diff_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Diff extraction failures should full-parse when heuristics cannot derive an edit."""

    class FailingDiffEngine:
        def __init__(self) -> None:
            self.cleared: list[str] = []

        async def extract_diff(self, user_prompt: str, current_layout: dict, project_id: str) -> dict:
            raise RuntimeError("diff unavailable")

        def clear_memory(self, project_id: str) -> None:
            self.cleared.append(project_id)

    fake_engine = FailingDiffEngine()
    parsed_layout = {
        "boundary": {"width": 14.0, "height": 10.0},
        "rooms": [],
        "walls": [],
        "openings": [],
    }

    async def _fake_parse_design_prompt_with_metadata(**kwargs):
        return SimpleNamespace(data=parsed_layout, self_review_triggered=False)

    monkeypatch.setattr(diff_orchestrator, "_resolve_langchain_engine", lambda _model: fake_engine)
    monkeypatch.setattr(
        diff_orchestrator,
        "parse_design_prompt_with_metadata",
        _fake_parse_design_prompt_with_metadata,
    )

    result = asyncio.run(
        diff_orchestrator.run_iterative_design(
            user_prompt="Please rethink this layout from scratch",
            current_layout=_sample_layout(),
            project_id="project-2",
            model_choice=ParseDesignModel.HUGGINGFACE,
            recovery_mode=RecoveryMode.REPAIR,
        )
    )

    assert result["layout"] == parsed_layout
    assert result["intent"] == "FULL_PARSE_FALLBACK"
    assert result["is_new_design"] is True
    assert fake_engine.cleared == ["project-2"]


def test_run_iterative_design_returns_original_layout_when_patch_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patch failures should return the untouched source layout with an error payload."""

    class FakeEngine:
        async def extract_diff(self, user_prompt: str, current_layout: dict, project_id: str) -> dict:
            return {
                "operation": "modify",
                "changes": {"rooms_to_modify": [{"name": "Kitchen", "width": 4.0, "height": 3.0}]},
            }

    class BrokenPatcher:
        def apply(self, current: dict, diff: dict) -> dict:
            raise ValueError("patch failed")

    monkeypatch.setattr(diff_orchestrator, "_resolve_langchain_engine", lambda _model: FakeEngine())
    monkeypatch.setattr(diff_orchestrator, "LayoutPatcher", BrokenPatcher)

    current_layout = _sample_layout()
    result = asyncio.run(
        diff_orchestrator.run_iterative_design(
            user_prompt="Make the kitchen bigger",
            current_layout=current_layout,
            project_id="project-3",
        )
    )

    assert result["layout"] == current_layout
    assert result["intent"] == "PATCH_FAILED"
    assert result["changed_rooms"] == []
    assert result["error"] == ["patch failed"]


def test_run_iterative_design_returns_original_layout_when_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validation failures should discard the patch and preserve the original layout."""

    patched_layout = {
        **_sample_layout(),
        "rooms": [
            *_sample_layout()["rooms"],
            {
                "name": "Bathroom",
                "room_type": "bathroom",
                "width": 2.0,
                "height": 2.0,
                "origin": {"x": 0.0, "y": 3.2},
            },
        ],
        "openings": [{"type": "door", "room_name": "Bathroom"}],
    }

    class FakeEngine:
        async def extract_diff(self, user_prompt: str, current_layout: dict, project_id: str) -> dict:
            return {
                "operation": "add",
                "changes": {
                    "rooms_to_add": [
                        {
                            "name": "Bathroom",
                            "room_type": "bathroom",
                            "width": 2.0,
                            "height": 2.0,
                        }
                    ]
                },
            }

    class FakePatcher:
        def apply(self, current: dict, diff: dict) -> dict:
            return patched_layout

    class FakePlanner:
        def plan(self, *, extracted_payload: dict, layout_payload: dict) -> dict:
            return patched_layout

    class BrokenValidator:
        def validate(self, *, extracted_payload: dict, planned_payload: dict, selected_topology: str = "unknown") -> None:
            raise ValueError("validation failed")

    monkeypatch.setattr(diff_orchestrator, "_resolve_langchain_engine", lambda _model: FakeEngine())
    monkeypatch.setattr(diff_orchestrator, "LayoutPatcher", FakePatcher)
    monkeypatch.setattr(diff_orchestrator, "DeterministicOpeningPlanner", FakePlanner)
    monkeypatch.setattr(diff_orchestrator, "LayoutValidator", BrokenValidator)

    current_layout = _sample_layout()
    result = asyncio.run(
        diff_orchestrator.run_iterative_design(
            user_prompt="Add a bathroom",
            current_layout=current_layout,
            project_id="project-4",
        )
    )

    assert result["layout"] == current_layout
    assert result["intent"] == "VALIDATION_FAILED"
    assert result["changed_rooms"] == []
    assert result["error"] == ["validation failed"]


def test_run_iterative_design_returns_changed_rooms_for_successful_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful iterative patches should return changed-room metadata."""

    patched_layout = {
        **_sample_layout(),
        "rooms": [
            *_sample_layout()["rooms"],
            {
                "name": "Bathroom",
                "room_type": "bathroom",
                "width": 2.0,
                "height": 2.0,
                "origin": {"x": 0.0, "y": 3.2},
            },
        ],
        "openings": [{"type": "door", "room_name": "Bathroom"}],
    }

    class FakeEngine:
        async def extract_diff(self, user_prompt: str, current_layout: dict, project_id: str) -> dict:
            return {
                "operation": "add",
                "changes": {
                    "rooms_to_add": [
                        {
                            "name": "Bathroom",
                            "room_type": "bathroom",
                            "width": 2.0,
                            "height": 2.0,
                        }
                    ]
                },
            }

    class FakePatcher:
        def apply(self, current: dict, diff: dict) -> dict:
            return patched_layout

    class FakePlanner:
        def plan(self, *, extracted_payload: dict, layout_payload: dict) -> dict:
            return patched_layout

    class PassingValidator:
        def validate(self, *, extracted_payload: dict, planned_payload: dict, selected_topology: str = "unknown") -> None:
            return None

    monkeypatch.setattr(diff_orchestrator, "_resolve_langchain_engine", lambda _model: FakeEngine())
    monkeypatch.setattr(diff_orchestrator, "LayoutPatcher", FakePatcher)
    monkeypatch.setattr(diff_orchestrator, "DeterministicOpeningPlanner", FakePlanner)
    monkeypatch.setattr(diff_orchestrator, "LayoutValidator", PassingValidator)

    result = asyncio.run(
        diff_orchestrator.run_iterative_design(
            user_prompt="Add a bathroom",
            current_layout=_sample_layout(),
            project_id="project-5",
        )
    )

    assert result["layout"] == patched_layout
    assert result["intent"] == "ADD"
    assert result["is_new_design"] is False
    assert result["changed_rooms"] == ["Bathroom"]
    assert result["self_review_triggered"] is False


def test_heuristic_diff_handles_add_room_and_relative_resize() -> None:
    """Heuristic extraction should cover basic add-room and relative-resize prompts."""

    current_layout = _sample_layout()

    add_diff = diff_orchestrator._heuristic_diff_from_prompt("Add a bathroom", current_layout)
    resize_diff = diff_orchestrator._heuristic_diff_from_prompt("Make the kitchen bigger", current_layout)

    assert add_diff["operation"] == "add"
    assert add_diff["changes"]["rooms_to_add"][0]["room_type"] == "bathroom"
    assert add_diff["changes"]["rooms_to_add"][0]["name"] == "Bathroom"
    assert resize_diff["operation"] == "modify"
    assert resize_diff["changes"]["rooms_to_modify"][0]["name"] == "Kitchen"
    assert resize_diff["changes"]["rooms_to_modify"][0]["width"] > 3.0
    assert resize_diff["changes"]["rooms_to_modify"][0]["height"] > 2.5
