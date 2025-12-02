"""
Models Module

This module contains Pydantic data models for representing content from
various systems in a type-safe, validated way.
"""

from atlassian_migration_tool.models.confluence_models import (
    ConfluenceAttachment,
    ConfluenceComment,
    ConfluencePage,
    ConfluenceSpace,
    ConfluenceExtractionResult,
)

from atlassian_migration_tool.models.jira_models import (
    JiraAttachment,
    JiraComment,
    JiraIssue,
    JiraProject,
    JiraExtractionResult,
)

__all__ = [
    # Confluence models
    "ConfluenceAttachment",
    "ConfluenceComment",
    "ConfluencePage",
    "ConfluenceSpace",
    "ConfluenceExtractionResult",

    # Jira models
    "JiraAttachment",
    "JiraComment",
    "JiraIssue",
    "JiraProject",
    "JiraExtractionResult",
]