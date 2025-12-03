"""
Web GUI Module

This module provides a web-based graphical user interface for the
Atlassian Migration Tool using FastAPI and HTMX.
"""

from atlassian_migration_tool.web.app import app, main, start_server

__all__ = ["app", "main", "start_server"]
