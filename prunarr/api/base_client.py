"""
Base API client class providing common functionality for all API integrations.

This module provides an abstract base class that standardizes API client initialization,
caching, and common operations across Radarr, Sonarr, and Tautulli integrations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from prunarr.logger import get_logger

# Optional cache manager import
try:
    from prunarr.cache import CacheManager
except ImportError:
    CacheManager = None


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients with standardized caching support.

    This class provides common functionality for all PrunArr API clients, including:
    - Standardized initialization with URL, API key, and optional caching
    - Consistent logging setup and debug mode support
    - Generic caching wrapper for all cached operations
    - Common error handling patterns

    Attributes:
        base_url: Normalized base URL for the API server
        api_key: API key for authentication
        cache_manager: Optional cache manager for performance optimization
        logger: Logger instance for this client
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        cache_manager: Optional["CacheManager"] = None,
        debug: bool = False,
        log_level: str = "ERROR",
    ) -> None:
        """
        Initialize the base API client with connection details.

        Args:
            url: Base URL of the API server
            api_key: API key for authentication
            cache_manager: Optional cache manager for performance optimization
            debug: Enable debug logging
            log_level: Minimum log level to display (DEBUG, INFO, WARNING, ERROR)
        """
        self.base_url = url.rstrip("/")
        self.api_key = api_key
        self.cache_manager = cache_manager
        self.logger = get_logger(self._get_logger_name(), debug=debug, log_level=log_level)

        # Initialize the underlying API client (implemented by subclass)
        self._initialize_client()

        self.logger.debug(f"Initialized {self.__class__.__name__} client: {self.base_url}")

    @abstractmethod
    def _get_logger_name(self) -> str:
        """
        Get the logger name for this API client.

        Returns:
            Logger name (e.g., "prunarr.radarr")
        """

    @abstractmethod
    def _initialize_client(self) -> None:
        """
        Initialize the underlying API client library.

        This method should create the actual API client instance (e.g., pyarr client)
        and store it in the appropriate instance variable.
        """
