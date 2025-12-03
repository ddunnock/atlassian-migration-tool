"""
Helper utility functions
"""
from datetime import datetime
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    Convert filename to safe filesystem name.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    filename = filename.strip('. ')

    if len(filename) > 200:
        filename = filename[:200]

    if not filename:
        filename = "unnamed"

    return filename


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_datetime(dt: datetime | None = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object (defaults to now)
        fmt: Format string

    Returns:
        Formatted datetime string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)
