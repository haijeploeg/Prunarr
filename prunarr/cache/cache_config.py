"""
Cache configuration module for PrunArr.

Defines cache settings including TTL values for different data types
and cache storage locations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CacheConfig:
    """
    Configuration for PrunArr cache system.

    Attributes:
        enabled: Whether caching is enabled
        cache_dir: Directory for cache storage
        ttl_movies: TTL for Radarr movie data (seconds)
        ttl_series: TTL for Sonarr series data (seconds)
        ttl_history: TTL for Tautulli watch history (seconds)
        ttl_tags: TTL for Radarr/Sonarr tags (seconds)
        ttl_metadata: TTL for IMDB/TVDB metadata (seconds)
        max_size_mb: Maximum cache size in megabytes (0 = unlimited)
    """

    enabled: bool = True
    cache_dir: Optional[Path] = None
    ttl_movies: int = 3600  # 1 hour
    ttl_series: int = 3600  # 1 hour
    ttl_history: int = 300  # 5 minutes
    ttl_tags: int = 86400  # 24 hours
    ttl_metadata: int = 604800  # 7 days
    max_size_mb: int = 100  # 100 MB max cache size

    def __post_init__(self):
        """Set default cache directory if not specified."""
        if self.cache_dir is None:
            self.cache_dir = Path.home() / ".prunarr" / "cache"
        elif isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir).expanduser()

        # Ensure cache directory exists
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_settings(cls, settings: dict) -> "CacheConfig":
        """
        Create CacheConfig from settings dictionary.

        Args:
            settings: Dictionary with cache configuration

        Returns:
            CacheConfig instance
        """
        return cls(
            enabled=settings.get("cache_enabled", True),
            cache_dir=settings.get("cache_dir"),
            ttl_movies=settings.get("cache_ttl_movies", 3600),
            ttl_series=settings.get("cache_ttl_series", 3600),
            ttl_history=settings.get("cache_ttl_history", 300),
            ttl_tags=settings.get("cache_ttl_tags", 86400),
            ttl_metadata=settings.get("cache_ttl_metadata", 604800),
            max_size_mb=settings.get("cache_max_size_mb", 100),
        )
