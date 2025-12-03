"""
Extractors Module

This module contains extractors for retrieving content from Atlassian products.
Each extractor is responsible for:
- Authenticating with the source system
- Retrieving content via API
- Downloading attachments
- Saving raw data to disk
"""

from atlassian_migration_tool.extractors.base_extractor import BaseExtractor
from atlassian_migration_tool.extractors.jira_extractor import JiraExtractor

__all__ = [
    "BaseExtractor",
    "JiraExtractor",
]
