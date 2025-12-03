"""
Status API Routes

Handles status monitoring and log streaming.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from atlassian_migration_tool.web.services import task_manager
from atlassian_migration_tool.web.services.progress_emitter import ProgressStatus
from atlassian_migration_tool.web.services.task_manager import TaskType

router = APIRouter()


class TaskSummary(BaseModel):
    """Summary of a task."""

    task_id: str
    task_type: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None


class SystemStatus(BaseModel):
    """Overall system status."""

    config_loaded: bool
    jira_configured: bool
    targets_configured: list[str]
    extracted_projects: list[str]
    transformed_projects: dict[str, list[str]]
    recent_tasks: list[TaskSummary]


class PipelineStatus(BaseModel):
    """Pipeline status for a project."""

    project: str
    extracted: bool
    extracted_at: str | None = None
    transformed: dict[str, bool] = {}
    transformed_at: dict[str, str | None] = {}
    uploaded: dict[str, bool] = {}
    uploaded_at: dict[str, str | None] = {}


@router.get("", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status."""
    try:
        from atlassian_migration_tool.utils.config_loader import load_config

        config = load_config()
        config_loaded = True
        jira_configured = bool(config.get("atlassian", {}).get("jira", {}).get("url"))

        targets = config.get("targets", {})
        targets_configured = [
            name for name, cfg in targets.items() if cfg.get("enabled", False)
        ]
    except Exception:
        config_loaded = False
        jira_configured = False
        targets_configured = []

    # Check extracted projects
    extracted_path = Path("data/extracted/jira")
    extracted_projects = []
    if extracted_path.exists():
        extracted_projects = [d.name for d in extracted_path.iterdir() if d.is_dir()]

    # Check transformed projects
    transformed_path = Path("data/transformed")
    transformed_projects: dict[str, list[str]] = {}
    if transformed_path.exists():
        for target_dir in transformed_path.iterdir():
            if target_dir.is_dir():
                target_name = target_dir.name
                projects = [d.name for d in target_dir.iterdir() if d.is_dir()]
                if projects:
                    transformed_projects[target_name] = projects

    # Get recent tasks
    all_tasks = task_manager.list_tasks()
    recent_tasks = [
        TaskSummary(
            task_id=t.task_id,
            task_type=t.task_type.value,
            status=t.status.value,
            created_at=t.created_at.isoformat(),
            started_at=t.started_at.isoformat() if t.started_at else None,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
            error=t.error,
        )
        for t in all_tasks[:10]  # Last 10 tasks
    ]

    return SystemStatus(
        config_loaded=config_loaded,
        jira_configured=jira_configured,
        targets_configured=targets_configured,
        extracted_projects=extracted_projects,
        transformed_projects=transformed_projects,
        recent_tasks=recent_tasks,
    )


@router.get("/tasks")
async def list_tasks(
    task_type: str | None = None,
    status: str | None = None,
):
    """List all tasks with optional filtering."""
    filter_type = TaskType(task_type) if task_type else None
    filter_status = ProgressStatus(status) if status else None

    tasks = task_manager.list_tasks(task_type=filter_type, status=filter_status)

    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "task_type": t.task_type.value,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "params": t.params,
                "error": t.error,
                "result": t.result,
            }
            for t in tasks
        ]
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get details of a specific task."""
    task = task_manager.get_task_info(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.task_id,
        "task_type": task.task_type.value,
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "params": task.params,
        "error": task.error,
        "result": task.result,
    }


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    if task_manager.cancel_task(task_id):
        return {"success": True, "message": "Task cancellation requested"}
    raise HTTPException(status_code=404, detail="Task not found or already completed")


@router.get("/pipeline/{project}")
async def get_pipeline_status(project: str):
    """Get pipeline status for a specific project."""
    # Check extraction
    extracted = False
    extracted_at = None
    extracted_path = Path(f"data/extracted/jira/{project}")
    if extracted_path.exists():
        extracted = True
        # Get modification time
        try:
            stat = extracted_path.stat()
            extracted_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except Exception:
            pass

    # Check transformations
    transformed: dict[str, bool] = {}
    transformed_at: dict[str, str | None] = {}

    for target in ["openproject", "gitlab"]:
        target_path = Path(f"data/transformed/{target}/{project}")
        if target_path.exists():
            transformed[target] = True
            try:
                stat = target_path.stat()
                transformed_at[target] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                transformed_at[target] = None
        else:
            transformed[target] = False
            transformed_at[target] = None

    # TODO: Check uploads (would need state tracking)
    uploaded: dict[str, bool] = {}
    uploaded_at: dict[str, str | None] = {}

    return PipelineStatus(
        project=project,
        extracted=extracted,
        extracted_at=extracted_at,
        transformed=transformed,
        transformed_at=transformed_at,
        uploaded=uploaded,
        uploaded_at=uploaded_at,
    )


@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries from log file."""
    log_path = Path("data/logs/migration.log")

    if not log_path.exists():
        return {"logs": [], "message": "Log file not found"}

    try:
        with open(log_path) as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            return {"logs": [line.strip() for line in recent_lines]}
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"logs": [], "error": str(e)}


@router.get("/logs/stream")
async def stream_logs():
    """Stream logs via Server-Sent Events."""

    async def log_generator():
        """Generate SSE events for logs."""
        log_path = Path("data/logs/migration.log")

        # Track file position
        if log_path.exists():
            with open(log_path) as f:
                f.seek(0, 2)  # Go to end
                position = f.tell()
        else:
            position = 0

        while True:
            try:
                if log_path.exists():
                    with open(log_path) as f:
                        f.seek(position)
                        new_lines = f.readlines()
                        position = f.tell()

                        for line in new_lines:
                            line = line.strip()
                            if line:
                                import json
                                data = json.dumps({"log": line})
                                yield f"data: {data}\n\n"

                # Wait before checking again
                await asyncio.sleep(1)

                # Send keepalive
                yield ": keepalive\n\n"

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error streaming logs: {e}")
                await asyncio.sleep(5)

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/cleanup")
async def cleanup_tasks(max_age_seconds: int = 3600):
    """Clean up completed tasks older than max_age_seconds."""
    removed = task_manager.cleanup_completed(max_age_seconds)
    return {"success": True, "removed": removed}
