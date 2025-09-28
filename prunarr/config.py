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
    )
