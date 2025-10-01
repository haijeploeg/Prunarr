"""
Watch history domain models for Tautulli integration.

Provides strongly-typed representations of watch history records
and watch status information.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class WatchStatus(Enum):
    """
    Enumeration of possible watch status values.

    Attributes:
        FULLY_WATCHED: Content was fully watched (100% completion)
        PARTIALLY_WATCHED: Content was partially watched
        STOPPED: Content was stopped before completion
        UNWATCHED: Content has not been watched
    """

    FULLY_WATCHED = 1
    PARTIALLY_WATCHED = 0
    STOPPED = -1
    UNWATCHED = -2

    @classmethod
    def from_tautulli_code(cls, code: int) -> WatchStatus:
        """
        Convert Tautulli watch status code to WatchStatus enum.

        Args:
            code: Tautulli status code (1=fully watched, 0=partial, other=stopped)

        Returns:
            WatchStatus enum value
        """
        if code == 1:
            return cls.FULLY_WATCHED
        elif code == 0:
            return cls.PARTIALLY_WATCHED
        else:
            return cls.STOPPED


@dataclass
class WatchHistory:
    """
    Represents a watch history record from Tautulli.

    Attributes:
        history_id: Unique history record ID
        rating_key: Plex rating key
        title: Content title
        user: Username who watched
        user_id: User ID
        media_type: Type of media (movie, show, episode)
        year: Release year
        watched_status: Watch status code (1=watched, 0=partial, other=stopped)
        progress: Watch progress percentage
        duration: Total duration in seconds
        watched_at: Timestamp when watched
        platform: Platform used for watching
        player: Player name
        grandparent_rating_key: Parent rating key (for episodes)
        parent_rating_key: Season rating key (for episodes)
        season_num: Season number (for episodes)
        episode_num: Episode number (for episodes)
        imdb_id: IMDB identifier
        tvdb_id: TVDB identifier
        bandwidth: Streaming bandwidth
        location: Watch location
        metadata: Additional metadata dictionary
    """

    history_id: int
    rating_key: str
    title: str
    user: str
    user_id: int
    media_type: str
    year: Optional[int]
    watched_status: int
    progress: int
    duration: int
    watched_at: str
    platform: Optional[str]
    player: Optional[str]
    grandparent_rating_key: Optional[str] = None
    parent_rating_key: Optional[str] = None
    season_num: Optional[int] = None
    episode_num: Optional[int] = None
    imdb_id: Optional[str] = None
    tvdb_id: Optional[str] = None
    bandwidth: Optional[int] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values for mutable attributes."""
        if self.metadata is None:
            self.metadata = {}

    @property
    def status(self) -> WatchStatus:
        """Get WatchStatus enum from watched_status code."""
        return WatchStatus.from_tautulli_code(self.watched_status)

    @property
    def is_fully_watched(self) -> bool:
        """Check if content was fully watched."""
        return self.watched_status == 1

    @property
    def is_partially_watched(self) -> bool:
        """Check if content was partially watched."""
        return self.watched_status == 0

    @property
    def is_stopped(self) -> bool:
        """Check if content was stopped."""
        return self.watched_status not in [0, 1]

    @property
    def watched_datetime(self) -> Optional[datetime]:
        """Convert watched_at timestamp to datetime."""
        try:
            return datetime.fromtimestamp(int(self.watched_at))
        except (ValueError, TypeError):
            return None

    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return self.duration // 60 if self.duration else 0

    @property
    def is_movie(self) -> bool:
        """Check if this is a movie watch record."""
        return self.media_type == "movie"

    @property
    def is_episode(self) -> bool:
        """Check if this is an episode watch record."""
        return self.media_type == "episode"

    @property
    def is_show(self) -> bool:
        """Check if this is a show watch record."""
        return self.media_type == "show"

    @classmethod
    def from_dict(cls, data: dict) -> WatchHistory:
        """
        Create WatchHistory instance from dictionary.

        Args:
            data: Dictionary containing watch history data

        Returns:
            WatchHistory instance
        """
        return cls(
            history_id=data.get("history_id") or data.get("id"),
            rating_key=data.get("rating_key", ""),
            title=data.get("title", ""),
            user=data.get("user", ""),
            user_id=data.get("user_id", 0),
            media_type=data.get("media_type", ""),
            year=data.get("year"),
            watched_status=data.get("watched_status", -1),
            progress=data.get("progress", 0),
            duration=data.get("duration", 0),
            watched_at=data.get("watched_at", ""),
            platform=data.get("platform"),
            player=data.get("player"),
            grandparent_rating_key=data.get("grandparent_rating_key"),
            parent_rating_key=data.get("parent_rating_key"),
            season_num=data.get("season_num"),
            episode_num=data.get("episode_num"),
            imdb_id=data.get("imdb_id"),
            tvdb_id=data.get("tvdb_id"),
            bandwidth=data.get("bandwidth"),
            location=data.get("location"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict:
        """
        Convert WatchHistory instance to dictionary.

        Returns:
            Dictionary representation of watch history
        """
        return {
            "history_id": self.history_id,
            "rating_key": self.rating_key,
            "title": self.title,
            "user": self.user,
            "user_id": self.user_id,
            "media_type": self.media_type,
            "year": self.year,
            "watched_status": self.watched_status,
            "progress": self.progress,
            "duration": self.duration,
            "watched_at": self.watched_at,
            "platform": self.platform,
            "player": self.player,
            "grandparent_rating_key": self.grandparent_rating_key,
            "parent_rating_key": self.parent_rating_key,
            "season_num": self.season_num,
            "episode_num": self.episode_num,
            "imdb_id": self.imdb_id,
            "tvdb_id": self.tvdb_id,
            "bandwidth": self.bandwidth,
            "location": self.location,
            "metadata": self.metadata,
        }
