"""
Parsing utilities for PrunArr application.

This module provides parsing functions for episode keys, file sizes,
and other data format conversions.
"""

import re
from datetime import datetime
from typing import Optional, Tuple


def make_episode_key(season_num: int, episode_num: int) -> str:
    """
    Create standardized episode key string.

    Args:
        season_num: Season number
        episode_num: Episode number

    Returns:
        Episode key in format "s{season}e{episode}" (e.g., "s1e5")
    """
    return f"s{season_num}e{episode_num}"


def parse_episode_key(episode_key: str) -> Optional[Tuple[int, int]]:
    """
    Parse episode key into season and episode numbers.

    Args:
        episode_key: Episode key string (e.g., "s1e5")

    Returns:
        Tuple of (season_num, episode_num) or None if parsing fails
    """
    try:
        parts = episode_key.lower().split("e")
        season_num = int(parts[0][1:])  # Remove 's' prefix
        episode_num = int(parts[1])
        return season_num, episode_num
    except (ValueError, IndexError, AttributeError):
        return None


def parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.

    Supports sizes with units: B, KB, MB, GB, TB
    Handles decimal values (e.g., "2.5GB")

    Args:
        size_str: File size string (e.g., "1GB", "500MB", "2.5GB")

    Returns:
        File size in bytes

    Raises:
        ValueError: If the size string format is invalid

    Examples:
        >>> parse_file_size("1GB")
        1073741824
        >>> parse_file_size("500MB")
        524288000
        >>> parse_file_size("2.5GB")
        2684354560
        >>> parse_file_size("1024B")
        1024
    """
    if not size_str:
        raise ValueError("Size string cannot be empty")

    # Match number (with optional decimal) and unit
    pattern = r"^(\d+(?:\.\d+)?)\s*([KMGT]?B)$"
    match = re.match(pattern, size_str.upper().strip())

    if not match:
        raise ValueError(
            f"Invalid file size format: '{size_str}'. "
            "Expected format: <number><unit> (e.g., '1GB', '500MB', '2.5GB')"
        )

    value_str, unit = match.groups()
    value = float(value_str)

    # Unit conversion factors
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    multiplier = units.get(unit, 1)
    return int(value * multiplier)


def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse ISO datetime string with timezone handling.

    Handles both standard ISO format and timestamps with 'Z' timezone indicator.

    Args:
        date_str: ISO format datetime string

    Returns:
        datetime object or None if parsing fails

    Examples:
        >>> parse_iso_datetime("2024-01-15T10:30:00+00:00")
        datetime.datetime(2024, 1, 15, 10, 30, tzinfo=datetime.timezone.utc)
        >>> parse_iso_datetime("2024-01-15T10:30:00Z")
        datetime.datetime(2024, 1, 15, 10, 30, tzinfo=datetime.timezone.utc)
        >>> parse_iso_datetime("")
        None
    """
    if not date_str:
        return None

    try:
        # Replace 'Z' with '+00:00' for proper ISO parsing
        normalized = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, AttributeError):
        return None


def safe_timestamp_to_datetime(timestamp: any, default=None) -> Optional[datetime]:
    """
    Safely convert timestamp to datetime object.

    Args:
        timestamp: Unix timestamp (int, str, or float)
        default: Default value if conversion fails (default: None)

    Returns:
        datetime object or default value if conversion fails

    Examples:
        >>> safe_timestamp_to_datetime(1705315800)
        datetime.datetime(2024, 1, 15, 10, 30)
        >>> safe_timestamp_to_datetime("1705315800")
        datetime.datetime(2024, 1, 15, 10, 30)
        >>> safe_timestamp_to_datetime("invalid")
        None
    """
    if not timestamp:
        return default

    try:
        return datetime.fromtimestamp(int(timestamp))
    except (ValueError, TypeError):
        return default
