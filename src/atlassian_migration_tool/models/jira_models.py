"""
Jira Data Models

Pydantic models for representing Jira content in a structured way.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class JiraAttachment(BaseModel):
    """Represents a Jira attachment."""

    id: str
    filename: str
    mime_type: str = Field(alias='mimeType')
    size: int
    created: str
    author: str
    local_path: Path | None = None

    class Config:
        populate_by_name = True


class JiraComment(BaseModel):
    """Represents a comment on a Jira issue."""

    id: str
    author: str
    created: str
    updated: str | None = None
    body: str


class JiraIssue(BaseModel):
    """Represents a Jira issue."""

    id: str
    key: str
    summary: str
    description: str | None = None
    issue_type: str = Field(alias='issueType')
    status: str
    priority: str | None = None
    assignee: str | None = None
    reporter: str
    created: str
    updated: str
    project_key: str = Field(alias='projectKey')
    parent_key: str | None = Field(None, alias='parentKey')
    labels: list[str] = Field(default_factory=list)
    attachments: list[JiraAttachment] = Field(default_factory=list)
    comments: list[JiraComment] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict, alias='customFields')
    local_path: Path | None = None

    class Config:
        populate_by_name = True


class JiraProject(BaseModel):
    """Represents a Jira project."""

    key: str
    name: str
    type: str
    description: str | None = None
    issues: list[JiraIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=datetime.now)

    def get_issue_count(self) -> int:
        """Get total number of issues."""
        return len(self.issues)

    def get_issue_by_key(self, key: str) -> JiraIssue | None:
        """Find an issue by its key."""
        for issue in self.issues:
            if issue.key == key:
                return issue
        return None


class JiraExtractionResult(BaseModel):
    """Represents the result of a Jira extraction operation."""

    projects: list[JiraProject]
    extraction_date: datetime = Field(default_factory=datetime.now)
    config: dict[str, Any]
    statistics: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
