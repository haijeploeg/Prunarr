"""
Parsing utilities for PrunArr application.

This module provides parsing functions for episode keys and other
data format conversions.
"""

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
