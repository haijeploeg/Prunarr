"""
Series domain model for Sonarr integration.

Provides a strongly-typed representation of TV series with watch status,
user associations, and episode tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Series:
    """
    Represents a TV series from Sonarr with associated metadata and watch status.

    Attributes:
        id: Sonarr series ID
        title: Series title
        year: Release year
        tvdb_id: TVDB identifier
        imdb_id: IMDB identifier
        user: Associated username from tags (None if untagged)
        has_file: Whether any episode files exist
        total_episodes: Total number of episodes
        downloaded_episodes: Number of downloaded episode files
        added: Date series was added to Sonarr
        monitored: Whether series is monitored in Sonarr
        status: Series status (continuing, ended, etc.)
        seasons: List of season dictionaries
        tags: List of tag IDs
        statistics: Series statistics dictionary
        watch_status: Watch status (fully_watched, partially_watched, unwatched, no_episodes)
        watched_episodes: Number of episodes watched by user
        completion_percentage: Percentage of episodes watched
        most_recent_watch: Most recent watch date
        days_since_watched: Days since most recent watch
        available_seasons: Comma-separated string of available season numbers
        total_size_on_disk: Total file size in bytes
    """

    id: int
    title: str
    year: Optional[int]
    tvdb_id: Optional[int]
    imdb_id: Optional[str]
    user: Optional[str]
    has_file: bool
    total_episodes: int
    downloaded_episodes: int
    added: Optional[str]
    monitored: bool
    status: Optional[str]
    seasons: List[dict]
    tags: List[int]
    statistics: dict
    watch_status: str = "unwatched"
    watched_episodes: int = 0
    completion_percentage: float = 0.0
    most_recent_watch: Optional[datetime] = None
    days_since_watched: Optional[int] = None
    available_seasons: str = ""
    total_size_on_disk: int = 0

    @property
    def is_fully_watched(self) -> bool:
        """Check if all episodes have been watched."""
        return self.watch_status == "fully_watched"

    @property
    def is_partially_watched(self) -> bool:
        """Check if some (but not all) episodes have been watched."""
        return self.watch_status == "partially_watched"

    @property
    def is_unwatched(self) -> bool:
        """Check if no episodes have been watched."""
        return self.watch_status == "unwatched"

    @property
    def has_no_episodes(self) -> bool:
        """Check if series has no episodes."""
        return self.watch_status == "no_episodes"

    @property
    def is_eligible_for_removal(self) -> bool:
        """
        Check if series is eligible for removal.

        A series is eligible if:
        - It is fully watched
        - It has a user association (not untagged)
        """
        return self.is_fully_watched and self.user is not None

    def is_watched_after_days(self, days: int) -> bool:
        """
        Check if series was last watched at least N days ago.

        Args:
            days: Minimum number of days since watched

        Returns:
            True if series was watched >= days ago, False otherwise
        """
        if not self.days_since_watched:
            return False
        return self.days_since_watched >= days

    @classmethod
    def from_dict(cls, data: dict) -> Series:
        """
        Create Series instance from dictionary.

        Args:
            data: Dictionary containing series data

        Returns:
            Series instance
        """
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            year=data.get("year"),
            tvdb_id=data.get("tvdb_id"),
            imdb_id=data.get("imdb_id"),
            user=data.get("user"),
            has_file=data.get("has_file", False),
            total_episodes=data.get("total_episodes", 0),
            downloaded_episodes=data.get("downloaded_episodes", 0),
            added=data.get("added"),
            monitored=data.get("monitored", False),
            status=data.get("status"),
            seasons=data.get("seasons", []),
            tags=data.get("tags", []),
            statistics=data.get("statistics", {}),
            watch_status=data.get("watch_status", "unwatched"),
            watched_episodes=data.get("watched_episodes", 0),
            completion_percentage=data.get("completion_percentage", 0.0),
            most_recent_watch=data.get("most_recent_watch"),
            days_since_watched=data.get("days_since_watched"),
            available_seasons=data.get("available_seasons", ""),
            total_size_on_disk=data.get("total_size_on_disk", 0),
        )

    def to_dict(self) -> dict:
        """
        Convert Series instance to dictionary.

        Returns:
            Dictionary representation of series
        """
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "tvdb_id": self.tvdb_id,
            "imdb_id": self.imdb_id,
            "user": self.user,
            "has_file": self.has_file,
            "total_episodes": self.total_episodes,
            "downloaded_episodes": self.downloaded_episodes,
            "added": self.added,
            "monitored": self.monitored,
            "status": self.status,
            "seasons": self.seasons,
            "tags": self.tags,
            "statistics": self.statistics,
            "watch_status": self.watch_status,
            "watched_episodes": self.watched_episodes,
            "completion_percentage": self.completion_percentage,
            "most_recent_watch": self.most_recent_watch,
            "days_since_watched": self.days_since_watched,
            "available_seasons": self.available_seasons,
            "total_size_on_disk": self.total_size_on_disk,
        }
