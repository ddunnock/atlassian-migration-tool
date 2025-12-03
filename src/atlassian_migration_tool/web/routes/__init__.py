"""
Web Routes Module

This module contains all API route handlers for the web GUI.
"""

from atlassian_migration_tool.web.routes import (
    config,
    connections,
    extract,
    status,
    transform,
    upload,
)

__all__ = [
    "config",
    "connections",
    "extract",
    "transform",
    "upload",
    "status",
]
