"""Pydantic models for design parsing API contracts."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_EPSILON = 1e-6


class ParseDesignModel(str, Enum):
    """Supported model backends for parse-design route."""

    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


class RecoveryMode(str, Enum):
    """Recovery behavior when model output is invalid."""

    STRICT = "strict"
    REPAIR = "repair"


class ParseDesignRequest(BaseModel):
    """Incoming request payload for design parsing."""

    prompt: str = Field(min_length=1, max_length=12000)
    model: ParseDesignModel
    recovery_mode: RecoveryMode = RecoveryMode.STRICT

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def _validate_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")
        return cleaned


class Point2D(BaseModel):
    """2D point in meters."""

    x: float
    y: float

    model_config = ConfigDict(extra="forbid")


class BoundaryIntent(BaseModel):
    """Building footprint boundary."""

    width: float = Field(gt=0)
    height: float = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class RoomIntent(BaseModel):
    """Rectangular room intent."""

    name: str = Field(min_length=1)
    room_type: str = Field(min_length=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    origin: Point2D

    model_config = ConfigDict(extra="forbid")


class WallSide(str, Enum):
    """Canonical wall side naming relative to room."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class WallIntent(BaseModel):
    """Explicit wall segments used by downstream DXF pipeline."""

    room_name: str = Field(min_length=1)
    wall: WallSide
    start: Point2D
    end: Point2D
    thickness: float = Field(default=0.2, gt=0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_non_zero_segment(self) -> "WallIntent":
        if abs(self.start.x - self.end.x) <= _EPSILON and abs(self.start.y - self.end.y) <= _EPSILON:
            raise ValueError("wall segment must be non-zero")
        return self


class OpeningType(str, Enum):
    """Supported opening types."""

    DOOR = "door"
    WINDOW = "window"


class OpeningIntent(BaseModel):
    """Door/window cut segment on a room wall."""

    type: OpeningType
    room_name: str = Field(min_length=1)
    wall: WallSide
    cut_start: Point2D
    cut_end: Point2D
    hinge: Literal["left", "right"] | None = None
    swing: Literal["in", "out"] | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_type_specific_rules(self) -> "OpeningIntent":
        if abs(self.cut_start.x - self.cut_end.x) <= _EPSILON and abs(self.cut_start.y - self.cut_end.y) <= _EPSILON:
            raise ValueError("opening cut segment must be non-zero")

        if self.type == OpeningType.DOOR:
            if self.hinge is None or self.swing is None:
                raise ValueError("door openings require hinge and swing")
        else:
            if self.hinge is not None or self.swing is not None:
                raise ValueError("window openings must not contain hinge or swing")
        return self


class ParsedDesignIntent(BaseModel):
    """Strict structured output used to generate DXF."""

    boundary: BoundaryIntent
    rooms: list[RoomIntent] = Field(min_length=1)
    walls: list[WallIntent] = Field(min_length=1)
    openings: list[OpeningIntent] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_geometry(self) -> "ParsedDesignIntent":
        room_map: dict[str, RoomIntent] = {}

        for room in self.rooms:
            if room.name in room_map:
                raise ValueError(f"duplicate room name: {room.name}")
            room_map[room.name] = room
            self._assert_room_inside_boundary(room)

        self._assert_no_room_overlap(self.rooms)

        declared_walls = {(wall.room_name, wall.wall.value) for wall in self.walls}
        for wall in self.walls:
            room = room_map.get(wall.room_name)
            if room is None:
                raise ValueError(f"wall references unknown room: {wall.room_name}")
            self._assert_segment_on_room_wall(
                room=room,
                wall=wall.wall.value,
                start=wall.start,
                end=wall.end,
                label=f"wall {wall.room_name}:{wall.wall.value}",
            )

        for opening in self.openings:
            room = room_map.get(opening.room_name)
            if room is None:
                raise ValueError(f"opening references unknown room: {opening.room_name}")
            if (opening.room_name, opening.wall.value) not in declared_walls:
                raise ValueError(
                    f"opening references undeclared wall: {opening.room_name}:{opening.wall.value}"
                )
            self._assert_segment_on_room_wall(
                room=room,
                wall=opening.wall.value,
                start=opening.cut_start,
                end=opening.cut_end,
                label=f"opening {opening.room_name}:{opening.wall.value}",
            )

        return self

    def _assert_room_inside_boundary(self, room: RoomIntent) -> None:
        x0 = room.origin.x
        y0 = room.origin.y
        x1 = x0 + room.width
        y1 = y0 + room.height

        if x0 < -_EPSILON or y0 < -_EPSILON:
            raise ValueError(f"room '{room.name}' has negative origin")
        if x1 > self.boundary.width + _EPSILON or y1 > self.boundary.height + _EPSILON:
            raise ValueError(f"room '{room.name}' exceeds boundary")

    @staticmethod
    def _assert_no_room_overlap(rooms: list[RoomIntent]) -> None:
        for idx, room_a in enumerate(rooms):
            ax0 = room_a.origin.x
            ay0 = room_a.origin.y
            ax1 = ax0 + room_a.width
            ay1 = ay0 + room_a.height

            for room_b in rooms[idx + 1 :]:
                bx0 = room_b.origin.x
                by0 = room_b.origin.y
                bx1 = bx0 + room_b.width
                by1 = by0 + room_b.height

                overlap_x = ax0 < bx1 - _EPSILON and ax1 > bx0 + _EPSILON
                overlap_y = ay0 < by1 - _EPSILON and ay1 > by0 + _EPSILON
                if overlap_x and overlap_y:
                    raise ValueError(f"rooms overlap: '{room_a.name}' and '{room_b.name}'")

    @staticmethod
    def _assert_segment_on_room_wall(
        room: RoomIntent,
        wall: str,
        start: Point2D,
        end: Point2D,
        label: str,
    ) -> None:
        x0 = room.origin.x
        y0 = room.origin.y
        x1 = x0 + room.width
        y1 = y0 + room.height

        if wall == WallSide.BOTTOM.value:
            ParsedDesignIntent._assert_horizontal_segment(start, end, x0, x1, y0, label)
            return
        if wall == WallSide.TOP.value:
            ParsedDesignIntent._assert_horizontal_segment(start, end, x0, x1, y1, label)
            return
        if wall == WallSide.LEFT.value:
            ParsedDesignIntent._assert_vertical_segment(start, end, y0, y1, x0, label)
            return
        if wall == WallSide.RIGHT.value:
            ParsedDesignIntent._assert_vertical_segment(start, end, y0, y1, x1, label)
            return

        raise ValueError(f"unsupported wall side: {wall}")

    @staticmethod
    def _assert_horizontal_segment(
        start: Point2D,
        end: Point2D,
        min_x: float,
        max_x: float,
        expected_y: float,
        label: str,
    ) -> None:
        if abs(start.y - expected_y) > _EPSILON or abs(end.y - expected_y) > _EPSILON:
            raise ValueError(f"{label} must lie on y={expected_y}")

        sx, ex = sorted((start.x, end.x))
        if sx < min_x - _EPSILON or ex > max_x + _EPSILON:
            raise ValueError(f"{label} exceeds wall bounds")
        if ex - sx <= _EPSILON:
            raise ValueError(f"{label} segment length must be > 0")

    @staticmethod
    def _assert_vertical_segment(
        start: Point2D,
        end: Point2D,
        min_y: float,
        max_y: float,
        expected_x: float,
        label: str,
    ) -> None:
        if abs(start.x - expected_x) > _EPSILON or abs(end.x - expected_x) > _EPSILON:
            raise ValueError(f"{label} must lie on x={expected_x}")

        sy, ey = sorted((start.y, end.y))
        if sy < min_y - _EPSILON or ey > max_y + _EPSILON:
            raise ValueError(f"{label} exceeds wall bounds")
        if ey - sy <= _EPSILON:
            raise ValueError(f"{label} segment length must be > 0")


class ParseErrorBody(BaseModel):
    """Structured API error payload."""

    code: str
    message: str
    details: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ParseDesignSuccessResponse(BaseModel):
    """Successful parse-design response."""

    success: Literal[True]
    model_used: str
    provider_used: str
    failover_triggered: bool = False
    latency_ms: float = Field(ge=0)
    data: ParsedDesignIntent

    model_config = ConfigDict(extra="forbid")


class ParseDesignErrorResponse(BaseModel):
    """Failed parse-design response."""

    success: Literal[False]
    model_used: str
    provider_used: str
    failover_triggered: bool = False
    latency_ms: float = Field(ge=0)
    error: ParseErrorBody

    model_config = ConfigDict(extra="forbid")
