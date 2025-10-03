"""
Persistent cache storage for PrunArr.

Handles reading and writing cache data to disk in JSON format with
compression support for large datasets.
"""

import gzip
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class CacheStore:
    """
    Persistent storage layer for cache data.

    Manages reading/writing cache data to disk with automatic expiration
    tracking and optional compression for large files.

    Attributes:
        cache_dir: Directory where cache files are stored
        compress: Whether to use gzip compression
    """

    CACHE_VERSION = "1.0"
    STATS_FILE = "cache_stats.json"

    def __init__(self, cache_dir: Path, compress: bool = True):
        """
        Initialize cache store.

        Args:
            cache_dir: Directory for cache storage
            compress: Enable gzip compression for cache files
        """
        self.cache_dir = cache_dir
        self.compress = compress
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize stats
        self.stats = self._load_stats()

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        suffix = ".json.gz" if self.compress else ".json"
        return self.cache_dir / f"{key}{suffix}"

    def _load_stats(self) -> Dict[str, Any]:
        """Load cache statistics from disk."""
        stats_path = self.cache_dir / self.STATS_FILE
        if stats_path.exists():
            try:
                with open(stats_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "version": self.CACHE_VERSION,
            "hits": 0,
            "misses": 0,
            "last_accessed": int(time.time()),
        }

    def _save_stats(self):
        """Save cache statistics to disk."""
        stats_path = self.cache_dir / self.STATS_FILE
        try:
            with open(stats_path, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass  # Non-critical, don't fail on stats save error

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data by key.

        Args:
            key: Cache key

        Returns:
            Cached data dictionary or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            self.stats["misses"] += 1
            self._save_stats()
            return None

        try:
            # Read and decompress if needed
            if self.compress:
                with gzip.open(cache_path, "rt", encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

            # Check if expired
            if cache_data.get("expires_at", 0) < time.time():
                self.delete(key)
                self.stats["misses"] += 1
                self._save_stats()
                return None

            self.stats["hits"] += 1
            self.stats["last_accessed"] = int(time.time())
            self._save_stats()

            return cache_data

        except Exception:
            # Corrupted cache file, delete it
            self.delete(key)
            self.stats["misses"] += 1
            self._save_stats()
            return None

    def set(self, key: str, data: Any, ttl: int):
        """
        Store data in cache with TTL.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        cache_path = self._get_cache_path(key)
        timestamp = int(time.time())

        cache_data = {
            "version": self.CACHE_VERSION,
            "data": data,
            "timestamp": timestamp,
            "ttl": ttl,
            "expires_at": timestamp + ttl,
        }

        try:
            # Write and compress if needed
            if self.compress:
                with gzip.open(cache_path, "wt", encoding="utf-8") as f:
                    json.dump(cache_data, f)
            else:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
        except Exception:
            pass  # Non-critical, cache write failure shouldn't break the app

    def delete(self, key: str):
        """
        Delete cached data by key.

        Args:
            key: Cache key to delete
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                cache_path.unlink()
            except Exception:
                pass  # Non-critical

    def clear(self, pattern: Optional[str] = None):
        """
        Clear cache files matching pattern.

        Args:
            pattern: Glob pattern to match cache files (None = all)
        """
        if pattern:
            files = self.cache_dir.glob(f"{pattern}*")
        else:
            files = self.cache_dir.glob("*.json*")

        for file in files:
            if file.name != self.STATS_FILE:
                try:
                    file.unlink()
                except Exception:
                    pass  # Non-critical

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        stats = self.stats.copy()

        # Calculate cache size
        total_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.json*")
            if f.name != self.STATS_FILE
        )
        stats["size_bytes"] = total_size
        stats["size_mb"] = round(total_size / (1024 * 1024), 2)

        # Count cache files
        stats["file_count"] = len(list(self.cache_dir.glob("*.json*"))) - 1  # Exclude stats file

        return stats

    def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about cached item without loading data.

        Args:
            key: Cache key

        Returns:
            Dictionary with cache metadata or None
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            if self.compress:
                with gzip.open(cache_path, "rt", encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

            timestamp = cache_data.get("timestamp", 0)
            expires_at = cache_data.get("expires_at", 0)
            ttl = cache_data.get("ttl", 0)

            return {
                "key": key,
                "timestamp": timestamp,
                "expires_at": expires_at,
                "ttl": ttl,
                "age_seconds": int(time.time()) - timestamp,
                "expires_in_seconds": max(0, expires_at - int(time.time())),
                "expired": expires_at < time.time(),
                "size_bytes": cache_path.stat().st_size,
            }
        except Exception:
            return None
