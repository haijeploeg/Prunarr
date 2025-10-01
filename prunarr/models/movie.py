"""
Movie domain model for Radarr integration.

Provides a strongly-typed representation of movies with watch status,
user associations, and file information.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Movie:
    """
    Represents a movie from Radarr with associated metadata and watch status.

    Attributes:
        id: Radarr movie ID
        title: Movie title
        year: Release year
        imdb_id: IMDB identifier
        user: Associated username from tags (None if untagged)
        has_file: Whether movie file exists
        file_size: File size in bytes
        added: Date movie was added to Radarr
        monitored: Whether movie is monitored in Radarr
        tags: List of tag IDs
        watch_status: Watch status (watched, unwatched, watched_by_other)
        watched_by: Comma-separated list of users who watched
        watched_at: Most recent watch date
        days_since_watched: Days since most recent watch
        all_watchers: List of all users who watched this movie
    """

    id: int
    title: str
    year: Optional[int]
    imdb_id: Optional[str]
    user: Optional[str]
    has_file: bool
    file_size: int
    added: Optional[str]
    monitored: bool
    tags: List[int]
    watch_status: str = "unwatched"
    watched_by: Optional[str] = None
    watched_at: Optional[datetime] = None
    days_since_watched: Optional[int] = None
    all_watchers: List[str] = None

    def __post_init__(self):
        """Initialize default values for mutable attributes."""
        if self.all_watchers is None:
            self.all_watchers = []

    @property
    def is_watched(self) -> bool:
        """Check if movie was watched by the associated user."""
        return self.watch_status == "watched"

    @property
    def is_watched_by_other(self) -> bool:
        """Check if movie was watched by someone other than the associated user."""
        return self.watch_status == "watched_by_other"

    @property
    def is_unwatched(self) -> bool:
        """Check if movie has not been watched."""
        return self.watch_status == "unwatched"

    @property
    def is_eligible_for_removal(self) -> bool:
        """
        Check if movie is eligible for removal.

        A movie is eligible if:
        - It was watched by the associated user
        - It has a user association (not untagged)
        """
        return self.is_watched and self.user is not None

    def is_watched_after_days(self, days: int) -> bool:
        """
        Check if movie was watched at least N days ago.

        Args:
            days: Minimum number of days since watched

        Returns:
            True if movie was watched >= days ago, False otherwise
        """
        if not self.days_since_watched:
            return False
        return self.days_since_watched >= days

    @classmethod
    def from_dict(cls, data: dict) -> Movie:
        """
        Create Movie instance from dictionary.

        Args:
            data: Dictionary containing movie data

        Returns:
            Movie instance
        """
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            year=data.get("year"),
            imdb_id=data.get("imdb_id"),
            user=data.get("user"),
            has_file=data.get("has_file", False),
            file_size=data.get("file_size", 0),
            added=data.get("added"),
            monitored=data.get("monitored", False),
            tags=data.get("tags", []),
            watch_status=data.get("watch_status", "unwatched"),
            watched_by=data.get("watched_by"),
            watched_at=data.get("watched_at"),
            days_since_watched=data.get("days_since_watched"),
            all_watchers=data.get("all_watchers", []),
        )

    def to_dict(self) -> dict:
        """
        Convert Movie instance to dictionary.

        Returns:
            Dictionary representation of movie
        """
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "imdb_id": self.imdb_id,
            "user": self.user,
            "has_file": self.has_file,
            "file_size": self.file_size,
            "added": self.added,
            "monitored": self.monitored,
            "tags": self.tags,
            "watch_status": self.watch_status,
            "watched_by": self.watched_by,
            "watched_at": self.watched_at,
            "days_since_watched": self.days_since_watched,
            "all_watchers": self.all_watchers,
        }
