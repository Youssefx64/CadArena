"""
Logging utility module.

Provides a centralized logging configuration for the application.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with standard configuration.
    
    Creates a logger with INFO level and a stream handler if one doesn't exist.
    Subsequent calls with the same name return the existing logger instance.
    
    Args:
        name: Logger name, typically the module name (e.g., __name__).
    
    Returns:
        Configured logger instance with stream handler and formatter.
    """
    logger = logging.getLogger(name)

    # Only configure if logger doesn't have handlers (avoid duplicate handlers)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(name)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
