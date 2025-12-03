"""
OpenProject Uploader

Uploads content to OpenProject via REST API.
"""

from typing import Any

from loguru import logger

from atlassian_migration_tool.uploaders.base_uploader import BaseUploader


class OpenProjectUploader(BaseUploader):
    """Upload content to OpenProject."""

    def test_connection(self) -> bool:
        """Test connection to OpenProject."""
        logger.info("Testing OpenProject connection")
        # TODO: Implement connection test
        return True

    def upload(self, content: Any) -> bool:
        """Upload content to OpenProject."""
        logger.info("Uploading to OpenProject")
        # TODO: Implement upload logic
        return True
