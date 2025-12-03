"""
Progress Emitter for Server-Sent Events

Manages streaming progress updates to the web UI via SSE.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class ProgressStatus(str, Enum):
    """Status values for progress events."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressEvent:
    """A progress event to be sent via SSE."""

    task_id: str
    event_type: str  # progress, log, status, complete, error
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ProgressEmitter:
    """
    Manages Server-Sent Events for progress streaming.

    Each task has its own asyncio.Queue for events.
    Subscribers receive events from the queue until completion.
    """

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._task_status: dict[str, ProgressStatus] = {}

    def create_task(self, task_id: str) -> None:
        """Create a new task with an event queue."""
        if task_id not in self._queues:
            self._queues[task_id] = asyncio.Queue()
            self._task_status[task_id] = ProgressStatus.PENDING
            logger.debug(f"Created progress queue for task: {task_id}")

    async def emit(
        self,
        task_id: str,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        """
        Emit a progress event.

        Args:
            task_id: The task identifier
            event_type: Type of event (progress, log, status, complete, error)
            data: Event data to send
        """
        if task_id not in self._queues:
            self.create_task(task_id)

        event = ProgressEvent(
            task_id=task_id,
            event_type=event_type,
            data=data,
        )

        await self._queues[task_id].put(event)
        logger.debug(f"Emitted {event_type} event for task {task_id}")

    async def emit_progress(
        self,
        task_id: str,
        progress: int,
        message: str,
        current: int | None = None,
        total: int | None = None,
    ) -> None:
        """
        Emit a progress update.

        Args:
            task_id: The task identifier
            progress: Progress percentage (0-100)
            message: Human-readable progress message
            current: Current item number (optional)
            total: Total items (optional)
        """
        data = {
            "progress": progress,
            "message": message,
        }
        if current is not None:
            data["current"] = current
        if total is not None:
            data["total"] = total

        await self.emit(task_id, "progress", data)

    async def emit_log(
        self,
        task_id: str,
        message: str,
        level: str = "info",
    ) -> None:
        """
        Emit a log message.

        Args:
            task_id: The task identifier
            message: Log message
            level: Log level (info, warning, error, debug)
        """
        await self.emit(task_id, "log", {"message": message, "level": level})

    async def emit_complete(
        self,
        task_id: str,
        success: bool,
        message: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit a completion event.

        Args:
            task_id: The task identifier
            success: Whether the task succeeded
            message: Completion message
            result: Optional result data
        """
        self._task_status[task_id] = (
            ProgressStatus.COMPLETED if success else ProgressStatus.FAILED
        )

        data = {
            "success": success,
            "message": message,
        }
        if result:
            data["result"] = result

        await self.emit(task_id, "complete", data)

    async def emit_error(
        self,
        task_id: str,
        error: str,
        suggestion: str | None = None,
    ) -> None:
        """
        Emit an error event.

        Args:
            task_id: The task identifier
            error: Error message
            suggestion: Optional suggestion for fixing the error
        """
        self._task_status[task_id] = ProgressStatus.FAILED

        data = {"error": error}
        if suggestion:
            data["suggestion"] = suggestion

        await self.emit(task_id, "error", data)

    async def subscribe(self, task_id: str) -> AsyncGenerator[str, None]:
        """
        Subscribe to events for a task.

        Yields SSE-formatted strings until the task completes.

        Args:
            task_id: The task identifier

        Yields:
            SSE-formatted event strings
        """
        if task_id not in self._queues:
            # Task doesn't exist, yield error and stop
            error_data = json.dumps({"error": "Task not found"})
            yield f"event: error\ndata: {error_data}\n\n"
            return

        queue = self._queues[task_id]
        self._task_status[task_id] = ProgressStatus.RUNNING

        try:
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Format as SSE
                    event_data = json.dumps(event.data)
                    yield f"event: {event.event_type}\ndata: {event_data}\n\n"

                    # Stop on completion events
                    if event.event_type in ("complete", "error"):
                        break

                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"

        except asyncio.CancelledError:
            logger.debug(f"SSE subscription cancelled for task {task_id}")
            raise
        finally:
            # Cleanup after subscription ends
            self._cleanup_task(task_id)

    def _cleanup_task(self, task_id: str) -> None:
        """Clean up task resources."""
        if task_id in self._queues:
            del self._queues[task_id]
            logger.debug(f"Cleaned up progress queue for task: {task_id}")

    def get_status(self, task_id: str) -> ProgressStatus | None:
        """Get the current status of a task."""
        return self._task_status.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Returns True if the task was cancelled, False if not found.
        """
        if task_id in self._queues:
            self._task_status[task_id] = ProgressStatus.CANCELLED
            # Put a cancellation event in the queue
            asyncio.create_task(
                self.emit(
                    task_id,
                    "complete",
                    {"success": False, "message": "Task cancelled by user"},
                )
            )
            return True
        return False


# Global progress emitter instance
progress_emitter = ProgressEmitter()
