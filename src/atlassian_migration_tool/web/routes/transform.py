"""
Transform API Routes

Handles transformation operations with progress streaming.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from atlassian_migration_tool.web.services import progress_emitter, task_manager
from atlassian_migration_tool.web.services.task_manager import TaskType

router = APIRouter()


class TransformRequest(BaseModel):
    """Request model for starting transformation."""

    input_dir: str = "data/extracted"
    output_dir: str = "data/transformed"
    target: str = "openproject"  # openproject or gitlab


class TransformResponse(BaseModel):
    """Response model for transformation start."""

    success: bool
    task_id: str | None = None
    message: str
    error: str | None = None
    suggestion: str | None = None


class TransformStatusResponse(BaseModel):
    """Response model for transformation status."""

    task_id: str
    status: str
    progress: int | None = None
    message: str | None = None
    result: dict[str, Any] | None = None


def run_transformation(
    task_id: str,
    emit_progress: Callable,
    emit_log: Callable,
    is_cancelled: Callable,
    input_dir: str,
    output_dir: str,
    target: str,
) -> dict[str, Any]:
    """
    Execute transformation in a background thread.

    This function is called by the task manager with progress callbacks.
    """
    import json
    from pathlib import Path

    emit_log("Starting transformation...")
    emit_progress(0, "Scanning extracted data...")

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    # Find all extracted projects
    jira_path = input_path / "jira"
    if not jira_path.exists():
        raise ValueError("No Jira data found in input directory")

    project_dirs = [d for d in jira_path.iterdir() if d.is_dir()]
    if not project_dirs:
        raise ValueError("No project data found in input directory")

    results = {
        "projects": [],
        "total_items_transformed": 0,
        "output_dir": str(output_path),
    }

    total_projects = len(project_dirs)
    emit_log(f"Found {total_projects} project(s) to transform")

    for idx, project_dir in enumerate(project_dirs):
        if is_cancelled():
            emit_log("Transformation cancelled by user", "warning")
            break

        project_key = project_dir.name
        progress = int((idx / total_projects) * 100)
        emit_progress(
            progress,
            f"Transforming: {project_key}",
            current=idx + 1,
            total=total_projects,
        )
        emit_log(f"Transforming project: {project_key}")

        try:
            # Create output directory structure
            project_output = output_path / target / project_key
            project_output.mkdir(parents=True, exist_ok=True)

            # Find all JSON files with extracted data
            json_files = list(project_dir.rglob("*.json"))
            items_transformed = 0

            for json_file in json_files:
                try:
                    with open(json_file) as f:
                        data = json.load(f)

                    # Transform based on target
                    if target == "openproject":
                        transformed = transform_for_openproject(data)
                    elif target == "gitlab":
                        transformed = transform_for_gitlab(data)
                    else:
                        transformed = data  # Pass through

                    # Save transformed data
                    rel_path = json_file.relative_to(project_dir)
                    output_file = project_output / rel_path
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                    with open(output_file, "w") as f:
                        json.dump(transformed, f, indent=2, default=str)

                    items_transformed += 1

                except Exception as e:
                    emit_log(f"  Warning: Failed to transform {json_file.name}: {e}", "warning")

            results["projects"].append({
                "key": project_key,
                "items": items_transformed,
                "status": "success",
            })
            results["total_items_transformed"] += items_transformed

            emit_log(f"  Transformed {items_transformed} files from {project_key}")

        except Exception as e:
            emit_log(f"  Failed to transform {project_key}: {e}", "error")
            results["projects"].append({
                "key": project_key,
                "items": 0,
                "status": "failed",
                "error": str(e),
            })

    emit_progress(100, "Transformation complete")
    emit_log(f"Transformation complete. Total items: {results['total_items_transformed']}")

    return results


def transform_for_openproject(data: Any) -> Any:
    """Transform data for OpenProject format."""
    # TODO: Implement full transformation logic
    # For now, pass through with metadata
    if isinstance(data, dict):
        return {
            "_transformed_for": "openproject",
            "_original_format": "jira",
            **data,
        }
    return data


def transform_for_gitlab(data: Any) -> Any:
    """Transform data for GitLab format."""
    # TODO: Implement full transformation logic
    # For now, pass through with metadata
    if isinstance(data, dict):
        return {
            "_transformed_for": "gitlab",
            "_original_format": "jira",
            **data,
        }
    return data


@router.post("", response_model=TransformResponse)
async def start_transformation(request: TransformRequest):
    """
    Start transformation of extracted data.

    Returns a task_id that can be used to track progress via SSE.
    """
    input_path = Path(request.input_dir)

    if not input_path.exists():
        return TransformResponse(
            success=False,
            message="Input directory not found",
            error=f"Directory does not exist: {request.input_dir}",
            suggestion="Run extraction first to populate the input directory",
        )

    if request.target not in ["openproject", "gitlab"]:
        return TransformResponse(
            success=False,
            message="Invalid target",
            error=f"Unknown target: {request.target}",
            suggestion="Use 'openproject' or 'gitlab' as target",
        )

    try:
        task_id = await task_manager.start_task(
            task_type=TaskType.TRANSFORM,
            func=run_transformation,
            params={
                "input_dir": request.input_dir,
                "output_dir": request.output_dir,
                "target": request.target,
            },
        )

        return TransformResponse(
            success=True,
            task_id=task_id,
            message=f"Transformation started for target: {request.target}",
        )

    except Exception as e:
        logger.exception("Failed to start transformation")
        return TransformResponse(
            success=False,
            message="Failed to start transformation",
            error=str(e),
        )


@router.get("/progress/{task_id}")
async def transformation_progress(task_id: str):
    """
    Stream transformation progress via Server-Sent Events.
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


@router.get("/status/{task_id}", response_model=TransformStatusResponse)
async def transformation_status(task_id: str):
    """Get the current status of a transformation task."""
    task_info = task_manager.get_task_info(task_id)

    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")

    return TransformStatusResponse(
        task_id=task_id,
        status=task_info.status.value,
        result=task_info.result,
        message=task_info.error if task_info.error else None,
    )


@router.post("/cancel/{task_id}")
async def cancel_transformation(task_id: str):
    """Cancel a running transformation task."""
    if task_manager.cancel_task(task_id):
        return {"success": True, "message": "Cancellation requested"}
    raise HTTPException(status_code=404, detail="Task not found or already completed")
