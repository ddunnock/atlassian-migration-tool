"""
Upload API Routes

Handles upload operations to target systems with progress streaming.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from atlassian_migration_tool.utils.config_loader import load_config
from atlassian_migration_tool.web.services import progress_emitter, task_manager
from atlassian_migration_tool.web.services.task_manager import TaskType

router = APIRouter()


class UploadRequest(BaseModel):
    """Request model for starting upload."""

    target: str  # openproject or gitlab
    input_dir: str = "data/transformed"
    dry_run: bool = False
    create_projects: bool = True
    update_existing: bool = True


class UploadResponse(BaseModel):
    """Response model for upload start."""

    success: bool
    task_id: str | None = None
    message: str
    error: str | None = None
    suggestion: str | None = None


class UploadStatusResponse(BaseModel):
    """Response model for upload status."""

    task_id: str
    status: str
    progress: int | None = None
    message: str | None = None
    result: dict[str, Any] | None = None


def run_upload(
    task_id: str,
    emit_progress: Callable,
    emit_log: Callable,
    is_cancelled: Callable,
    target: str,
    input_dir: str,
    dry_run: bool,
    create_projects: bool,
    update_existing: bool,
) -> dict[str, Any]:
    """
    Execute upload in a background thread.

    This function is called by the task manager with progress callbacks.
    """
    import json
    from pathlib import Path

    emit_log(f"Starting upload to {target}...")
    if dry_run:
        emit_log("DRY RUN MODE - No changes will be made to target system", "warning")

    emit_progress(0, "Scanning transformed data...")

    input_path = Path(input_dir)

    if not input_path.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    # Find transformed data for the target
    target_path = input_path / target
    if not target_path.exists():
        raise ValueError(f"No transformed data found for target: {target}")

    project_dirs = [d for d in target_path.iterdir() if d.is_dir()]
    if not project_dirs:
        raise ValueError("No project data found in input directory")

    results = {
        "target": target,
        "dry_run": dry_run,
        "projects": [],
        "total_items_uploaded": 0,
        "total_items_skipped": 0,
        "total_errors": 0,
    }

    total_projects = len(project_dirs)
    emit_log(f"Found {total_projects} project(s) to upload")

    # Load target configuration
    config = load_config()
    target_config = config.get("targets", {}).get(target, {})

    if not target_config.get("enabled", False):
        raise ValueError(f"Target {target} is not enabled in configuration")

    for idx, project_dir in enumerate(project_dirs):
        if is_cancelled():
            emit_log("Upload cancelled by user", "warning")
            break

        project_key = project_dir.name
        progress = int((idx / total_projects) * 100)
        emit_progress(
            progress,
            f"Uploading: {project_key}",
            current=idx + 1,
            total=total_projects,
        )
        emit_log(f"Uploading project: {project_key}")

        project_result = {
            "key": project_key,
            "items_uploaded": 0,
            "items_skipped": 0,
            "errors": 0,
            "status": "success",
        }

        try:
            # Find all JSON files
            json_files = list(project_dir.rglob("*.json"))

            for json_file in json_files:
                if is_cancelled():
                    break

                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    if dry_run:
                        # Simulate upload
                        emit_log(f"  [DRY RUN] Would upload: {json_file.name}")
                        project_result["items_skipped"] += 1
                    else:
                        # TODO: Implement actual upload logic
                        # For now, just log what would be uploaded
                        if target == "openproject":
                            success = upload_to_openproject(
                                data, target_config, create_projects, update_existing
                            )
                        elif target == "gitlab":
                            success = upload_to_gitlab(
                                data, target_config, create_projects, update_existing
                            )
                        else:
                            success = False

                        if success:
                            project_result["items_uploaded"] += 1
                        else:
                            project_result["items_skipped"] += 1

                except Exception as e:
                    emit_log(f"  Error uploading {json_file.name}: {e}", "error")
                    project_result["errors"] += 1

            results["projects"].append(project_result)
            results["total_items_uploaded"] += project_result["items_uploaded"]
            results["total_items_skipped"] += project_result["items_skipped"]
            results["total_errors"] += project_result["errors"]

            emit_log(
                f"  Completed {project_key}: "
                f"{project_result['items_uploaded']} uploaded, "
                f"{project_result['items_skipped']} skipped, "
                f"{project_result['errors']} errors"
            )

        except Exception as e:
            emit_log(f"  Failed to upload {project_key}: {e}", "error")
            project_result["status"] = "failed"
            project_result["error"] = str(e)
            results["projects"].append(project_result)

    emit_progress(100, "Upload complete")
    emit_log(
        f"Upload complete. "
        f"Uploaded: {results['total_items_uploaded']}, "
        f"Skipped: {results['total_items_skipped']}, "
        f"Errors: {results['total_errors']}"
    )

    return results


def upload_to_openproject(
    data: Any, config: dict[str, Any], create_projects: bool, update_existing: bool
) -> bool:
    """Upload data to OpenProject."""
    # TODO: Implement OpenProject upload
    # This is a placeholder that always returns True
    logger.debug("OpenProject upload not yet implemented")
    return True


def upload_to_gitlab(
    data: Any, config: dict[str, Any], create_projects: bool, update_existing: bool
) -> bool:
    """Upload data to GitLab."""
    # TODO: Implement GitLab upload
    # This is a placeholder that always returns True
    logger.debug("GitLab upload not yet implemented")
    return True


@router.post("/{target}", response_model=UploadResponse)
async def start_upload(target: str, request: UploadRequest):
    """
    Start upload to a target system.

    Returns a task_id that can be used to track progress via SSE.
    """
    if target not in ["openproject", "gitlab"]:
        return UploadResponse(
            success=False,
            message="Invalid target",
            error=f"Unknown target: {target}",
            suggestion="Use 'openproject' or 'gitlab' as target",
        )

    try:
        # Verify target is configured and enabled
        config = load_config()
        target_config = config.get("targets", {}).get(target, {})

        if not target_config.get("enabled", False):
            return UploadResponse(
                success=False,
                message=f"{target.capitalize()} is not enabled",
                error="Target system is disabled in configuration",
                suggestion=f"Enable {target} in your configuration file",
            )

        if not target_config.get("url"):
            return UploadResponse(
                success=False,
                message=f"{target.capitalize()} URL not configured",
                error="Target URL is not set",
                suggestion=f"Configure the {target} URL in settings",
            )

        # Check input directory
        input_path = Path(request.input_dir) / target
        if not input_path.exists():
            return UploadResponse(
                success=False,
                message="No transformed data found",
                error=f"Directory does not exist: {input_path}",
                suggestion="Run transformation for this target first",
            )

        task_id = await task_manager.start_task(
            task_type=TaskType.UPLOAD,
            func=run_upload,
            params={
                "target": target,
                "input_dir": request.input_dir,
                "dry_run": request.dry_run,
                "create_projects": request.create_projects,
                "update_existing": request.update_existing,
            },
        )

        mode = " (DRY RUN)" if request.dry_run else ""
        return UploadResponse(
            success=True,
            task_id=task_id,
            message=f"Upload started to {target.capitalize()}{mode}",
        )

    except Exception as e:
        logger.exception("Failed to start upload")
        return UploadResponse(
            success=False,
            message="Failed to start upload",
            error=str(e),
        )


@router.get("/progress/{task_id}")
async def upload_progress(task_id: str):
    """
    Stream upload progress via Server-Sent Events.
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


@router.get("/status/{task_id}", response_model=UploadStatusResponse)
async def upload_status(task_id: str):
    """Get the current status of an upload task."""
    task_info = task_manager.get_task_info(task_id)

    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")

    return UploadStatusResponse(
        task_id=task_id,
        status=task_info.status.value,
        result=task_info.result,
        message=task_info.error if task_info.error else None,
    )


@router.post("/cancel/{task_id}")
async def cancel_upload(task_id: str):
    """Cancel a running upload task."""
    if task_manager.cancel_task(task_id):
        return {"success": True, "message": "Cancellation requested"}
    raise HTTPException(status_code=404, detail="Task not found or already completed")
