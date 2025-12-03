"""
Jira to OpenProject Transformer

Transforms Jira issues to OpenProject work packages.
"""

from typing import Any

from loguru import logger

from atlassian_migration_tool.models.jira_models import JiraIssue
from atlassian_migration_tool.transformers.base_transformer import BaseTransformer


class JiraToOpenProjectTransformer(BaseTransformer):
    """Transform Jira issues to OpenProject work packages."""

    def transform(self, issue: JiraIssue) -> dict[str, Any]:
        """Transform Jira issue to OpenProject format."""
        logger.info(f"Transforming issue: {issue.key}")

        # TODO: Implement transformation
        work_package = {
            "subject": issue.summary,
            "description": issue.description,
            "status": issue.status,
            "priority": issue.priority,
        }

        return work_package

    def validate(self, transformed_data: dict[str, Any]) -> bool:
        """Validate transformed work package."""
        required_fields = ["subject", "description"]
        return all(field in transformed_data for field in required_fields)
