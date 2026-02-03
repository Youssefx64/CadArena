from typing import Literal


class DoorSpec:
    def __init__(
        self,
        width: float = 1.0,
        hinge: Literal["left", "right"] = "left",
        swing: Literal["in", "out"] = "in",
        angle: float = 90,
    ):
        self.width = width
        self.hinge = hinge
        self.swing = swing
        self.angle = angle
