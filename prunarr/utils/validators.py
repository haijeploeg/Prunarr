"""
Validation utilities for PrunArr application.

This module provides validation functions for user input,
configuration values, and data integrity checks.
"""

import re
from typing import Optional


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
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]?B)$', size_str.upper().strip())
    if not match:
        return None

    value, unit = match.groups()
    value = float(value)

    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
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
    pattern = r'^s\d+e\d+$'
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
