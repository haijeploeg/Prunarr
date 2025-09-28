"""
Tautulli API client module for PrunArr CLI application.

This module provides a comprehensive interface to the Tautulli API for watch history
analysis and metadata extraction. It handles complex operations like paginated history
retrieval, metadata caching, and ID extraction from various media databases.

The TautulliAPI class provides:
- Advanced watch history retrieval with server-side filtering and pagination
- Metadata extraction and caching for performance optimization
- IMDB and TVDB ID extraction from media GUIDs
- Flexible filtering and sorting capabilities
- Comprehensive error handling and data validation
- Series metadata caching for efficient batch operations
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
import requests

# Compiled regex patterns for efficient ID extraction
IMDB_ID_PATTERN = re.compile(r"^imdb:\/\/(tt\d+)")
TVDB_ID_PATTERN = re.compile(r"^tvdb:\/\/(\d+)")


class TautulliAPI:
    """
    Advanced Tautulli API client with comprehensive watch history and metadata capabilities.

    This class provides a sophisticated interface to Tautulli's REST API, offering both
    high-level convenience methods and fine-grained control over data retrieval. It handles
    watch history analysis, metadata extraction, and media database ID resolution while
    providing robust error handling and performance optimization.

    The API client is designed to:
    - Handle large-scale watch history analysis with efficient pagination
    - Provide flexible filtering and sorting for complex queries
    - Extract and cache metadata for performance optimization
    - Support multiple media database ID formats (IMDB, TVDB)
    - Enable batch operations with intelligent caching strategies

    Attributes:
        base_url: Tautulli server base URL (normalized)
        api_key: Tautulli API key for authentication
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        """
        Initialize the Tautulli API client with server connection details.

        Args:
            base_url: Base URL of the Tautulli server (e.g., "http://localhost:8181")
            api_key: Tautulli API key for authentication

        Examples:
            >>> tautulli = TautulliAPI("http://localhost:8181", "your-api-key")
            >>> history = tautulli.get_watch_history(limit=100)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(self, cmd: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute authenticated API request to Tautulli server.

        This internal method handles the low-level communication with Tautulli's API,
        including authentication, parameter formatting, and response parsing.

        Args:
            cmd: Tautulli API command to execute
            params: Optional dictionary of command parameters

        Returns:
            Parsed JSON response data from Tautulli API

        Raises:
            requests.HTTPError: If API request fails or authentication is invalid
            requests.Timeout: If request exceeds timeout limit

        Note:
            All API requests automatically include authentication and are limited
            to 15-second timeout for reliability.
        """
        url = f"{self.base_url}/api/v2"
        params = params or {}
        params.update({"apikey": self.api_key, "cmd": cmd})

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json().get("response", {})

    def get_watch_history(
        self,
        page_size: int = 100,
        order_column: str = "date",
        order_dir: str = "desc",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve comprehensive watch history with advanced pagination and sorting.

        This method provides efficient access to Tautulli's watch history with support
        for server-side sorting, pagination, and intelligent limiting. It handles large
        datasets efficiently while maintaining data consistency and performance.

        Args:
            page_size: Number of records per API request (default: 100)
            order_column: Column to sort by (date, friendly_name, media_type, etc.)
            order_dir: Sort direction ("desc" or "asc")
            limit: Maximum number of records to return (None for all available)

        Returns:
            List of comprehensive watch history records with complete metadata

        Examples:
            Get recent watch history:
            >>> recent = tautulli.get_watch_history(limit=50)

            Get all history sorted by user:
            >>> by_user = tautulli.get_watch_history(order_column="friendly_name")

            Get large dataset efficiently:
            >>> large_dataset = tautulli.get_watch_history(page_size=500, limit=10000)

        Note:
            This method implements intelligent pagination to minimize API calls
            while respecting rate limits and server performance.
        """
        all_records: List[Dict[str, Any]] = []
        start = 0

        while True:
            # Calculate how many records to request this iteration
            current_page_size = page_size
            if limit and (limit - len(all_records)) < page_size:
                current_page_size = limit - len(all_records)

            params = {
                "length": current_page_size,
                "start": start,
                "order_column": order_column,
                "order_dir": order_dir,
            }

            resp = self._request("get_history", params=params)
            # Tautulli response structure: { "data": { "data": [ ... ] } }
            page_data = resp.get("data", {}).get("data", [])

            if not page_data:
                break

            all_records.extend(page_data)

            # Stop if we've reached our limit or got less than requested
            if limit and len(all_records) >= limit:
                break
            if len(page_data) < current_page_size:
                break

            start += current_page_size

        return all_records

    def get_movie_completed_history(self) -> List[Dict[str, Any]]:
        """
        Get completed movie watch history records sorted newest first.

        Returns records where watched_status == 1 and media_type == "movie",
        sorted by date descending using server-side sorting.
        """
        # Use server-side sorting for better performance
        all_records = self.get_watch_history(order_column="date", order_dir="desc")

        return [
            {
                "title": r.get("title"),
                "rating_key": r.get("rating_key"),
                "user": r.get("friendly_name"),
                "watched_at": r.get("date"),
                "watched_status": r.get("watched_status"),
                "media_type": r.get("media_type"),
            }
            for r in all_records
            if r.get("watched_status") == 1 and r.get("media_type") == "movie"
        ]

    def get_filtered_history(
        self,
        watched_only: bool = False,
        user_id: int | None = None,
        username: str | None = None,
        media_type: str | None = None,
        limit: int | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get filtered history based on specified criteria with server-side sorting.

        Args:
            watched_only: Only include fully watched items (watched_status == 1)
            user_id: Filter by specific user ID
            username: Filter by username (friendly_name)
            media_type: Filter by media type ('movie', 'show', 'episode')
            limit: Limit number of results (None for all)

        Returns:
            List of formatted history records sorted newest first by server
        """
        # Use server-side sorting (newest first) and smart limiting
        # We might need more records than the limit due to client-side filtering
        fetch_limit = None
        if limit:
            # Fetch more records to account for filtering, but cap at reasonable amount
            fetch_limit = min(limit * 3, 1000)

        # Get pre-sorted records from server (newest first by date)
        all_records = self.get_watch_history(
            order_column="date", order_dir="desc", limit=fetch_limit
        )

        filtered_records = []

        for record in all_records:
            # Apply client-side filters (server-side filtering not available for these criteria)

            # Filter by watched status
            if watched_only and record.get("watched_status") != 1:
                continue

            # Filter by user ID
            if user_id is not None and record.get("user_id") != user_id:
                continue

            # Filter by username (friendly_name)
            if username and record.get("friendly_name") != username:
                continue

            # Filter by media type
            if media_type and record.get("media_type") != media_type:
                continue

            # Format the record with relevant fields
            formatted_record = {
                "history_id": record.get("id"),
                "title": record.get("title"),
                "rating_key": record.get("rating_key"),
                "user": record.get("friendly_name"),
                "user_id": record.get("user_id"),
                "watched_at": record.get("date"),
                "stopped": record.get("stopped"),
                "watched_status": record.get("watched_status"),
                "media_type": record.get("media_type"),
                "year": record.get("year"),
                "duration": record.get("duration"),
                "percent_complete": record.get("percent_complete"),
                "ip_address": record.get("ip_address"),
                "platform": record.get("platform"),
                "player": record.get("player"),
            }
            filtered_records.append(formatted_record)

            # Apply limit after filtering (records are already sorted by server)
            if limit and len(filtered_records) >= limit:
                break

        return filtered_records

    def get_history_item_details(self, history_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific history item by searching through all history.

        Args:
            history_id: The history entry ID to find
        """
        # Get all history records and search for the matching ID
        all_records = self.get_watch_history()

        # Find the record with matching ID
        matching_record = None
        for record in all_records:
            if record.get("id") == history_id:
                matching_record = record
                break

        if not matching_record:
            return {}

        record = matching_record

        # Get additional metadata if available
        rating_key = record.get("rating_key")
        metadata = {}
        if rating_key:
            metadata = self.get_metadata(rating_key)

        # Combine history and metadata info
        return {
            "history_id": record.get("id"),
            "title": record.get("title"),
            "rating_key": record.get("rating_key"),
            "user": record.get("friendly_name"),
            "user_id": record.get("user_id"),
            "watched_at": record.get("date"),
            "started": record.get("started"),
            "stopped": record.get("stopped"),
            "paused_counter": record.get("paused_counter"),
            "watched_status": record.get("watched_status"),
            "media_type": record.get("media_type"),
            "year": record.get("year"),
            "duration": record.get("duration"),
            "percent_complete": record.get("percent_complete"),
            "ip_address": record.get("ip_address"),
            "platform": record.get("platform"),
            "player": record.get("player"),
            "bandwidth": record.get("bandwidth"),
            "location": record.get("location"),
            "secure": record.get("secure"),
            "relayed": record.get("relayed"),
            # From metadata
            "imdb_id": self.get_imdb_id_from_rating_key(rating_key) if rating_key else None,
            "summary": metadata.get("summary", ""),
            "rating": metadata.get("rating", ""),
            "content_rating": metadata.get("content_rating", ""),
            "studio": metadata.get("studio", ""),
            "genres": metadata.get("genres", []),
            "directors": metadata.get("directors", []),
            "writers": metadata.get("writers", []),
            "actors": metadata.get("actors", []),
        }

    def get_metadata(self, rating_key: str) -> Dict[str, Any]:
        """Haal metadata op van een item via rating_key."""
        resp = self._request("get_metadata", params={"rating_key": rating_key})
        return resp.get("data", {})

    def get_imdb_id_from_rating_key(self, rating_key: str) -> str | None:
        """
        Haal IMDb ID (tt...) uit metadata.guids wanneer beschikbaar.
        Retourneert bijvoorbeeld 'tt1234567' of None.
        """
        metadata = self.get_metadata(rating_key)
        for guid in metadata.get("guids", []) or []:
            m = IMDB_ID_PATTERN.match(guid)
            if m:
                return m.group(1)
        return None

    def get_episode_completed_history(self) -> List[Dict[str, Any]]:
        """
        Get completed episode watch history records sorted newest first.

        Returns records where watched_status == 1 and media_type == "episode",
        sorted by date descending using server-side sorting.
        """
        # Use server-side sorting for better performance
        all_records = self.get_watch_history(order_column="date", order_dir="desc")

        return [
            {
                "title": r.get("title"),
                "rating_key": r.get("rating_key"),
                "parent_rating_key": r.get("parent_rating_key"),
                "grandparent_rating_key": r.get("grandparent_rating_key"),
                "user": r.get("friendly_name"),
                "watched_at": r.get("date"),
                "watched_status": r.get("watched_status"),
                "media_type": r.get("media_type"),
                "season_num": r.get("parent_media_index"),
                "episode_num": r.get("media_index"),
                "series_title": r.get("grandparent_title"),
            }
            for r in all_records
            if r.get("watched_status") == 1 and r.get("media_type") == "episode"
        ]

    def get_tvdb_id_from_rating_key(self, rating_key: str) -> str | None:
        """
        Haal TVDB ID uit metadata.guids wanneer beschikbaar.
        Retourneert bijvoorbeeld '123456' of None.
        """
        metadata = self.get_metadata(rating_key)
        for guid in metadata.get("guids", []) or []:
            m = TVDB_ID_PATTERN.match(guid)
            if m:
                return m.group(1)
        return None

    def build_series_metadata_cache(self, episode_history: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Build a cache mapping grandparent_rating_key to tvdb_id for efficient lookups.

        Args:
            episode_history: List of episode history records

        Returns:
            Dictionary mapping grandparent_rating_key -> tvdb_id
        """
        series_cache = {}
        unique_series_keys = set()

        # Collect unique series (grandparent) rating keys
        for record in episode_history:
            grandparent_key = record.get("grandparent_rating_key")
            if grandparent_key and grandparent_key not in unique_series_keys:
                unique_series_keys.add(grandparent_key)

        # Get metadata for each unique series
        for series_key in unique_series_keys:
            try:
                metadata = self.get_metadata(str(series_key))
                tvdb_id = None

                for guid in metadata.get("guids", []) or []:
                    m = TVDB_ID_PATTERN.match(guid)
                    if m:
                        tvdb_id = m.group(1)
                        break

                if tvdb_id:
                    series_cache[str(series_key)] = tvdb_id

            except Exception as e:
                # Log error but continue with other series
                continue

        return series_cache
