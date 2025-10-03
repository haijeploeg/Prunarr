"""
Utility modules for PrunArr application.

This package provides focused utility modules for formatting,
parsing, filtering, and validation operations.
"""

# Import from submodules for backward compatibility
from prunarr.utils.formatters import (
    format_completion_percentage,
    format_date,
    format_date_or_default,
    format_duration,
    format_episode_count,
    format_file_size,
    format_history_watch_status,
    format_movie_watch_status,
    format_series_watch_status,
    format_timestamp,
    format_timestamp_to_date,
    safe_get,
    safe_str,
)
from prunarr.utils.parsers import make_episode_key, parse_episode_key

__all__ = [
    # Formatters
    "format_file_size",
    "format_date",
    "format_date_or_default",
    "format_timestamp",
    "format_timestamp_to_date",
    "format_duration",
    "format_movie_watch_status",
    "format_series_watch_status",
    "format_history_watch_status",
    "format_completion_percentage",
    "format_episode_count",
    "safe_str",
    "safe_get",
    # Parsers
    "make_episode_key",
    "parse_episode_key",
]
