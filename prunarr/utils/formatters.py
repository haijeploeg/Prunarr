"""
Formatting utilities for PrunArr CLI application.

This module provides formatting functions for displaying data
in human-readable formats with Rich markup styling.
"""

from datetime import datetime
from typing import Any, Dict, Optional


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size string (e.g., "1.2 GB" or "450 MB")
    """
    if not size_bytes:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Format with appropriate decimal places
    if size >= 100:
        return f"{size:.0f} {units[unit_index]}"
    elif size >= 10:
        return f"{size:.1f} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_date(date_obj: Optional[datetime]) -> str:
    """
    Format datetime object to human readable format.

    Args:
        date_obj: Datetime object or None

    Returns:
        Formatted date string in "YYYY-MM-DD" format or "N/A"
    """
    if not date_obj:
        return "N/A"
    return date_obj.strftime("%Y-%m-%d")


def format_date_or_default(date_obj: Optional[datetime], default: str = "N/A") -> str:
    """
    Format datetime to YYYY-MM-DD or return default.

    Flexible version of format_date() that allows custom default values.

    Args:
        date_obj: Datetime object or None
        default: Default string if date_obj is None (default: "N/A")

    Returns:
        Formatted date string in "YYYY-MM-DD" format or default value

    Examples:
        >>> format_date_or_default(datetime(2024, 1, 15))
        '2024-01-15'
        >>> format_date_or_default(None)
        'N/A'
        >>> format_date_or_default(None, "Never")
        'Never'
    """
    if not date_obj:
        return default
    return date_obj.strftime("%Y-%m-%d")


def format_timestamp_to_date(timestamp: Any, default: str = "N/A") -> str:
    """
    Convert Unix timestamp to formatted date string.

    Args:
        timestamp: Unix timestamp (int, str, or float)
        default: Default string if conversion fails (default: "N/A")

    Returns:
        Formatted date string in "YYYY-MM-DD" format or default value

    Examples:
        >>> format_timestamp_to_date(1705315800)
        '2024-01-15'
        >>> format_timestamp_to_date("1705315800")
        '2024-01-15'
        >>> format_timestamp_to_date(None)
        'N/A'
        >>> format_timestamp_to_date("invalid", "Unknown")
        'Unknown'
    """
    if not timestamp:
        return default

    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return default


def format_timestamp(timestamp: str) -> str:
    """
    Format Unix timestamp to human readable datetime format.

    Args:
        timestamp: Unix timestamp as string

    Returns:
        Formatted datetime string in "YYYY-MM-DD HH:MM" format
    """
    if not timestamp:
        return "N/A"

    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return str(timestamp)


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2h 30m" or "45m")
    """
    if not seconds:
        return "N/A"

    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_movie_watch_status(status: str) -> str:
    """
    Format movie watch status with Rich markup colors.

    Args:
        status: Watch status (watched, unwatched, watched_by_other)

    Returns:
        Colored status string with Rich markup
    """
    status_colors = {
        "watched": "[green]✓ Watched[/green]",
        "unwatched": "[red]✗ Unwatched[/red]",
        "watched_by_other": "[yellow]👤 Watched[/yellow]",
    }
    return status_colors.get(status, "[dim]Unknown[/dim]")


def format_series_watch_status(status: str) -> str:
    """
    Format series watch status with Rich markup colors.

    Args:
        status: Watch status (fully_watched, partially_watched, unwatched, no_episodes)

    Returns:
        Colored status string with Rich markup
    """
    if status == "fully_watched":
        return "[green]✓ Fully Watched[/green]"
    elif status == "partially_watched":
        return "[yellow]📺 Partially Watched[/yellow]"
    elif status == "unwatched":
        return "[red]✗ Unwatched[/red]"
    elif status == "no_episodes":
        return "[dim]❌ No Episodes[/dim]"
    else:
        return "[dim]❓ Unknown[/dim]"


def format_history_watch_status(status: int) -> str:
    """
    Format history watch status with Rich markup colors.

    Args:
        status: Tautulli watched status code
               1 = Fully watched, 0 = Partially watched, other = Stopped

    Returns:
        Colored status string with Rich markup
    """
    if status == 1:
        return "[green]✓ Watched[/green]"
    elif status == 0:
        return "[yellow]⏸ Partial[/yellow]"
    else:
        return "[red]✗ Stopped[/red]"


def format_completion_percentage(percentage: float) -> str:
    """
    Format completion percentage with color coding.

    Args:
        percentage: Completion percentage (0-100)

    Returns:
        Colored percentage string with Rich markup
    """
    if percentage >= 100:
        return f"[green]{percentage:.0f}%[/green]"
    elif percentage >= 50:
        return f"[yellow]{percentage:.0f}%[/yellow]"
    elif percentage > 0:
        return f"[red]{percentage:.0f}%[/red]"
    else:
        return "[dim]0%[/dim]"


def format_episode_count(watched: int, total: int) -> str:
    """
    Format episode count with color coding.

    Args:
        watched: Number of watched episodes
        total: Total number of episodes

    Returns:
        Colored episode count string
    """
    if total == 0:
        return "[dim]0/0[/dim]"
    elif watched == total:
        return f"[green]{watched}/{total}[/green]"
    elif watched > 0:
        return f"[yellow]{watched}/{total}[/yellow]"
    else:
        return f"[red]{watched}/{total}[/red]"


def safe_str(value: Any, default: str = "N/A") -> str:
    """
    Safely convert value to string with default fallback.

    Commonly used pattern in table row creation to handle None values.

    Args:
        value: Value to convert to string
        default: Default string if value is None or empty (default: "N/A")

    Returns:
        String representation of value or default

    Examples:
        >>> safe_str(None)
        'N/A'
        >>> safe_str("test")
        'test'
        >>> safe_str(123)
        '123'
        >>> safe_str("", default="Unknown")
        'Unknown'
    """
    if value is None or value == "":
        return default
    return str(value)


def safe_get(data: Dict[str, Any], key: str, default: str = "N/A") -> str:
    """
    Safely get value from dict and convert to string.

    Combines dict.get() with str() conversion and None handling.
    Commonly used pattern: str(movie.get("title", "N/A"))

    Args:
        data: Dictionary to get value from
        key: Key to look up
        default: Default string if key not found or value is None

    Returns:
        String representation of value or default

    Examples:
        >>> safe_get({"title": "Test"}, "title")
        'Test'
        >>> safe_get({"title": None}, "title")
        'N/A'
        >>> safe_get({}, "missing", "Unknown")
        'Unknown'
    """
    value = data.get(key)
    return safe_str(value, default)
