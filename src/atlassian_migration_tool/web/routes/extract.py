"""
Extract API Routes

Handles Jira extraction operations with progress streaming.
"""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from atlassian_migration_tool.utils.config_loader import load_config
from atlassian_migration_tool.web.services import progress_emitter, task_manager
from atlassian_migration_tool.web.services.task_manager import TaskType

router = APIRouter()


class ExtractRequest(BaseModel):
    """Request model for starting extraction."""

    projects: list[str]
    output_dir: str = "data/extracted"
    include_attachments: bool = True
    include_comments: bool = True


class ExtractResponse(BaseModel):
    """Response model for extraction start."""

    success: bool
    task_id: str | None = None
    message: str
    error: str | None = None
    suggestion: str | None = None


class ExtractStatusResponse(BaseModel):
    """Response model for extraction status."""

    task_id: str
    status: str
    progress: int | None = None
    message: str | None = None
    result: dict[str, Any] | None = None


def run_jira_extraction(
    task_id: str,
    emit_progress: Callable,
    emit_log: Callable,
    is_cancelled: Callable,
    projects: list[str],
    output_dir: str,
    include_attachments: bool,
    include_comments: bool,
) -> dict[str, Any]:
    """
    Execute Jira extraction in a background thread.

    This function is called by the task manager with progress callbacks.
    """
    from atlassian_migration_tool.extractors import JiraExtractor

    emit_log("Starting Jira extraction...")
    emit_progress(0, "Initializing...")

    try:
        config = load_config()
        jira_config = config.get("atlassian", {}).get("jira", {})
        jira_config["output_dir"] = output_dir

        extractor = JiraExtractor(jira_config)
        emit_log("Connected to Jira")

        results = {
            "projects": [],
            "total_issues": 0,
            "total_attachments": 0,
        }

        total_projects = len(projects)

        for idx, project_key in enumerate(projects):
            if is_cancelled():
                emit_log("Extraction cancelled by user", "warning")
                break

            progress = int((idx / total_projects) * 100)
            emit_progress(
                progress,
                f"Extracting project: {project_key}",
                current=idx + 1,
                total=total_projects,
            )
            emit_log(f"Extracting project: {project_key}")

            try:
                project = extractor.extract_project(project_key)
                issue_count = len(project.issues)

                results["projects"].append({
                    "key": project_key,
                    "issues": issue_count,
                    "status": "success",
                })
                results["total_issues"] += issue_count

                emit_log(f"  Extracted {issue_count} issues from {project_key}")

                # Count by type
                types: dict[str, int] = {}
                for issue in project.issues:
                    t = issue.issue_type
                    types[t] = types.get(t, 0) + 1

                for issue_type, count in sorted(types.items()):
                    emit_log(f"    - {issue_type}: {count}")

            except Exception as e:
                emit_log(f"  Failed to extract {project_key}: {e}", "error")
                results["projects"].append({
                    "key": project_key,
                    "issues": 0,
                    "status": "failed",
                    "error": str(e),
                })

        emit_progress(100, "Extraction complete")
        emit_log(f"Extraction complete. Total issues: {results['total_issues']}")

        return results

    except Exception as e:
        emit_log(f"Extraction failed: {e}", "error")
        raise


@router.post("/jira", response_model=ExtractResponse)
async def start_jira_extraction(request: ExtractRequest):
    """
    Start Jira extraction.

    Returns a task_id that can be used to track progress via SSE.
    """
    if not request.projects:
        return ExtractResponse(
            success=False,
            message="No projects specified",
            error="At least one project key is required",
            suggestion="Provide project keys in the 'projects' field",
        )

    try:
        # Verify configuration
        config = load_config()
        jira_config = config.get("atlassian", {}).get("jira", {})

        if not jira_config.get("url"):
            return ExtractResponse(
                success=False,
                message="Jira not configured",
                error="Jira URL is not set in configuration",
                suggestion="Configure Jira connection in settings first",
            )

        # Start the extraction task
        task_id = await task_manager.start_task(
            task_type=TaskType.EXTRACT,
            func=run_jira_extraction,
            params={
                "projects": request.projects,
                "output_dir": request.output_dir,
                "include_attachments": request.include_attachments,
                "include_comments": request.include_comments,
            },
        )

        return ExtractResponse(
            success=True,
            task_id=task_id,
            message=f"Extraction started for {len(request.projects)} project(s)",
        )

    except Exception as e:
        logger.exception("Failed to start extraction")
        return ExtractResponse(
            success=False,
            message="Failed to start extraction",
            error=str(e),
        )


@router.get("/progress/{task_id}")
async def extraction_progress(task_id: str):
    """
    Stream extraction progress via Server-Sent Events.

    Connect to this endpoint to receive real-time progress updates.
    """
    return StreamingResponse(
        progress_emitter.subscribe(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status/{task_id}", response_model=ExtractStatusResponse)
async def extraction_status(task_id: str):
    """Get the current status of an extraction task."""
    task_info = task_manager.get_task_info(task_id)

    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")

    return ExtractStatusResponse(
        task_id=task_id,
        status=task_info.status.value,
        result=task_info.result,
        message=task_info.error if task_info.error else None,
    )


@router.post("/cancel/{task_id}")
async def cancel_extraction(task_id: str):
    """Cancel a running extraction task."""
    if task_manager.cancel_task(task_id):
        return {"success": True, "message": "Cancellation requested"}
    raise HTTPException(status_code=404, detail="Task not found or already completed")
