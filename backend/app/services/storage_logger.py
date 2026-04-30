"""Structured logging for database operations."""

import logging
from typing import Any, Optional

logger = logging.getLogger("cadarena.storage")


class StorageLogger:
    """Centralized logging for database mutations and security events."""

    @staticmethod
    def log_mutation(
        operation: str,
        table: str,
        record_id: str,
        user_id: Optional[str] = None,
        changes: Optional[dict] = None,
    ) -> None:
        """Log database mutation (CREATE, UPDATE, DELETE)."""
        logger.info(
            f"{operation} {table}",
            extra={
                "operation": operation,
                "table": table,
                "record_id": record_id,
                "user_id": user_id,
                "changes": changes or {},
            },
        )

    @staticmethod
    def log_query_error(
        operation: str,
        query: str,
        exception: Exception,
        user_id: Optional[str] = None,
    ) -> None:
        """Log query execution error."""
        logger.error(
            f"Query error in {operation}: {str(exception)}",
            extra={
                "operation": operation,
                "query": query[:200],
                "user_id": user_id,
                "exception": str(exception),
            },
            exc_info=True,
        )

    @staticmethod
    def log_security_event(
        event: str,
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Log security-related events (API key ops, voting, etc)."""
        logger.info(
            f"Security event: {event}",
            extra={
                "event": event,
                "user_id": user_id,
                "details": details or {},
            },
        )

    @staticmethod
    def log_validation_error(
        field: str,
        value: Any,
        reason: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log validation failures."""
        logger.warning(
            f"Validation error: {field} - {reason}",
            extra={
                "field": field,
                "value": str(value)[:100],
                "reason": reason,
                "user_id": user_id,
            },
        )

    @staticmethod
    def log_constraint_violation(
        table: str,
        constraint: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log constraint violations (unique, foreign key, etc)."""
        logger.warning(
            f"Constraint violation: {table}.{constraint}",
            extra={
                "table": table,
                "constraint": constraint,
                "user_id": user_id,
            },
        )
