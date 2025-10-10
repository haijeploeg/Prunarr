"""
Table row formatting helpers for PrunArr CLI application.

This module provides reusable table row formatting functions to eliminate
duplication between list and removal commands.
"""

from typing import Any, Dict, List

from prunarr.utils.formatters import (
    format_completion_percentage,
    format_date_or_default,
    format_episode_count,
    format_file_size,
    format_movie_watch_status,
    format_series_watch_status,
    safe_get,
    safe_str,
)
from prunarr.utils.parsers import parse_iso_datetime


def format_tags_display(tag_labels: List[str], max_tags: int = 3) -> str:
    """
    Format tag labels for table display.

    Args:
        tag_labels: List of tag label strings (non-user tags)
        max_tags: Maximum number of tags to show before truncating

    Returns:
        Formatted tag string (e.g., "4K, HDR, Action" or "4K, HDR, Action, +2 more")
    """
    if not tag_labels:
        return "-"

    if len(tag_labels) <= max_tags:
        return ", ".join(tag_labels)
    else:
        visible_tags = ", ".join(tag_labels[:max_tags])
        remaining = len(tag_labels) - max_tags
        return f"{visible_tags}, +{remaining} more"


def format_movie_table_row(movie: Dict[str, Any], include_streaming: bool = False) -> List[str]:
    """
    Format a movie dictionary into a list of formatted strings for table display.

    Args:
        movie: Movie dictionary containing all movie data
        include_streaming: Whether to include streaming availability column

    Returns:
        List of formatted strings ready for table.add_row()
        Order: Title, Year, User, Watch Status, Watched By, Days Ago, File Size, [Streaming], Added
    """
    # Format user display
    user_display = safe_get(movie, "user") or "[dim]Untagged[/dim]"

    # Format tags
    tags_display = format_tags_display(movie.get("tag_labels", []))

    # Format watched by (handle multiple users)
    watched_by = safe_get(movie, "watched_by") or "N/A"

    # Format days since watched
    days_ago = (
        str(movie.get("days_since_watched", ""))
        if movie.get("days_since_watched") is not None
        else "N/A"
    )

    # Format added date
    added_date = format_date_or_default(parse_iso_datetime(movie.get("added")))

    # Build row data (without streaming)
    # Order: Title, Year, User, Tags, Watch Status, Watched By, Days Ago, File Size
    row_data = [
        safe_get(movie, "title"),
        safe_get(movie, "year"),
        user_display,
        tags_display,
        format_movie_watch_status(movie.get("watch_status", "unknown")),
        watched_by,
        days_ago,
        format_file_size(movie.get("file_size", 0)),
    ]

    # Add streaming info if requested
    if include_streaming:
        streaming_available = movie.get("streaming_available")
        if streaming_available is True:
            streaming_display = "✓"
        elif streaming_available is False:
            streaming_display = "✗"
        else:
            streaming_display = "-"  # Not checked yet
        row_data.append(streaming_display)

    # Add date at the end
    row_data.append(added_date)

    return row_data


def format_series_table_row(series: Dict[str, Any], include_streaming: bool = False) -> List[str]:
    """
    Format a series dictionary into a list of formatted strings for table display.

    Args:
        series: Series dictionary containing all series data
        include_streaming: Whether to include streaming availability column

    Returns:
        List of formatted strings ready for table.add_row()
        Order: ID, Title, User, Status, Episodes, Progress, Seasons, Size, [Streaming], Last Watched, Days Ago
    """
    # Format user display
    user_display = safe_str(series.get("user"), default="Untagged")

    # Format tags
    tags_display = format_tags_display(series.get("tag_labels", []))

    # Format available seasons
    available_seasons = series.get("available_seasons", "")
    seasons_display = available_seasons if available_seasons else "-"

    # Format last watched date
    last_watched_str = format_date_or_default(series.get("most_recent_watch"), default="Never")

    # Format days since watched
    days_ago = safe_str(series.get("days_since_watched"))

    # Build row data (without streaming)
    # Order: ID, Title, User, Tags, Status, Episodes, Progress, Seasons, Size
    row_data = [
        safe_get(series, "id"),
        safe_get(series, "title"),
        user_display,
        tags_display,
        format_series_watch_status(series.get("watch_status", "unknown")),
        format_episode_count(series.get("watched_episodes", 0), series.get("total_episodes", 0)),
        format_completion_percentage(series.get("completion_percentage", 0)),
        seasons_display,
        format_file_size(series.get("total_size_on_disk", 0)),
    ]

    # Add streaming info if requested
    if include_streaming:
        streaming_available = series.get("streaming_available")
        if streaming_available is True:
            streaming_display = "✓"
        elif streaming_available is False:
            streaming_display = "✗"
        else:
            streaming_display = "-"  # Not checked yet
        row_data.append(streaming_display)

    # Add last watched date and days ago at the end
    row_data.append(last_watched_str)
    row_data.append(days_ago)

    return row_data
