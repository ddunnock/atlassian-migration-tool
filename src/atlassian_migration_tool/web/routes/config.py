"""
Configuration API Routes

Handles loading, saving, and validating configuration files.
"""

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from atlassian_migration_tool.utils.config_loader import load_config

router = APIRouter()


class ConfigResponse(BaseModel):
    """Response model for configuration data."""

    success: bool
    config: dict[str, Any] | None = None
    error: str | None = None
    suggestion: str | None = None


class ConfigSaveRequest(BaseModel):
    """Request model for saving configuration."""

    config: dict[str, Any]
    path: str = "config/config.yaml"


class ValidationResponse(BaseModel):
    """Response model for configuration validation."""

    valid: bool
    errors: list[str] = []
    warnings: list[str] = []


@router.get("", response_model=ConfigResponse)
async def get_config(path: str = "config/config.yaml"):
    """
    Load and return the current configuration.

    Args:
        path: Path to the configuration file (default: config/config.yaml)
    """
    try:
        config = load_config(path)
        return ConfigResponse(success=True, config=config)
    except FileNotFoundError:
        return ConfigResponse(
            success=False,
            error="Configuration file not found",
            suggestion=f"Create a config file at '{path}' or copy from config.example.yaml",
        )
    except yaml.YAMLError as e:
        return ConfigResponse(
            success=False,
            error=f"Invalid YAML syntax: {str(e)}",
            suggestion="Check your configuration file for YAML formatting errors",
        )
    except Exception as e:
        return ConfigResponse(
            success=False,
            error=f"Failed to load configuration: {str(e)}",
            suggestion="Check the configuration file format and permissions",
        )


@router.post("", response_model=ConfigResponse)
async def save_config(request: ConfigSaveRequest):
    """
    Save configuration to file.

    Args:
        request: Configuration data and target path
    """
    try:
        config_path = Path(request.path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(request.config, f, default_flow_style=False, sort_keys=False)

        return ConfigResponse(success=True, config=request.config)
    except PermissionError:
        return ConfigResponse(
            success=False,
            error="Permission denied",
            suggestion=f"Check write permissions for '{request.path}'",
        )
    except Exception as e:
        return ConfigResponse(
            success=False,
            error=f"Failed to save configuration: {str(e)}",
        )


@router.get("/validate", response_model=ValidationResponse)
async def validate_config(path: str = "config/config.yaml"):
    """
    Validate the configuration file.

    Args:
        path: Path to the configuration file
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        config = load_config(path)

        # Check required sections
        required_sections = ["atlassian", "targets", "migration"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: '{section}'")

        # Check Jira configuration
        if "atlassian" in config:
            jira = config["atlassian"].get("jira", {})
            if not jira.get("url"):
                errors.append("Jira URL is not configured")
            if not jira.get("username"):
                errors.append("Jira username is not configured")
            if not jira.get("api_token") or jira.get("api_token", "").startswith("${"):
                warnings.append(
                    "Jira API token may not be set (uses environment variable)"
                )

        # Check target systems
        if "targets" in config:
            targets = config["targets"]
            enabled_targets = [
                name for name, cfg in targets.items() if cfg.get("enabled", False)
            ]
            if not enabled_targets:
                warnings.append("No target systems are enabled")

        return ValidationResponse(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    except FileNotFoundError:
        return ValidationResponse(
            valid=False, errors=[f"Configuration file not found: {path}"]
        )
    except Exception as e:
        return ValidationResponse(valid=False, errors=[f"Validation failed: {str(e)}"])


@router.get("/example")
async def get_example_config():
    """Return the example configuration file content."""
    try:
        example_path = Path("config/config.example.yaml")
        if example_path.exists():
            with open(example_path) as f:
                return {"success": True, "content": f.read()}
        return {"success": False, "error": "Example configuration not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
