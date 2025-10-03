"""
Cache manager for PrunArr application.

Coordinates caching across different data types with appropriate TTL values
and provides high-level caching operations.
"""

import hashlib
from typing import Any, Callable, Dict, List, Optional

from prunarr.cache.cache_config import CacheConfig
from prunarr.cache.cache_store import CacheStore
from prunarr.logger import get_logger


class CacheManager:
    """
    High-level cache management for PrunArr.

    Provides convenient caching methods for different data types with
    automatic TTL handling and cache key generation.

    Attributes:
        config: Cache configuration
        store: Persistent cache storage
    """

    # Cache key prefixes for different data types
    KEY_RADARR_MOVIES = "radarr_movies"
    KEY_RADARR_MOVIE = "radarr_movie"
    KEY_SONARR_SERIES = "sonarr_series"
    KEY_SONARR_SERIES_DETAIL = "sonarr_series_detail"
    KEY_SONARR_EPISODES = "sonarr_episodes"
    KEY_TAUTULLI_HISTORY = "tautulli_history"
    KEY_RADARR_TAG = "radarr_tag"
    KEY_SONARR_TAG = "sonarr_tag"
    KEY_METADATA_IMDB = "metadata_imdb"
    KEY_METADATA_TVDB = "metadata_tvdb"

    def __init__(self, config: CacheConfig, debug: bool = False, log_level: str = "ERROR"):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration
            debug: Enable debug logging
            log_level: Minimum log level to display
        """
        self.config = config
        self.store = CacheStore(config.cache_dir) if config.enabled else None
        self.logger = get_logger("prunarr.cache", debug=debug, log_level=log_level)
        self.last_was_cache_hit = False  # Track if last operation was a cache hit

        if config.enabled:
            self.logger.debug(
                f"Cache initialized: dir={config.cache_dir}, max_size={config.max_size_mb}MB"
            )

    def _generate_key(self, prefix: str, *args) -> str:
        """
        Generate cache key from prefix and arguments.

        Args:
            prefix: Key prefix (e.g., "radarr_movies")
            *args: Additional arguments to include in key

        Returns:
            Cache key string
        """
        if not args:
            return prefix

        # Create hash of arguments for shorter keys
        key_data = "_".join(str(arg) for arg in args)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"{prefix}_{key_hash}"

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.config.enabled and self.store is not None

    def get_or_fetch(
        self, key_prefix: str, fetch_func: Callable[[], Any], ttl: int, *key_args
    ) -> Any:
        """
        Get data from cache or fetch if not available.

        Args:
            key_prefix: Cache key prefix
            fetch_func: Function to call if cache miss
            ttl: Time to live in seconds
            *key_args: Additional arguments for cache key

        Returns:
            Cached or freshly fetched data
        """
        if not self.is_enabled():
            self.logger.debug(f"Cache disabled, fetching: {key_prefix}")
            self.last_was_cache_hit = False
            return fetch_func()

        key = self._generate_key(key_prefix, *key_args)
        cached = self.store.get(key)

        if cached is not None:
            self.logger.debug(f"Cache HIT: {key}")
            self.last_was_cache_hit = True
            return cached.get("data")

        # Cache miss, fetch and store
        self.logger.debug(f"Cache MISS: {key}, fetching...")
        self.last_was_cache_hit = False
        data = fetch_func()
        self.store.set(key, data, ttl)
        self.logger.debug(f"Cached {key} (TTL: {ttl}s)")
        return data

    # Convenience methods for specific data types

    def get_radarr_movies(self, fetch_func: Callable[[], List[Dict]]) -> List[Dict]:
        """
        Get Radarr movies from cache or fetch.

        Args:
            fetch_func: Function to fetch movies

        Returns:
            List of movie dictionaries
        """
        return self.get_or_fetch(self.KEY_RADARR_MOVIES, fetch_func, self.config.ttl_movies)

    def get_sonarr_series(self, fetch_func: Callable[[], List[Dict]]) -> List[Dict]:
        """
        Get Sonarr series from cache or fetch.

        Args:
            fetch_func: Function to fetch series

        Returns:
            List of series dictionaries
        """
        return self.get_or_fetch(self.KEY_SONARR_SERIES, fetch_func, self.config.ttl_series)

    def get_sonarr_series_detail(self, series_id: int, fetch_func: Callable[[], Dict]) -> Dict:
        """
        Get individual Sonarr series details from cache or fetch.

        Args:
            series_id: Series ID
            fetch_func: Function to fetch series details

        Returns:
            Series dictionary with full details
        """
        return self.get_or_fetch(
            self.KEY_SONARR_SERIES_DETAIL, fetch_func, self.config.ttl_series, series_id
        )

    def get_sonarr_episodes(
        self, series_id: int, fetch_func: Callable[[], List[Dict]]
    ) -> List[Dict]:
        """
        Get episodes for a specific series from cache or fetch.

        Args:
            series_id: Series ID
            fetch_func: Function to fetch episodes

        Returns:
            List of episode dictionaries
        """
        return self.get_or_fetch(
            self.KEY_SONARR_EPISODES, fetch_func, self.config.ttl_series, series_id
        )

    def get_radarr_movie_detail(self, movie_id: int, fetch_func: Callable[[], Dict]) -> Dict:
        """
        Get individual Radarr movie details from cache or fetch.

        Args:
            movie_id: Movie ID
            fetch_func: Function to fetch movie details

        Returns:
            Movie dictionary with full details
        """
        return self.get_or_fetch(
            self.KEY_RADARR_MOVIE, fetch_func, self.config.ttl_movies, movie_id
        )

    def get_tautulli_history(
        self, fetch_func: Callable[[], List[Dict]], *filter_args
    ) -> List[Dict]:
        """
        Get Tautulli watch history from cache or fetch.

        Args:
            fetch_func: Function to fetch history
            *filter_args: Optional filter arguments for cache key

        Returns:
            List of history record dictionaries
        """
        return self.get_or_fetch(
            self.KEY_TAUTULLI_HISTORY, fetch_func, self.config.ttl_history, *filter_args
        )

    def get_radarr_tag(self, tag_id: int, fetch_func: Callable[[], Dict]) -> Dict:
        """
        Get Radarr tag from cache or fetch.

        Args:
            tag_id: Tag ID
            fetch_func: Function to fetch tag

        Returns:
            Tag dictionary
        """
        return self.get_or_fetch(self.KEY_RADARR_TAG, fetch_func, self.config.ttl_tags, tag_id)

    def get_sonarr_tag(self, tag_id: int, fetch_func: Callable[[], Dict]) -> Dict:
        """
        Get Sonarr tag from cache or fetch.

        Args:
            tag_id: Tag ID
            fetch_func: Function to fetch tag

        Returns:
            Tag dictionary
        """
        return self.get_or_fetch(self.KEY_SONARR_TAG, fetch_func, self.config.ttl_tags, tag_id)

    def get_metadata_imdb(self, rating_key: str, fetch_func: Callable[[], Dict]) -> Dict:
        """
        Get IMDB metadata from cache or fetch.

        Args:
            rating_key: Plex rating key
            fetch_func: Function to fetch metadata

        Returns:
            Metadata dictionary
        """
        return self.get_or_fetch(
            self.KEY_METADATA_IMDB, fetch_func, self.config.ttl_metadata, rating_key
        )

    def get_metadata_tvdb(self, rating_key: str, fetch_func: Callable[[], Dict]) -> Dict:
        """
        Get TVDB metadata from cache or fetch.

        Args:
            rating_key: Plex rating key
            fetch_func: Function to fetch metadata

        Returns:
            Metadata dictionary
        """
        return self.get_or_fetch(
            self.KEY_METADATA_TVDB, fetch_func, self.config.ttl_metadata, rating_key
        )

    def clear_all(self):
        """Clear all cached data."""
        if self.is_enabled():
            self.store.clear()

    def clear_movies(self):
        """Clear Radarr movie cache."""
        if self.is_enabled():
            self.store.clear(self.KEY_RADARR_MOVIES)

    def clear_series(self):
        """Clear Sonarr series cache (including details and episodes)."""
        if self.is_enabled():
            self.store.clear(self.KEY_SONARR_SERIES)
            self.store.clear(self.KEY_SONARR_SERIES_DETAIL)
            self.store.clear(self.KEY_SONARR_EPISODES)

    def clear_history(self):
        """Clear Tautulli history cache."""
        if self.is_enabled():
            self.store.clear(self.KEY_TAUTULLI_HISTORY)

    def clear_tags(self):
        """Clear tag caches."""
        if self.is_enabled():
            self.store.clear(self.KEY_RADARR_TAG)
            self.store.clear(self.KEY_SONARR_TAG)

    def clear_metadata(self):
        """Clear metadata caches."""
        if self.is_enabled():
            self.store.clear(self.KEY_METADATA_IMDB)
            self.store.clear(self.KEY_METADATA_TVDB)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.is_enabled():
            return {"enabled": False}

        stats = self.store.get_stats()
        stats["enabled"] = True
        stats["cache_dir"] = str(self.config.cache_dir)

        return stats

    def get_cache_info(self, key_prefix: str, *key_args) -> Optional[Dict]:
        """
        Get information about cached item.

        Args:
            key_prefix: Cache key prefix
            *key_args: Additional key arguments

        Returns:
            Cache info dictionary or None
        """
        if not self.is_enabled():
            return None

        key = self._generate_key(key_prefix, *key_args)
        return self.store.get_cache_info(key)
