"""
Domain models for PrunArr application.

This module provides strongly-typed domain models that represent the core
business entities of the application, ensuring type safety and validation
throughout the codebase.
"""

from prunarr.models.episode import Episode, Season
from prunarr.models.movie import Movie
from prunarr.models.series import Series
from prunarr.models.watch_history import WatchHistory, WatchStatus

__all__ = [
    "Episode",
    "Season",
    "Movie",
    "Series",
    "WatchHistory",
    "WatchStatus",
]
