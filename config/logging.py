import logging

from rich.logging import RichHandler

LOGGING_LEVEL = logging.INFO


def setup_logging(name: str = __name__) -> logging.Logger:
    """
    Setup and return a logger with RichHandler for better formatting.

    Args:
        name: The name of the logger (usually __name__)

    Returns:
        A configured logger instance
    """
    logging.basicConfig(
        format="%(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=LOGGING_LEVEL,
        handlers=[RichHandler(rich_tracebacks=True)],
        force=True,
    )
    return logging.getLogger(name)
