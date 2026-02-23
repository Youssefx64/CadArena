"""Shared structured rule-violation exception for deterministic planning."""

from __future__ import annotations


class RuleViolationError(ValueError):
    """Represents a deterministic architecture-rule violation."""

    def __init__(
        self,
        *,
        code: str,
        reason: str,
        violated_rule: str,
        room: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.violated_rule = violated_rule
        self.room = room

    def to_detail_message(self) -> str:
        if self.room:
            return f"{self.violated_rule}: {self.reason} (room={self.room})"
        return f"{self.violated_rule}: {self.reason}"
