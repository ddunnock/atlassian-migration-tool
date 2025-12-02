"""
Jira Data Models

Pydantic models for representing Jira content in a structured way.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field


class JiraAttachment(BaseModel):
    """Represents a Jira attachment."""

    id: str
    filename: str
    mime_type: str = Field(alias='mimeType')
    size: int
    created: str
    author: str
    local_path: Optional[Path] = None

    class Config:
        populate_by_name = True


class JiraComment(BaseModel):
    """Represents a comment on a Jira issue."""

    id: str
    author: str
    created: str
    updated: Optional[str] = None
    body: str


class JiraIssue(BaseModel):
    """Represents a Jira issue."""

    id: str
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: str = Field(alias='issueType')
    status: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: str
    created: str
    updated: str
    project_key: str = Field(alias='projectKey')
    parent_key: Optional[str] = Field(None, alias='parentKey')
    labels: List[str] = Field(default_factory=list)
    attachments: List[JiraAttachment] = Field(default_factory=list)
    comments: List[JiraComment] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, alias='customFields')
    local_path: Optional[Path] = None

    class Config:
        populate_by_name = True


class JiraProject(BaseModel):
    """Represents a Jira project."""

    key: str
    name: str
    type: str
    description: Optional[str] = None
    issues: List[JiraIssue] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=datetime.now)

    def get_issue_count(self) -> int:
        """Get total number of issues."""
        return len(self.issues)

    def get_issue_by_key(self, key: str) -> Optional[JiraIssue]:
        """Find an issue by its key."""
        for issue in self.issues:
            if issue.key == key:
                return issue
        return None


class JiraExtractionResult(BaseModel):
    """Represents the result of a Jira extraction operation."""

    projects: List[JiraProject]
    extraction_date: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any]
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)