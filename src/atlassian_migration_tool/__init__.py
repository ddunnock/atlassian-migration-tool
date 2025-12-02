"""
Atlassian Migration Tool

A comprehensive Python package for migrating content from Atlassian Confluence
and Jira to open-source alternatives (Wiki.js, OpenProject, GitLab).

Example:
    >>> from atlassian_migration_tool import ConfluenceExtractor
    >>> from atlassian_migration_tool.utils import load_config
    >>>
    >>> config = load_config()
    >>> extractor = ConfluenceExtractor(config['atlassian']['confluence'])
    >>> spaces = extractor.list_spaces()
"""

__version__ = "0.1.0"
__author__ = "Your Organization"
__license__ = "MIT"

# Import main classes for easy access
from atlassian_migration_tool.extractors import (
    ConfluenceExtractor,
    JiraExtractor,
)

from atlassian_migration_tool.transformers import (
    ConfluenceToMarkdownTransformer,
    JiraToOpenProjectTransformer,
    ContentToGitLabTransformer,
)

from atlassian_migration_tool.uploaders import (
    WikiJSUploader,
    OpenProjectUploader,
    GitLabUploader,
)

from atlassian_migration_tool.models import (
    ConfluencePage,
    ConfluenceSpace,
    JiraIssue,
    JiraProject,
)

from atlassian_migration_tool.utils import (
    load_config,
    setup_logger,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",

    # Extractors
    "ConfluenceExtractor",
    "JiraExtractor",

    # Transformers
    "ConfluenceToMarkdownTransformer",
    "JiraToOpenProjectTransformer",
    "ContentToGitLabTransformer",

    # Uploaders
    "WikiJSUploader",
    "OpenProjectUploader",
    "GitLabUploader",

    # Models
    "ConfluencePage",
    "ConfluenceSpace",
    "JiraIssue",
    "JiraProject",

    # Utils
    "load_config",
    "setup_logger",
]