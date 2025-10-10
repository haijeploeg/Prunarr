"""
Validation utilities for PrunArr application.

This module provides validation functions for user input,
configuration values, and data integrity checks.
"""

import re
from typing import List, Optional

import typer


def validate_filesize_string(size_str: str) -> Optional[int]:
    """
    Parse and validate file size string to bytes.

    Args:
        size_str: File size string (e.g., '1GB', '500MB', '2.5GB')

    Returns:
        Size in bytes, or None if invalid format

    Examples:
        >>> validate_filesize_string('1GB')
        1073741824
        >>> validate_filesize_string('500MB')
        524288000
        >>> validate_filesize_string('invalid')
        None
    """
    if not size_str:
        return None

    # Match number with optional decimal and unit
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGT]?B)$", size_str.upper().strip())
    if not match:
        return None

    value, unit = match.groups()
    value = float(value)

    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    multiplier = units.get(unit, 1)
    return int(value * multiplier)


def validate_episode_key_format(episode_key: str) -> bool:
    """
    Validate episode key format.

    Args:
        episode_key: Episode key string (should be "s{season}e{episode}")

    Returns:
        True if valid format, False otherwise

    Examples:
        >>> validate_episode_key_format('s1e5')
        True
        >>> validate_episode_key_format('invalid')
        False
    """
    pattern = r"^s\d+e\d+$"
    return bool(re.match(pattern, episode_key.lower()))


def validate_positive_int(value: any) -> Optional[int]:
    """
    Validate and convert value to positive integer.

    Args:
        value: Value to validate

    Returns:
        Positive integer or None if invalid

    Examples:
        >>> validate_positive_int(5)
        5
        >>> validate_positive_int('10')
        10
        >>> validate_positive_int(-1)
        None
        >>> validate_positive_int('invalid')
        None
    """
    try:
        num = int(value)
        return num if num > 0 else None
    except (ValueError, TypeError):
        return None


def validate_non_negative_int(value: any) -> Optional[int]:
    """
    Validate and convert value to non-negative integer.

    Args:
        value: Value to validate

    Returns:
        Non-negative integer or None if invalid

    Examples:
        >>> validate_non_negative_int(0)
        0
        >>> validate_non_negative_int(5)
        5
        >>> validate_non_negative_int(-1)
        None
    """
    try:
        num = int(value)
        return num if num >= 0 else None
    except (ValueError, TypeError):
        return None


def validate_percentage(value: any) -> Optional[float]:
    """
    Validate percentage value (0-100).

    Args:
        value: Value to validate

    Returns:
        Float between 0-100 or None if invalid

    Examples:
        >>> validate_percentage(50)
        50.0
        >>> validate_percentage(100.5)
        None
        >>> validate_percentage(-5)
        None
    """
    try:
        num = float(value)
        return num if 0 <= num <= 100 else None
    except (ValueError, TypeError):
        return None


def validate_output_format(output: str, logger) -> None:
    """
    Validate output format option for CLI commands.

    Args:
        output: Output format string to validate
        logger: Logger instance for error messages

    Raises:
        typer.Exit: If output format is invalid

    Examples:
        >>> validate_output_format("table", logger)  # Valid - no error
        >>> validate_output_format("json", logger)   # Valid - no error
        >>> validate_output_format("xml", logger)    # Invalid - raises Exit
    """
    valid_formats = ["table", "json"]
    if output not in valid_formats:
        logger.error(f"Invalid output format: {output}. Must be 'table' or 'json'")
        raise typer.Exit(1)


def validate_sort_option(
    sort_by: str, valid_options: List[str], logger, option_name: str = "sort option"
) -> None:
    """
    Validate sort option against list of valid options.

    Args:
        sort_by: Sort option to validate
        valid_options: List of valid sort options
        logger: Logger instance for error messages
        option_name: Name of the option for error message (default: "sort option")

    Raises:
        typer.Exit: If sort option is invalid

    Examples:
        >>> validate_sort_option("title", ["title", "date"], logger)  # Valid
        >>> validate_sort_option("size", ["title", "date"], logger)   # Invalid - raises Exit
    """
    if sort_by not in valid_options:
        options_str = ", ".join(valid_options)
        logger.error(f"Invalid {option_name}: {sort_by}. Valid options: {options_str}")
        raise typer.Exit(1)


def validate_media_type(media_type: str, logger) -> None:
    """
    Validate media type option for Tautulli history filtering.

    Args:
        media_type: Media type to validate
        logger: Logger instance for error messages

    Raises:
        typer.Exit: If media type is invalid
    """
    valid_types = ["movie", "show", "episode"]
    if media_type and media_type not in valid_types:
        logger.error(f"Invalid media type: {media_type}. Valid types: {', '.join(valid_types)}")
        raise typer.Exit(1)


def validate_log_level(log_level: str) -> str:
    """
    Validate and normalize log level.

    Args:
        log_level: Log level string to validate

    Returns:
        Normalized log level (uppercase)

    Raises:
        ValueError: If log level is invalid

    Examples:
        >>> validate_log_level("debug")
        'DEBUG'
        >>> validate_log_level("INFO")
        'INFO'
        >>> validate_log_level("invalid")
        Traceback (most recent call last):
        ...
        ValueError: log_level must be one of ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    """
    allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    normalized = log_level.upper()

    if normalized not in allowed_levels:
        raise ValueError(f"log_level must be one of {allowed_levels}, got '{log_level}'")

    return normalized


def validate_streaming_filters(
    on_streaming: bool, not_on_streaming: bool, settings, logger
) -> None:
    """
    Validate streaming filter options.

    Args:
        on_streaming: Filter for items on streaming services
        not_on_streaming: Filter for items not on streaming services
        settings: Settings object with streaming configuration
        logger: Logger instance for error messages

    Raises:
        typer.Exit: If both filters are used together or streaming is not enabled
    """
    # Check mutual exclusivity
    if on_streaming and not_on_streaming:
        logger.error("Cannot use both --on-streaming and --not-on-streaming filters together")
        raise typer.Exit(1)

    # Check if streaming is configured
    if (on_streaming or not_on_streaming) and not settings.streaming_enabled:
        logger.error(
            "Streaming filters require streaming_enabled=true in configuration. "
            "Please configure streaming_enabled, streaming_locale, and streaming_providers in your config."
        )
        raise typer.Exit(1)
