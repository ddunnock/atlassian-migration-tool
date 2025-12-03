"""
Web Services Module

This module contains background task management and progress streaming services.
"""

from atlassian_migration_tool.web.services.progress_emitter import ProgressEmitter, progress_emitter
from atlassian_migration_tool.web.services.task_manager import TaskManager, task_manager

__all__ = [
    "TaskManager",
    "task_manager",
    "ProgressEmitter",
    "progress_emitter",
]
