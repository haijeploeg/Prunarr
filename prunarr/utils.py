"""
Shared utility functions for PrunArr CLI application.

This module provides common formatting and helper functions used across
command modules to eliminate code duplication and ensure consistency.
"""

from datetime import datetime
from typing import Optional, Tuple


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


# Episode key utilities

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