"""
Base Extractor Class

Abstract base class for all extractors providing common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path
import json
from loguru import logger


class BaseExtractor(ABC):
    """
    Abstract base class for content extractors.

    All extractors should inherit from this class and implement the required methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the extractor.

        Args:
            config: Configuration dictionary for the extractor
        """
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'data/extracted'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the source system.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def extract(self) -> Any:
        """
        Extract content from the source system.

        Returns:
            Extracted content object
        """
        pass

    def _sanitize_filename(self, filename: str) -> str:
        """
        Convert filename to safe filesystem name.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')

        # Limit length
        if len(filename) > 200:
            filename = filename[:200]

        # Ensure we have a valid filename
        if not filename:
            filename = "unnamed"

        return filename

    def _save_json(self, filepath: Path, data: Any):
        """
        Save data as JSON file.

        Args:
            filepath: Path to save JSON file
            data: Data to serialize to JSON
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.debug(f"Saved JSON to {filepath}")

    def _save_text(self, filepath: Path, content: str):
        """
        Save text content to file.

        Args:
            filepath: Path to save text file
            content: Text content to save
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Saved text to {filepath}")

    def _load_json(self, filepath: Path) -> Any:
        """
        Load data from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Loaded data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_text(self, filepath: Path) -> str:
        """
        Load text content from file.

        Args:
            filepath: Path to text file

        Returns:
            File content
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()