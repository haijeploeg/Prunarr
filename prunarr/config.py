"""
Configuration management module for PrunArr CLI.

This module provides configuration loading and validation functionality,
supporting both YAML configuration files and environment variables.
Ensures all required API keys and URLs are properly configured and validated.

The configuration supports:
- Radarr API connection settings
- Sonarr API connection settings
- Tautulli API connection settings
- User tag pattern customization
- Flexible loading from files or environment
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """
    Application settings model with validation for all configuration values.

    This class defines the complete configuration schema for PrunArr,
    including all required API credentials and optional customization settings.
    All settings can be provided via YAML configuration file or environment variables.
    """

    # Radarr connection settings
    radarr_api_key: str = Field(
        ..., description="API key for Radarr instance (required for movie management)"
    )
    radarr_url: str = Field(
        ..., description="Base URL for Radarr instance (e.g., http://localhost:7878)"
    )

    # Sonarr connection settings
    sonarr_api_key: str = Field(
        ..., description="API key for Sonarr instance (required for series management)"
    )
    sonarr_url: str = Field(
        ..., description="Base URL for Sonarr instance (e.g., http://localhost:8989)"
    )

    # Tautulli connection settings
    tautulli_api_key: str = Field(
        ..., description="API key for Tautulli instance (required for watch history)"
    )
    tautulli_url: str = Field(
        ..., description="Base URL for Tautulli instance (e.g., http://localhost:8181)"
    )

    # User tag pattern configuration
    user_tag_regex: str = Field(
        default=r"^\d+ - (.+)$",
        description="Regex pattern for extracting usernames from Radarr/Sonarr tags",
    )

    # Cache configuration
    cache_enabled: bool = Field(default=True, description="Enable caching to improve performance")
    cache_dir: Optional[str] = Field(
        default=None, description="Custom cache directory (default: ~/.prunarr/cache)"
    )
    cache_ttl_movies: int = Field(
        default=3600, description="TTL for Radarr movie cache in seconds (default: 1 hour)"
    )
    cache_ttl_series: int = Field(
        default=3600, description="TTL for Sonarr series cache in seconds (default: 1 hour)"
    )
    cache_ttl_history: int = Field(
        default=300, description="TTL for Tautulli history cache in seconds (default: 5 minutes)"
    )
    cache_ttl_tags: int = Field(
        default=86400, description="TTL for tag cache in seconds (default: 24 hours)"
    )
    cache_ttl_metadata: int = Field(
        default=604800, description="TTL for metadata cache in seconds (default: 7 days)"
    )
    cache_max_size_mb: int = Field(
        default=100, description="Maximum cache size in megabytes (default: 100 MB)"
    )

    # Logging configuration
    log_level: str = Field(
        default="ERROR",
        description="Default log level: DEBUG, INFO, WARNING, ERROR (default: ERROR)",
    )

    # Streaming provider configuration
    streaming_enabled: bool = Field(
        default=False, description="Enable streaming provider checking via JustWatch"
    )
    streaming_locale: str = Field(
        default="en_US",
        description="Locale for JustWatch queries (format: language_COUNTRY, e.g., en_US)",
    )
    streaming_providers: list[str] = Field(
        default_factory=list,
        description="List of streaming provider technical names (e.g., netflix, amazonprime, disneyplus)",
    )
    cache_ttl_streaming: int = Field(
        default=86400,
        description="TTL for JustWatch streaming data cache in seconds (default: 24 hours)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """
        Validate log level is one of the allowed values.

        Args:
            value: The log level to validate

        Returns:
            Uppercase log level string

        Raises:
            ValueError: If log level is not valid
        """
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        value_upper = value.upper()
        if value_upper not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}, got '{value}'")
        return value_upper

    @field_validator(
        "radarr_api_key",
        "radarr_url",
        "sonarr_api_key",
        "sonarr_url",
        "tautulli_api_key",
        "tautulli_url",
    )
    @classmethod
    def validate_required_fields(cls, value: str) -> str:
        """
        Validate that required configuration fields are not empty.

        Args:
            value: The field value to validate

        Returns:
            Stripped string value

        Raises:
            ValueError: If the field is empty or whitespace-only
        """
        if not value or not value.strip():
            raise ValueError("cannot be empty")
        return value.strip()

    @field_validator("user_tag_regex")
    @classmethod
    def validate_regex_pattern(cls, value: str) -> str:
        """
        Validate that the user tag regex pattern is syntactically correct.

        Args:
            value: The regex pattern to validate

        Returns:
            Stripped regex pattern

        Raises:
            ValueError: If the regex pattern is invalid
        """
        try:
            re.compile(value)
            return value.strip()
        except re.error as e:
            raise ValueError(f"invalid regex pattern: {e}")

    @field_validator("radarr_url", "sonarr_url", "tautulli_url")
    @classmethod
    def validate_url_format(cls, value: str) -> str:
        """
        Validate and normalize URL formats.

        Args:
            value: The URL to validate

        Returns:
            Normalized URL with trailing slash removed
        """
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return value.rstrip("/")


def load_settings(config_file: Optional[str] = None) -> Settings:
    """
    Load configuration settings from YAML file or environment variables.

    Configuration loading priority:
    1. YAML file values (if config_file is provided)
    2. Environment variables
    3. Default values (where applicable)

    Args:
        config_file: Optional path to YAML configuration file

    Returns:
        Validated Settings object with all configuration

    Raises:
        FileNotFoundError: If specified config file doesn't exist
        ValidationError: If configuration values are invalid
        yaml.YAMLError: If YAML file is malformed
    """
    config_data: Dict[str, Any] = {}

    # Load from YAML file if provided
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with config_path.open("r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration file: {e}")

    # Build settings with YAML values taking precedence over environment variables
    return Settings(
        radarr_api_key=config_data.get("radarr_api_key") or os.getenv("RADARR_API_KEY", ""),
        radarr_url=config_data.get("radarr_url") or os.getenv("RADARR_URL", ""),
        sonarr_api_key=config_data.get("sonarr_api_key") or os.getenv("SONARR_API_KEY", ""),
        sonarr_url=config_data.get("sonarr_url") or os.getenv("SONARR_URL", ""),
        tautulli_api_key=config_data.get("tautulli_api_key") or os.getenv("TAUTULLI_API_KEY", ""),
        tautulli_url=config_data.get("tautulli_url") or os.getenv("TAUTULLI_URL", ""),
        user_tag_regex=config_data.get("user_tag_regex")
        or os.getenv("USER_TAG_REGEX", r"^\d+ - (.+)$"),
        # Cache settings
        cache_enabled=config_data.get("cache_enabled", True),
        cache_dir=config_data.get("cache_dir"),
        cache_ttl_movies=config_data.get("cache_ttl_movies", 3600),
        cache_ttl_series=config_data.get("cache_ttl_series", 3600),
        cache_ttl_history=config_data.get("cache_ttl_history", 300),
        cache_ttl_tags=config_data.get("cache_ttl_tags", 86400),
        cache_ttl_metadata=config_data.get("cache_ttl_metadata", 604800),
        cache_max_size_mb=config_data.get("cache_max_size_mb", 100),
        # Streaming settings
        streaming_enabled=config_data.get("streaming_enabled", False),
        streaming_locale=config_data.get("streaming_locale", "en_US"),
        streaming_providers=config_data.get("streaming_providers", []),
        cache_ttl_streaming=config_data.get("cache_ttl_streaming", 86400),
    )
