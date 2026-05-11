import logging
import time
from contextvars import ContextVar
from typing import Optional

# Context variable to store the request ID for the current task/thread
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class RequestIdFormatter(logging.Formatter):
    """Formatter that includes the request_id from the context context."""
    def format(self, record):
        record.request_id = request_id_ctx.get() or "N/A"
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with enterprise-grade configuration.
    """
    logger = logging.getLogger(name)
    logger.propagate = False

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        
        # Structured format: [TIMESTAMP] [LEVEL] [REQUEST_ID] [LOGGER] - MESSAGE
        formatter = RequestIdFormatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(request_id)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
