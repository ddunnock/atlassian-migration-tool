"""
Confluence Data Models

Pydantic models for representing Confluence content in a structured way.
These models provide type safety, validation, and easy serialization.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator


class ConfluenceAttachment(BaseModel):
    """Represents a Confluence attachment."""

    id: str
    title: str
    media_type: str = Field(alias='mediaType')
    file_size: int = Field(alias='fileSize')
    created: str
    created_by: str = Field(alias='createdBy')
    local_path: Optional[Path] = None
    download_url: Optional[str] = None

    class Config:
        populate_by_name = True


class ConfluenceComment(BaseModel):
    """Represents a comment on a Confluence page."""

    id: str
    author: str
    created: str
    content: str
    parent_id: Optional[str] = None


class ConfluencePage(BaseModel):
    """
    Represents a Confluence page with all its content and metadata.
    """

    id: str
    title: str
    content: str
    space_key: str = Field(alias='spaceKey')
    version: int
    created: str
    last_updated: str = Field(alias='lastUpdated')
    creator: str
    last_modifier: str = Field(alias='lastModifier')
    labels: List[str] = Field(default_factory=list)
    attachments: List[ConfluenceAttachment] = Field(default_factory=list)
    comments: List[ConfluenceComment] = Field(default_factory=list)
    children: List['ConfluencePage'] = Field(default_factory=list)
    parent_id: Optional[str] = None
    local_path: Optional[Path] = None
    status: str = "current"

    class Config:
        populate_by_name = True

    @validator('created', 'last_updated')
    def validate_date(cls, v):
        """Ensure dates are in ISO format."""
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    def get_hierarchy_path(self) -> List[str]:
        """
        Get the hierarchy path from root to this page.

        Returns:
            List of page titles representing the path
        """
        path = [self.title]
        # This would be implemented to traverse up the parent chain
        return path

    def has_children(self) -> bool:
        """Check if page has child pages."""
        return len(self.children) > 0

    def get_all_attachments(self) -> List[ConfluenceAttachment]:
        """Get all attachments including from child pages."""
        all_attachments = list(self.attachments)
        for child in self.children:
            all_attachments.extend(child.get_all_attachments())
        return all_attachments

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(by_alias=True, exclude_none=True)


class ConfluenceSpace(BaseModel):
    """
    Represents a complete Confluence space with all its pages.
    """

    key: str
    name: str
    type: str
    description: Optional[str] = None
    homepage_id: Optional[str] = Field(None, alias='homepageId')
    pages: List[ConfluencePage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True

    def get_page_count(self) -> int:
        """Get total number of pages (including nested)."""
        def count_pages(pages: List[ConfluencePage]) -> int:
            count = len(pages)
            for page in pages:
                count += count_pages(page.children)
            return count

        return count_pages(self.pages)

    def get_all_pages(self) -> List[ConfluencePage]:
        """Get flat list of all pages."""
        def flatten_pages(pages: List[ConfluencePage]) -> List[ConfluencePage]:
            flat = []
            for page in pages:
                flat.append(page)
                flat.extend(flatten_pages(page.children))
            return flat

        return flatten_pages(self.pages)

    def get_page_by_id(self, page_id: str) -> Optional[ConfluencePage]:
        """Find a page by its ID."""
        for page in self.get_all_pages():
            if page.id == page_id:
                return page
        return None

    def get_page_by_title(self, title: str) -> Optional[ConfluencePage]:
        """Find a page by its title."""
        for page in self.get_all_pages():
            if page.title == title:
                return page
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get space statistics."""
        all_pages = self.get_all_pages()
        all_attachments = []
        all_comments = []

        for page in all_pages:
            all_attachments.extend(page.attachments)
            all_comments.extend(page.comments)

        return {
            'total_pages': len(all_pages),
            'total_attachments': len(all_attachments),
            'total_comments': len(all_comments),
            'total_labels': len(set(
                label for page in all_pages for label in page.labels
            )),
            'content_size_bytes': sum(len(page.content) for page in all_pages),
        }


class ConfluenceExtractionResult(BaseModel):
    """
    Represents the result of a Confluence extraction operation.
    """

    spaces: List[ConfluenceSpace]
    extraction_date: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any]
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def calculate_statistics(self):
        """Calculate overall statistics."""
        self.statistics = {
            'total_spaces': len(self.spaces),
            'total_pages': sum(space.get_page_count() for space in self.spaces),
            'total_attachments': sum(
                len(space.get_all_pages()[0].get_all_attachments())
                if space.get_all_pages() else 0
                for space in self.spaces
            ),
            'errors': len(self.errors),
            'warnings': len(self.warnings),
        }

    def get_space_by_key(self, key: str) -> Optional[ConfluenceSpace]:
        """Find a space by its key."""
        for space in self.spaces:
            if space.key == key:
                return space
        return None


# Example usage and validation
if __name__ == "__main__":
    # Create a sample page
    page = ConfluencePage(
        id="123456",
        title="Example Page",
        content="<p>This is example content</p>",
        spaceKey="DOCS",
        version=1,
        created="2024-01-01T00:00:00Z",
        lastUpdated="2024-01-02T00:00:00Z",
        creator="John Doe",
        lastModifier="Jane Smith",
        labels=["documentation", "example"],
    )

    # Add an attachment
    attachment = ConfluenceAttachment(
        id="789",
        title="diagram.png",
        mediaType="image/png",
        fileSize=1024000,
        created="2024-01-01T00:00:00Z",
        createdBy="John Doe",
    )
    page.attachments.append(attachment)

    # Add a comment
    comment = ConfluenceComment(
        id="456",
        author="Jane Smith",
        created="2024-01-02T00:00:00Z",
        content="Great documentation!",
    )
    page.comments.append(comment)

    # Create a space
    space = ConfluenceSpace(
        key="DOCS",
        name="Documentation",
        type="global",
        pages=[page],
    )

    # Print statistics
    stats = space.get_statistics()
    print(f"Space statistics: {stats}")

    # Export to JSON
    print(f"\nPage JSON:\n{page.model_dump_json(indent=2)}")