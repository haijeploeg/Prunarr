"""
Filtering utilities for PrunArr application.

This module provides common filtering functions for movies and series
based on various criteria.
"""

from typing import Any, Dict, List, Optional


def filter_by_username(
    items: List[Dict[str, Any]], username: Optional[str]
) -> List[Dict[str, Any]]:
    """
    Filter items by username.

    Args:
        items: List of items with 'user' field
        username: Username to filter by (None = no filter)

    Returns:
        Filtered list of items
    """
    if not username:
        return items
    return [item for item in items if item.get("user") == username]


def filter_by_title(
    items: List[Dict[str, Any]], title_filter: Optional[str]
) -> List[Dict[str, Any]]:
    """
    Filter items by partial title match (case-insensitive).

    Args:
        items: List of items with 'title' field
        title_filter: Title substring to filter by (None = no filter)

    Returns:
        Filtered list of items
    """
    if not title_filter:
        return items

    title_lower = title_filter.lower()
    return [item for item in items if title_lower in item.get("title", "").lower()]


def filter_by_watch_status(
    items: List[Dict[str, Any]],
    watched: bool = False,
    unwatched: bool = False,
    status_field: str = "watch_status",
) -> List[Dict[str, Any]]:
    """
    Filter items by watch status.

    Args:
        items: List of items with watch status field
        watched: Show only watched items
        unwatched: Show only unwatched items
        status_field: Name of the status field to check

    Returns:
        Filtered list of items
    """
    if not watched and not unwatched:
        return items

    if watched:
        return [item for item in items if item.get(status_field) in ["watched", "fully_watched"]]
    elif unwatched:
        return [item for item in items if item.get(status_field) in ["unwatched"]]

    return items


def filter_by_season(items: List[Dict[str, Any]], season: Optional[int]) -> List[Dict[str, Any]]:
    """
    Filter items by season number.

    Args:
        items: List of items with 'season_number' field
        season: Season number to filter by (None = no filter)

    Returns:
        Filtered list of items
    """
    if season is None:
        return items
    return [item for item in items if item.get("season_number") == season]


def filter_by_days_watched(
    items: List[Dict[str, Any]], min_days: Optional[int]
) -> List[Dict[str, Any]]:
    """
    Filter items by minimum days since watched.

    Args:
        items: List of items with 'days_since_watched' field
        min_days: Minimum days since watched (None = no filter)

    Returns:
        Filtered list of items
    """
    if min_days is None:
        return items

    return [
        item
        for item in items
        if item.get("days_since_watched") is not None and item.get("days_since_watched") >= min_days
    ]


def filter_by_filesize(
    items: List[Dict[str, Any]], min_size_bytes: Optional[int]
) -> List[Dict[str, Any]]:
    """
    Filter items by minimum file size.

    Args:
        items: List of items with 'file_size' field
        min_size_bytes: Minimum file size in bytes (None = no filter)

    Returns:
        Filtered list of items
    """
    if min_size_bytes is None:
        return items

    return [item for item in items if item.get("file_size", 0) >= min_size_bytes]
