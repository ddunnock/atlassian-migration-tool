"""
Task Manager for Background Operations

Manages background task execution with progress tracking.
"""

import asyncio
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger

from atlassian_migration_tool.web.services.progress_emitter import (
    ProgressStatus,
    progress_emitter,
)


class TaskType(str, Enum):
    """Types of background tasks."""

    EXTRACT = "extract"
    TRANSFORM = "transform"
    UPLOAD = "upload"


@dataclass
class TaskInfo:
    """Information about a running or completed task."""

    task_id: str
    task_type: TaskType
    status: ProgressStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: dict[str, Any] | None = None
    params: dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Manages background task execution.

    Uses a ThreadPoolExecutor to run blocking operations without
    blocking the async event loop.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskInfo] = {}
        self._cancel_flags: dict[str, threading.Event] = {}
        self._emitter = progress_emitter
        self._lock = threading.Lock()

    def create_task_id(self) -> str:
        """Generate a unique task ID."""
        return str(uuid.uuid4())[:8]

    async def start_task(
        self,
        task_type: TaskType,
        func: Callable,
        params: dict[str, Any],
    ) -> str:
        """
        Start a background task.

        Args:
            task_type: Type of task (extract, transform, upload)
            func: The function to execute (should accept task_id, cancel_flag, emitter, **params)
            params: Parameters to pass to the function

        Returns:
            The task ID
        """
        task_id = self.create_task_id()

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=ProgressStatus.PENDING,
            created_at=datetime.now(),
            params=params,
        )

        with self._lock:
            self._tasks[task_id] = task_info
            self._cancel_flags[task_id] = threading.Event()

        # Create progress queue
        self._emitter.create_task(task_id)

        # Submit to executor
        loop = asyncio.get_event_loop()
        self._executor.submit(
            self._run_task,
            loop,
            task_id,
            func,
            params,
        )

        logger.info(f"Started {task_type.value} task: {task_id}")
        return task_id

    def _run_task(
        self,
        loop: asyncio.AbstractEventLoop,
        task_id: str,
        func: Callable,
        params: dict[str, Any],
    ) -> None:
        """
        Execute a task in a thread.

        This bridges the sync thread execution with async progress emission.
        """
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = ProgressStatus.RUNNING
                self._tasks[task_id].started_at = datetime.now()

        cancel_flag = self._cancel_flags.get(task_id)

        # Create a sync wrapper for emitting progress
        def emit_progress(progress: int, message: str, **kwargs):
            asyncio.run_coroutine_threadsafe(
                self._emitter.emit_progress(task_id, progress, message, **kwargs),
                loop,
            )

        def emit_log(message: str, level: str = "info"):
            asyncio.run_coroutine_threadsafe(
                self._emitter.emit_log(task_id, message, level),
                loop,
            )

        def is_cancelled() -> bool:
            return cancel_flag.is_set() if cancel_flag else False

        try:
            # Execute the task function
            result = func(
                task_id=task_id,
                emit_progress=emit_progress,
                emit_log=emit_log,
                is_cancelled=is_cancelled,
                **params,
            )

            # Task completed successfully
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].status = ProgressStatus.COMPLETED
                    self._tasks[task_id].completed_at = datetime.now()
                    self._tasks[task_id].result = result

            asyncio.run_coroutine_threadsafe(
                self._emitter.emit_complete(
                    task_id,
                    success=True,
                    message="Task completed successfully",
                    result=result,
                ),
                loop,
            )

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Task {task_id} failed: {error_msg}")

            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].status = ProgressStatus.FAILED
                    self._tasks[task_id].completed_at = datetime.now()
                    self._tasks[task_id].error = error_msg

            asyncio.run_coroutine_threadsafe(
                self._emitter.emit_error(task_id, error_msg),
                loop,
            )

        finally:
            # Cleanup
            with self._lock:
                if task_id in self._cancel_flags:
                    del self._cancel_flags[task_id]

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: The task to cancel

        Returns:
            True if the task was found and signaled, False otherwise
        """
        with self._lock:
            if task_id in self._cancel_flags:
                self._cancel_flags[task_id].set()
                if task_id in self._tasks:
                    self._tasks[task_id].status = ProgressStatus.CANCELLED
                logger.info(f"Cancelled task: {task_id}")
                return True
        return False

    def get_task_info(self, task_id: str) -> TaskInfo | None:
        """Get information about a task."""
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(
        self,
        task_type: TaskType | None = None,
        status: ProgressStatus | None = None,
    ) -> list[TaskInfo]:
        """
        List tasks with optional filtering.

        Args:
            task_type: Filter by task type
            status: Filter by status

        Returns:
            List of matching tasks
        """
        with self._lock:
            tasks = list(self._tasks.values())

        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        if status:
            tasks = [t for t in tasks if t.status == status]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """
        Remove completed tasks older than max_age_seconds.

        Returns the number of tasks removed.
        """
        now = datetime.now()
        removed = 0

        with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.status in (
                    ProgressStatus.COMPLETED,
                    ProgressStatus.FAILED,
                    ProgressStatus.CANCELLED,
                ):
                    if task.completed_at:
                        age = (now - task.completed_at).total_seconds()
                        if age > max_age_seconds:
                            to_remove.append(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]
                removed += 1

        if removed:
            logger.debug(f"Cleaned up {removed} completed tasks")

        return removed


# Global task manager instance
task_manager = TaskManager()
