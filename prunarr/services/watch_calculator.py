"""
Watch calculator service for determining watch status and progress.

This service handles all calculations related to watch status, progress
percentages, and completion analysis for movies and series.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from prunarr.utils.parsers import parse_episode_key


class WatchCalculator:
    """
    Service for calculating watch status and progress metrics.

    This service encapsulates logic for determining watch status,
    calculating completion percentages, and analyzing watch history
    for both movies and series.
    """

    @staticmethod
    def determine_movie_watch_status(
        movie_user: Optional[str], all_watchers: List[str]
    ) -> Tuple[str, Optional[str]]:
        """
        Determine watch status and watched_by display for a movie.

        Args:
            movie_user: Username associated with the movie (from tags)
            all_watchers: List of all users who watched the movie

        Returns:
            Tuple of (watch_status, watched_by_display)
            - watch_status: "watched", "watched_by_other", or "unwatched"
            - watched_by_display: Comma-separated list of watchers or None
        """
        if not all_watchers:
            return "unwatched", None

        watched_by_display = ", ".join(sorted(all_watchers))

        if movie_user and movie_user in all_watchers:
            return "watched", watched_by_display
        elif movie_user and movie_user not in all_watchers:
            return "watched_by_other", watched_by_display
        else:
            # Untagged movie that has been watched
            return "watched", watched_by_display

    @staticmethod
    def determine_series_watch_status(watched_episodes: int, total_episodes: int) -> str:
        """
        Determine overall watch status for a series.

        Args:
            watched_episodes: Number of episodes watched by user
            total_episodes: Total number of episodes

        Returns:
            Watch status: "fully_watched", "partially_watched", "unwatched", or "no_episodes"
        """
        if total_episodes == 0:
            return "no_episodes"
        elif watched_episodes == 0:
            return "unwatched"
        elif watched_episodes == total_episodes:
            return "fully_watched"
        else:
            return "partially_watched"

    @staticmethod
    def calculate_completion_percentage(watched_count: int, total_count: int) -> float:
        """
        Calculate completion percentage.

        Args:
            watched_count: Number of items watched
            total_count: Total number of items

        Returns:
            Completion percentage (0-100)
        """
        if total_count == 0:
            return 0.0
        return (watched_count / total_count) * 100

    @staticmethod
    def calculate_days_since_watched(watched_timestamp: str) -> Optional[int]:
        """
        Calculate days since content was watched.

        Args:
            watched_timestamp: Unix timestamp as string

        Returns:
            Number of days since watched, or None if invalid timestamp
        """
        if not watched_timestamp:
            return None

        try:
            watched_date = datetime.fromtimestamp(int(watched_timestamp))
            return (datetime.now() - watched_date).days
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_most_recent_watch(
        series_watch_info: Dict[str, Dict],
    ) -> Tuple[Optional[datetime], Optional[int]]:
        """
        Calculate most recent watch date and days since for a series.

        Args:
            series_watch_info: Dictionary mapping episode_key -> user -> watch_data

        Returns:
            Tuple of (most_recent_watch_datetime, days_since_watched)
        """
        if not series_watch_info:
            return None, None

        most_recent_ts = 0
        for episode_watchers in series_watch_info.values():
            for user_watch in episode_watchers.values():
                watched_at = user_watch.get("watched_at")
                if watched_at and int(watched_at) > most_recent_ts:
                    most_recent_ts = int(watched_at)

        if most_recent_ts > 0:
            most_recent_watch = datetime.fromtimestamp(most_recent_ts)
            days_since_watched = (datetime.now() - most_recent_watch).days
            return most_recent_watch, days_since_watched

        return None, None

    @staticmethod
    def count_watched_episodes(
        series_watch_info: Dict[str, Dict],
        series_user: Optional[str],
        season_filter: Optional[int] = None,
    ) -> int:
        """
        Count episodes watched by a specific user.

        Args:
            series_watch_info: Dictionary mapping episode_key -> user -> watch_data
            series_user: Username to count watches for
            season_filter: Optional season number to filter by

        Returns:
            Number of episodes watched by the user
        """
        if not series_user:
            return 0

        count = 0
        for episode_key, episode_watchers in series_watch_info.items():
            parsed = parse_episode_key(episode_key)
            if not parsed:
                continue

            season_num, _ = parsed

            # Apply season filter
            if season_filter is not None and season_num != season_filter:
                continue

            # Skip season 0 (specials) unless specifically requested
            if season_filter is None and season_num == 0:
                continue

            # Check if series user watched this episode
            if series_user in episode_watchers:
                count += 1

        return count

    @staticmethod
    def get_most_recent_watch_from_episode_watchers(
        episode_watchers: Dict[str, Dict],
    ) -> Tuple[Optional[datetime], Optional[int]]:
        """
        Get most recent watch datetime and days since from episode watchers dict.

        Args:
            episode_watchers: Dictionary mapping user -> watch_data

        Returns:
            Tuple of (most_recent_watch_datetime, days_since_watched)
        """
        if not episode_watchers:
            return None, None

        most_recent_ts = max(
            int(w["watched_at"]) for w in episode_watchers.values() if w.get("watched_at")
        )

        if most_recent_ts > 0:
            most_recent_watch = datetime.fromtimestamp(most_recent_ts)
            days_since_watched = (datetime.now() - most_recent_watch).days
            return most_recent_watch, days_since_watched

        return None, None
