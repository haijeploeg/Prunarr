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


def filter_by_tags(
    items: List[Dict[str, Any]],
    tags: Optional[List[str]],
    match_all: bool = False,
) -> List[Dict[str, Any]]:
    """
    Filter items by tag labels (case-insensitive).

    Args:
        items: List of items with 'tag_labels' field
        tags: List of tag names to filter by (None = no filter)
        match_all: If True, item must have ALL tags; if False, item must have ANY tag

    Returns:
        Filtered list of items

    Examples:
        >>> # Items with ANY of these tags
        >>> filtered = filter_by_tags(movies, ["4K", "Action"], match_all=False)
        >>>
        >>> # Items with ALL of these tags
        >>> filtered = filter_by_tags(movies, ["4K", "HDR"], match_all=True)
    """
    if not tags:
        return items

    # Normalize tags to lowercase for case-insensitive matching
    tags_lower = [tag.lower() for tag in tags]

    filtered_items = []
    for item in items:
        item_tags = [tag.lower() for tag in item.get("tag_labels", [])]

        if match_all:
            # Item must have ALL specified tags
            if all(tag in item_tags for tag in tags_lower):
                filtered_items.append(item)
        else:
            # Item must have ANY of the specified tags
            if any(tag in item_tags for tag in tags_lower):
                filtered_items.append(item)

    return filtered_items


def filter_by_excluded_tags(
    items: List[Dict[str, Any]],
    excluded_tags: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """
    Filter out items that have any of the specified tags (case-insensitive).

    Args:
        items: List of items with 'tag_labels' field
        excluded_tags: List of tag names to exclude (None = no filter)

    Returns:
        Filtered list of items (excluding items with any of the specified tags)

    Examples:
        >>> # Exclude items with these tags
        >>> filtered = filter_by_excluded_tags(movies, ["Kids", "Documentary"])
    """
    if not excluded_tags:
        return items

    # Normalize tags to lowercase for case-insensitive matching
    excluded_tags_lower = [tag.lower() for tag in excluded_tags]

    filtered_items = []
    for item in items:
        item_tags = [tag.lower() for tag in item.get("tag_labels", [])]

        # Include item only if it doesn't have any of the excluded tags
        if not any(tag in excluded_tags_lower for tag in item_tags):
            filtered_items.append(item)

    return filtered_items


def apply_streaming_filter(
    items: List[Dict[str, Any]],
    on_streaming: bool,
    not_on_streaming: bool,
    media_type: str,
    settings,
    cache_manager,
    logger,
) -> List[Dict[str, Any]]:
    """
    Apply streaming availability filtering to items.

    This function checks whether items are available on configured streaming
    services and filters them accordingly. It uses caching to minimize API
    calls to the JustWatch service.

    Args:
        items: List of items to filter (movies or series)
        on_streaming: If True, keep only items available on streaming
        not_on_streaming: If True, keep only items not available on streaming
        media_type: Type of media ('movie' or 'show')
        settings: Settings object with streaming configuration
        cache_manager: Cache manager for storing streaming availability data
        logger: Logger instance for progress messages

    Returns:
        Filtered list of items based on streaming availability

    Examples:
        >>> filtered = apply_streaming_filter(
        ...     items=movies,
        ...     on_streaming=True,
        ...     not_on_streaming=False,
        ...     media_type='movie',
        ...     settings=settings,
        ...     cache_manager=cache_manager,
        ...     logger=logger
        ... )
    """
    # No filter needed if neither option is set
    if not on_streaming and not not_on_streaming:
        return items

    from prunarr.services.streaming_checker import StreamingChecker

    logger.info("Filtering by streaming availability (using cached data)...")
    streaming_checker = StreamingChecker(
        locale=settings.streaming_locale,
        providers=settings.streaming_providers,
        cache_manager=cache_manager,
        logger=logger,
    )

    streaming_filtered = []
    for item in items:
        # Try to use cached streaming_available field first
        is_available = item.get("streaming_available")

        # If not in cache, check via API (and cache the result)
        if is_available is None:
            is_available = streaming_checker.is_on_streaming(
                media_type=media_type,
                title=item.get("title", ""),
                year=item.get("year"),
                imdb_id=item.get("imdb_id") if media_type == "movie" else None,
                tvdb_id=item.get("tvdb_id") if media_type == "show" else None,
            )

        # Apply the appropriate filter
        if on_streaming and is_available:
            streaming_filtered.append(item)
        elif not_on_streaming and not is_available:
            streaming_filtered.append(item)

    filter_type = "on streaming" if on_streaming else "not on streaming"
    logger.info(f"After streaming filter: {len(streaming_filtered)} items {filter_type}")

    return streaming_filtered


def populate_streaming_data(
    items: List[Dict[str, Any]],
    media_type: str,
    settings,
    cache_manager,
    logger,
) -> List[Dict[str, Any]]:
    """
    Populate streaming availability data for all items without filtering.

    This function checks streaming availability for all items and adds the
    streaming_available field to each item. It uses caching to minimize API calls.

    Args:
        items: List of items to populate (movies or series)
        media_type: Type of media ('movie' or 'show')
        settings: Settings object with streaming configuration
        cache_manager: Cache manager for storing streaming availability data
        logger: Logger instance for progress messages

    Returns:
        List of items with streaming_available field populated
    """
    from prunarr.services.streaming_checker import StreamingChecker

    logger.info("Populating streaming availability data...")
    streaming_checker = StreamingChecker(
        locale=settings.streaming_locale,
        providers=settings.streaming_providers,
        cache_manager=cache_manager,
        logger=logger,
    )

    for item in items:
        # Check if already populated
        if item.get("streaming_available") is None:
            is_available = streaming_checker.is_on_streaming(
                media_type=media_type,
                title=item.get("title", ""),
                year=item.get("year"),
                imdb_id=item.get("imdb_id") if media_type == "movie" else None,
                tvdb_id=item.get("tvdb_id") if media_type == "show" else None,
            )
            item["streaming_available"] = is_available

    return items
