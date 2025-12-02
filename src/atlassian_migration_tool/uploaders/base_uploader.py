"""
Base Uploader Class

Abstract base class for all uploaders providing common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from loguru import logger


class BaseUploader(ABC):
    """
    Abstract base class for content uploaders.

    All uploaders should inherit from this class and implement the required methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the uploader.

        Args:
            config: Configuration dictionary for the uploader
        """
        self.config = config
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the target system.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def upload(self, content: Any) -> bool:
        """
        Upload content to the target system.

        Args:
            content: Content to upload

        Returns:
            True if upload successful, False otherwise
        """
        pass