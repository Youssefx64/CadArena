"""Pure domain entities with no framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Point2D:
    x: float
    y: float


Point = Point2D


@dataclass
class RectangleGeometry:
    width: float
    height: float
    origin: Point2D = field(default_factory=lambda: Point2D(x=0.0, y=0.0))
    type: str = "rectangle"


RectangleBoundary = RectangleGeometry


@dataclass
class Room:
    name: str
    room_type: str
    width: float
    height: float
    origin: Point2D | None = None


@dataclass
class Opening:
    type: str
    width: float
    position: Point2D
    orientation: str

