"""
Base Transformer Class

Abstract base class for all transformers providing common functionality.
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class BaseTransformer(ABC):
    """
    Abstract base class for content transformers.

    All transformers should inherit from this class and implement the required methods.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the transformer.

        Args:
            config: Configuration dictionary for the transformer
        """
        self.config = config
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def transform(self, input_data: Any) -> Any:
        """
        Transform input data to output format.

        Args:
            input_data: Data to transform

        Returns:
            Transformed data
        """
        pass

    @abstractmethod
    def validate(self, transformed_data: Any) -> bool:
        """
        Validate transformed data.

        Args:
            transformed_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        pass
