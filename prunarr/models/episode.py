"""
Episode and Season domain models for Sonarr integration.

Provides strongly-typed representations of TV episodes and seasons
with watch status and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Episode:
    """
    Represents a single TV episode with watch status and metadata.

    Attributes:
        season_number: Season number
        episode_number: Episode number
        episode_key: Standardized episode key (e.g., "s1e5")
        title: Episode title
        air_date: Air date string
        runtime: Runtime in minutes
        has_file: Whether episode file exists
        episode_file_id: Episode file ID
        watched: Whether episode was watched by associated user
        watched_at: Timestamp when watched
        watched_by: Username who watched
        watch_status: Watch status (watched_by_user, watched_by_others, unwatched)
        watched_by_user: Whether watched by associated user
        watched_by_others: Whether watched by other users
        all_watchers: List of all users who watched
        most_recent_watch: Most recent watch datetime
        days_since_watched: Days since most recent watch
        watchers_detail: Detailed watcher information dictionary
        overview: Episode overview/summary
        monitored: Whether episode is monitored
    """

    season_number: int
    episode_number: int
    episode_key: str
    title: str
    air_date: str
    runtime: int
    has_file: bool
    episode_file_id: Optional[int]
    watched: bool
    watched_at: Optional[str]
    watched_by: str
    watch_status: str
    watched_by_user: bool
    watched_by_others: bool
    all_watchers: List[str]
    most_recent_watch: Optional[datetime]
    days_since_watched: Optional[int]
    watchers_detail: Dict
    overview: str = ""
    monitored: bool = False

    @property
    def is_watched_by_user(self) -> bool:
        """Check if episode was watched by the associated user."""
        return self.watch_status == "watched_by_user"

    @property
    def is_watched_by_others(self) -> bool:
        """Check if episode was watched by other users only."""
        return self.watch_status == "watched_by_others"

    @property
    def is_unwatched(self) -> bool:
        """Check if episode has not been watched."""
        return self.watch_status == "unwatched"

    @classmethod
    def from_dict(cls, data: dict) -> Episode:
        """
        Create Episode instance from dictionary.

        Args:
            data: Dictionary containing episode data

        Returns:
            Episode instance
        """
        return cls(
            season_number=data.get("season_number"),
            episode_number=data.get("episode_number"),
            episode_key=data.get("episode_key"),
            title=data.get("title"),
            air_date=data.get("air_date", ""),
            runtime=data.get("runtime", 0),
            has_file=data.get("has_file", False),
            episode_file_id=data.get("episode_file_id"),
            watched=data.get("watched", False),
            watched_at=data.get("watched_at"),
            watched_by=data.get("watched_by", ""),
            watch_status=data.get("watch_status", "unwatched"),
            watched_by_user=data.get("watched_by_user", False),
            watched_by_others=data.get("watched_by_others", False),
            all_watchers=data.get("all_watchers", []),
            most_recent_watch=data.get("most_recent_watch"),
            days_since_watched=data.get("days_since_watched"),
            watchers_detail=data.get("watchers_detail", {}),
            overview=data.get("overview", ""),
            monitored=data.get("monitored", False),
        )

    def to_dict(self) -> dict:
        """
        Convert Episode instance to dictionary.

        Returns:
            Dictionary representation of episode
        """
        return {
            "season_number": self.season_number,
            "episode_number": self.episode_number,
            "episode_key": self.episode_key,
            "title": self.title,
            "air_date": self.air_date,
            "runtime": self.runtime,
            "has_file": self.has_file,
            "episode_file_id": self.episode_file_id,
            "watched": self.watched,
            "watched_at": self.watched_at,
            "watched_by": self.watched_by,
            "watch_status": self.watch_status,
            "watched_by_user": self.watched_by_user,
            "watched_by_others": self.watched_by_others,
            "all_watchers": self.all_watchers,
            "most_recent_watch": self.most_recent_watch,
            "days_since_watched": self.days_since_watched,
            "watchers_detail": self.watchers_detail,
            "overview": self.overview,
            "monitored": self.monitored,
        }


@dataclass
class Season:
    """
    Represents a TV season with aggregated episode information.

    Attributes:
        season_number: Season number
        episodes: List of Episode instances
        watched_by_user: Number of episodes watched by user
        watched_by_others: Number of episodes watched by others only
        unwatched: Number of unwatched episodes
        total_episodes: Total number of episodes
        completion_percentage: Percentage of episodes watched by user
        total_size: Total file size in bytes
    """

    season_number: int
    episodes: List[Episode]
    watched_by_user: int = 0
    watched_by_others: int = 0
    unwatched: int = 0
    total_episodes: int = 0
    completion_percentage: float = 0.0
    total_size: int = 0

    @property
    def is_fully_watched(self) -> bool:
        """Check if all episodes in season were watched by user."""
        return self.watched_by_user == self.total_episodes and self.total_episodes > 0

    @property
    def is_partially_watched(self) -> bool:
        """Check if some (but not all) episodes were watched by user."""
        return 0 < self.watched_by_user < self.total_episodes

    @property
    def is_unwatched(self) -> bool:
        """Check if no episodes were watched by user."""
        return self.watched_by_user == 0

    @classmethod
    def from_dict(cls, data: dict) -> Season:
        """
        Create Season instance from dictionary.

        Args:
            data: Dictionary containing season data

        Returns:
            Season instance
        """
        episodes = [Episode.from_dict(ep) for ep in data.get("episodes", [])]
        return cls(
            season_number=data.get("season_number"),
            episodes=episodes,
            watched_by_user=data.get("watched_by_user", 0),
            watched_by_others=data.get("watched_by_others", 0),
            unwatched=data.get("unwatched", 0),
            total_episodes=data.get("total_episodes", 0),
            completion_percentage=data.get("completion_percentage", 0.0),
            total_size=data.get("total_size", 0),
        )

    def to_dict(self) -> dict:
        """
        Convert Season instance to dictionary.

        Returns:
            Dictionary representation of season
        """
        return {
            "season_number": self.season_number,
            "episodes": [ep.to_dict() for ep in self.episodes],
            "watched_by_user": self.watched_by_user,
            "watched_by_others": self.watched_by_others,
            "unwatched": self.unwatched,
            "total_episodes": self.total_episodes,
            "completion_percentage": self.completion_percentage,
            "total_size": self.total_size,
        }
