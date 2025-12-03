"""
Connection Testing API Routes

Handles testing connections to Jira and target systems.
"""

from typing import Any

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from atlassian_migration_tool.utils.config_loader import load_config

router = APIRouter()


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""

    system: str
    success: bool
    message: str
    details: dict[str, Any] | None = None
    suggestion: str | None = None


class ConnectionTestResponse(BaseModel):
    """Response for connection test requests."""

    results: list[ConnectionTestResult]


class JiraProject(BaseModel):
    """Jira project information."""

    key: str
    name: str
    id: str | None = None
    project_type: str | None = None


class JiraProjectsResponse(BaseModel):
    """Response for Jira projects listing."""

    success: bool
    projects: list[JiraProject] = []
    error: str | None = None
    suggestion: str | None = None


@router.post("/test/jira", response_model=ConnectionTestResult)
async def test_jira_connection():
    """Test connection to Jira."""
    try:
        config = load_config()
        jira_config = config.get("atlassian", {}).get("jira", {})

        if not jira_config.get("url"):
            return ConnectionTestResult(
                system="Jira",
                success=False,
                message="Jira URL not configured",
                suggestion="Configure the Jira URL in your config.yaml file",
            )

        from atlassian_migration_tool.extractors import JiraExtractor

        extractor = JiraExtractor(jira_config)
        projects = extractor.list_projects()

        return ConnectionTestResult(
            system="Jira",
            success=True,
            message=f"Connected successfully. Found {len(projects)} accessible projects.",
            details={
                "url": jira_config.get("url"),
                "username": jira_config.get("username"),
                "project_count": len(projects),
            },
        )

    except Exception as e:
        error_msg = str(e).lower()

        # Provide helpful suggestions based on error type
        suggestion = None
        if "401" in error_msg or "unauthorized" in error_msg:
            suggestion = "Check your API token. For Jira Cloud, use an API token from id.atlassian.com"
        elif "403" in error_msg or "forbidden" in error_msg:
            suggestion = "Your account may not have permission to access this Jira instance"
        elif "404" in error_msg or "not found" in error_msg:
            suggestion = "Check the Jira URL is correct and accessible"
        elif "connection" in error_msg or "timeout" in error_msg:
            suggestion = "Check your network connection and that the Jira server is reachable"

        logger.error(f"Jira connection test failed: {e}")
        return ConnectionTestResult(
            system="Jira",
            success=False,
            message=f"Connection failed: {str(e)}",
            suggestion=suggestion,
        )


@router.post("/test/openproject", response_model=ConnectionTestResult)
async def test_openproject_connection():
    """Test connection to OpenProject."""
    try:
        config = load_config()
        op_config = config.get("targets", {}).get("openproject", {})

        if not op_config.get("enabled", False):
            return ConnectionTestResult(
                system="OpenProject",
                success=False,
                message="OpenProject is not enabled",
                suggestion="Enable OpenProject in targets configuration",
            )

        if not op_config.get("url"):
            return ConnectionTestResult(
                system="OpenProject",
                success=False,
                message="OpenProject URL not configured",
                suggestion="Configure the OpenProject URL in your config.yaml file",
            )

        # TODO: Implement actual connection test
        return ConnectionTestResult(
            system="OpenProject",
            success=True,
            message="Connection test not yet implemented",
            details={"url": op_config.get("url")},
        )

    except Exception as e:
        logger.error(f"OpenProject connection test failed: {e}")
        return ConnectionTestResult(
            system="OpenProject",
            success=False,
            message=f"Connection failed: {str(e)}",
        )


@router.post("/test/gitlab", response_model=ConnectionTestResult)
async def test_gitlab_connection():
    """Test connection to GitLab."""
    try:
        config = load_config()
        gl_config = config.get("targets", {}).get("gitlab", {})

        if not gl_config.get("enabled", False):
            return ConnectionTestResult(
                system="GitLab",
                success=False,
                message="GitLab is not enabled",
                suggestion="Enable GitLab in targets configuration",
            )

        if not gl_config.get("url"):
            return ConnectionTestResult(
                system="GitLab",
                success=False,
                message="GitLab URL not configured",
                suggestion="Configure the GitLab URL in your config.yaml file",
            )

        # TODO: Implement actual connection test
        return ConnectionTestResult(
            system="GitLab",
            success=True,
            message="Connection test not yet implemented",
            details={"url": gl_config.get("url")},
        )

    except Exception as e:
        logger.error(f"GitLab connection test failed: {e}")
        return ConnectionTestResult(
            system="GitLab",
            success=False,
            message=f"Connection failed: {str(e)}",
        )


@router.post("/test/all", response_model=ConnectionTestResponse)
async def test_all_connections():
    """Test connections to all configured systems."""
    results = []

    # Test Jira
    jira_result = await test_jira_connection()
    results.append(jira_result)

    # Test enabled targets
    try:
        config = load_config()
        targets = config.get("targets", {})

        if targets.get("openproject", {}).get("enabled", False):
            op_result = await test_openproject_connection()
            results.append(op_result)

        if targets.get("gitlab", {}).get("enabled", False):
            gl_result = await test_gitlab_connection()
            results.append(gl_result)

    except Exception as e:
        logger.error(f"Failed to load config for connection tests: {e}")

    return ConnectionTestResponse(results=results)


@router.get("/jira/projects", response_model=JiraProjectsResponse)
async def list_jira_projects():
    """List available Jira projects."""
    try:
        config = load_config()
        jira_config = config.get("atlassian", {}).get("jira", {})

        if not jira_config.get("url"):
            return JiraProjectsResponse(
                success=False,
                error="Jira not configured",
                suggestion="Configure Jira connection in settings first",
            )

        from atlassian_migration_tool.extractors import JiraExtractor

        extractor = JiraExtractor(jira_config)
        projects_data = extractor.list_projects()

        projects = [
            JiraProject(
                key=p.get("key", ""),
                name=p.get("name", ""),
                id=p.get("id"),
                project_type=p.get("projectTypeKey"),
            )
            for p in projects_data
        ]

        return JiraProjectsResponse(success=True, projects=projects)

    except Exception as e:
        error_msg = str(e).lower()
        suggestion = None

        if "401" in error_msg or "unauthorized" in error_msg:
            suggestion = "Authentication failed. Check your API token."
        elif "connection" in error_msg:
            suggestion = "Cannot reach Jira server. Check the URL and network connection."

        logger.error(f"Failed to list Jira projects: {e}")
        return JiraProjectsResponse(
            success=False,
            error=f"Failed to list projects: {str(e)}",
            suggestion=suggestion,
        )
