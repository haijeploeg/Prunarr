"""
Serialization utilities for PrunArr application.

This module provides JSON serialization helpers for converting
domain objects and datetime values to JSON-compatible formats.
"""

from datetime import datetime
from typing import Any, Dict, Optional


def prepare_datetime_for_json(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime object to ISO format string for JSON serialization.

    Args:
        dt: datetime object or None

    Returns:
        ISO format string or None if input is None

    Examples:
        >>> from datetime import datetime
        >>> prepare_datetime_for_json(datetime(2024, 1, 15, 10, 30))
        '2024-01-15T10:30:00'
        >>> prepare_datetime_for_json(None)
        None
    """
    return dt.isoformat() if dt else None


def prepare_movie_for_json(movie: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare movie data for JSON output.

    Converts datetime objects to ISO strings and ensures all fields
    are JSON-serializable.

    Args:
        movie: Movie dictionary with watch history data

    Returns:
        JSON-serializable movie dictionary

    Examples:
        >>> movie = {
        ...     'title': 'Test Movie',
        ...     'watched_date': datetime(2024, 1, 15),
        ...     'filesize': 1073741824
        ... }
        >>> result = prepare_movie_for_json(movie)
        >>> result['watched_date']
        '2024-01-15T00:00:00'
    """
    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "year": movie.get("year"),
        "username": movie.get("username"),
        "watched": movie.get("watched", False),
        "watched_by": movie.get("watched_by"),
        "watched_date": prepare_datetime_for_json(movie.get("watched_date")),
        "days_watched": movie.get("days_watched"),
        "filesize": movie.get("filesize"),
        "added_date": prepare_datetime_for_json(movie.get("added_date")),
    }


def prepare_series_for_json(series: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare series data for JSON output.

    Converts datetime objects to ISO strings and ensures all fields
    are JSON-serializable.

    Args:
        series: Series dictionary with watch history data

    Returns:
        JSON-serializable series dictionary

    Examples:
        >>> series = {
        ...     'title': 'Test Series',
        ...     'most_recent_watch': datetime(2024, 1, 15),
        ...     'watched_episodes': 10,
        ...     'total_episodes': 20
        ... }
        >>> result = prepare_series_for_json(series)
        >>> result['last_watched']
        '2024-01-15T00:00:00'
    """
    return {
        "id": series.get("id"),
        "title": series.get("title"),
        "user": series.get("user"),
        "watch_status": series.get("watch_status"),
        "watched_episodes": series.get("watched_episodes", 0),
        "total_episodes": series.get("total_episodes", 0),
        "completion_percentage": series.get("completion_percentage", 0),
        "seasons": series.get("available_seasons", ""),
        "total_size_bytes": series.get("total_size_on_disk", 0),
        "last_watched": prepare_datetime_for_json(series.get("most_recent_watch")),
        "days_since_watched": series.get("days_since_watched"),
    }


def prepare_history_for_json(history: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare history record for JSON output.

    Converts timestamp to ISO datetime strings and ensures all fields
    are JSON-serializable.

    Args:
        history: History dictionary from Tautulli

    Returns:
        JSON-serializable history dictionary

    Examples:
        >>> history = {
        ...     'history_id': 123,
        ...     'title': 'Test Movie',
        ...     'watched_at': 1705315800
        ... }
        >>> result = prepare_history_for_json(history)
        >>> result['watched_at']
        '2024-01-15T10:30:00'
    """
    from prunarr.utils.parsers import safe_timestamp_to_datetime

    # Convert watched_at timestamp to datetime, then to ISO string
    watched_at_dt = safe_timestamp_to_datetime(history.get("watched_at"))

    return {
        "history_id": history.get("history_id"),
        "title": history.get("title"),
        "user": history.get("user"),
        "media_type": history.get("media_type"),
        "watched_status": history.get("watched_status"),
        "percent_complete": history.get("percent_complete"),
        "duration": history.get("duration"),
        "watched_at": prepare_datetime_for_json(watched_at_dt),
        "platform": history.get("platform"),
        "year": history.get("year"),
        "rating_key": history.get("rating_key"),
    }


def prepare_episode_for_json(episode: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare episode data for JSON output.

    Converts datetime objects to ISO strings and ensures all fields
    are JSON-serializable.

    Args:
        episode: Episode dictionary with watch history data

    Returns:
        JSON-serializable episode dictionary

    Examples:
        >>> episode = {
        ...     'title': 'Test Episode',
        ...     'air_date': datetime(2024, 1, 15),
        ...     'watched_date': datetime(2024, 1, 20)
        ... }
        >>> result = prepare_episode_for_json(episode)
        >>> result['air_date']
        '2024-01-15T00:00:00'
    """
    return {
        "id": episode.get("id"),
        "season_number": episode.get("seasonNumber"),
        "episode_number": episode.get("episodeNumber"),
        "title": episode.get("title"),
        "air_date": prepare_datetime_for_json(episode.get("airDate")),
        "runtime": episode.get("runtime"),
        "watched": episode.get("watched", False),
        "watched_by": episode.get("watched_by"),
        "watched_date": prepare_datetime_for_json(episode.get("watched_date")),
        "filesize": episode.get("filesize", 0),
    }


def prepare_season_for_json(season: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare season data for JSON output.

    Converts episode lists and datetime objects to JSON-serializable format.

    Args:
        season: Season dictionary with episode data

    Returns:
        JSON-serializable season dictionary

    Examples:
        >>> season = {
        ...     'season_number': 1,
        ...     'episodes': [{'title': 'Ep1', 'watched': True}],
        ...     'total_filesize': 5368709120
        ... }
        >>> result = prepare_season_for_json(season)
        >>> len(result['episodes'])
        1
    """
    return {
        "season_number": season.get("season_number"),
        "total_episodes": season.get("total_episodes", 0),
        "watched_episodes": season.get("watched_episodes", 0),
        "progress_percent": season.get("progress_percent", 0.0),
        "total_filesize": season.get("total_filesize", 0),
        "episodes": [prepare_episode_for_json(ep) for ep in season.get("episodes", [])],
    }
