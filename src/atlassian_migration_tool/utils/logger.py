"""
Logging configuration
"""
import sys
from pathlib import Path

from loguru import logger


def setup_logger(
        level: str = "INFO",
        log_file: str = "data/logs/migration.log",
        console: bool = True
):
    """
    Configure logger with file and console output.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        console: Whether to log to console

    Returns:
        Configured logger
    """
    logger.remove()

    if console:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
                   "<level>{message}</level>",
            level=level,
        )

    # Ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        rotation="100 MB",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    )

    return logger
