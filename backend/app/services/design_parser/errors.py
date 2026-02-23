"""Typed service errors for the design parser flow."""

from __future__ import annotations


class ParseDesignServiceError(Exception):
    """Structured service exception for parse-design failures."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        model_used: str,
        provider_used: str | None = None,
        failover_triggered: bool = False,
        details: list[str] | None = None,
        reason: str | None = None,
        violated_rule: str | None = None,
        room: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.model_used = model_used
        self.provider_used = provider_used or model_used
        self.failover_triggered = failover_triggered
        self.details = details or []
        self.reason = reason
        self.violated_rule = violated_rule
        self.room = room
