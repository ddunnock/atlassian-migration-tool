"""
Atlassian Migration Tool

A comprehensive Python package for migrating content from Jira
to open-source alternatives (OpenProject, GitLab).

Example:
    >>> from atlassian_migration_tool import JiraExtractor
    >>> from atlassian_migration_tool.utils import load_config
    >>>
    >>> config = load_config()
    >>> extractor = JiraExtractor(config['atlassian']['jira'])
    >>> projects = extractor.list_projects()
"""

__version__ = "0.1.0"
__author__ = "Your Organization"
__license__ = "MIT"

# Import main classes for easy access
from atlassian_migration_tool.extractors import JiraExtractor
from atlassian_migration_tool.models import (
    JiraIssue,
    JiraProject,
)
from atlassian_migration_tool.transformers import (
    ContentToGitLabTransformer,
    JiraToOpenProjectTransformer,
)
from atlassian_migration_tool.uploaders import (
    GitLabUploader,
    OpenProjectUploader,
    WikiJSUploader,
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
    "JiraExtractor",

    # Transformers
    "JiraToOpenProjectTransformer",
    "ContentToGitLabTransformer",

    # Uploaders
    "WikiJSUploader",
    "OpenProjectUploader",
    "GitLabUploader",

    # Models
    "JiraIssue",
    "JiraProject",

    # Utils
    "load_config",
    "setup_logger",
]
