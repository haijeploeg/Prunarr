"""
Sonarr API client module for PrunArr CLI application.

This module provides a comprehensive interface to the Sonarr API for TV series and episode
management operations. It wraps the pyarr library while adding advanced functionality for
episode tracking, file size management, and season-level operations.

The SonarrAPI class serves as an enhanced facade over pyarr.SonarrAPI, providing:
- Comprehensive series and episode retrieval with metadata
- Advanced episode file management and size tracking
- Season-based organization and statistics
- Direct API access for complex operations bypassing pyarr limitations
- Robust error handling and fallback mechanisms
- Detailed episode-to-file mapping for storage analysis
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from pyarr import SonarrAPI as PyarrSonarrAPI

from prunarr.api.base_client import BaseAPIClient

# Optional cache manager import
try:
    from prunarr.cache import CacheManager
except ImportError:
    CacheManager = None


class SonarrAPI(BaseAPIClient):
    """
    Enhanced Sonarr API client with comprehensive TV series and episode management capabilities.

    This class provides a sophisticated interface to Sonarr's REST API, offering both
    high-level convenience methods and direct API access for complex operations. It handles
    series retrieval, episode management, file tracking, and season statistics while
    providing robust error handling and data consistency.

    The API client is designed to:
    - Abstract pyarr implementation details while providing enhanced functionality
    - Support complex episode file mapping and size calculations
    - Handle direct HTTP API calls when pyarr limitations are encountered
    - Provide comprehensive episode and season metadata
    - Support advanced filtering and organization operations

    Attributes:
        _api: Internal pyarr SonarrAPI instance for standard operations
        _base_url: Sonarr server base URL (normalized)
        _api_key: Sonarr API key for authentication
        cache_manager: Optional cache manager for performance optimization
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        cache_manager: Optional["CacheManager"] = None,
        debug: bool = False,
        log_level: str = "ERROR",
    ) -> None:
        """
        Initialize the Sonarr API client with server connection details.

        Args:
            url: Base URL of the Sonarr server (e.g., "http://localhost:8989")
            api_key: Sonarr API key for authentication
            cache_manager: Optional cache manager for performance optimization
            debug: Enable debug logging
            log_level: Minimum log level to display

        Examples:
            >>> sonarr = SonarrAPI("http://localhost:8989", "your-api-key")
            >>> series = sonarr.get_series()
        """
        # Note: SonarrAPI uses _base_url and _api_key internally for direct API calls
        super().__init__(url, api_key, cache_manager, debug, log_level)
        self._base_url = self.base_url
        self._api_key = self.api_key

    def _get_logger_name(self) -> str:
        """Get the logger name for this API client."""
        return "prunarr.sonarr"

    def _initialize_client(self) -> None:
        """Initialize the underlying pyarr SonarrAPI client."""
        self._api = PyarrSonarrAPI(self.base_url, self.api_key)

    def get_series(self, series_id: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve TV series from Sonarr with optional filtering and detailed metadata.

        This method provides access to Sonarr's series collection with support for
        various filtering options. It can retrieve all series or specific series
        based on provided criteria. Results are cached if cache_manager is available.

        Args:
            series_id: Optional specific series ID to retrieve
            **kwargs: Additional query parameters passed to the Sonarr API

        Returns:
            List of series dictionaries containing complete series metadata including
            seasons, statistics, and file information

        Examples:
            Get all series:
            >>> series_list = sonarr.get_series()

            Get specific series:
            >>> series = sonarr.get_series(series_id=123)

            Get series with custom parameters:
            >>> monitored_series = sonarr.get_series(monitored=True)

        Raises:
            Exception: If API communication fails or authentication is invalid
        """
        # Only cache when retrieving all series
        if (
            series_id is None
            and not kwargs
            and self.cache_manager
            and self.cache_manager.is_enabled()
        ):
            return self.cache_manager.get_sonarr_series(lambda: self._api.get_series(**kwargs))

        if series_id is not None:
            return self._api.get_series(series_id, **kwargs)
        return self._api.get_series(**kwargs)

    def get_series_by_id(self, series_id: int) -> Dict[str, Any]:
        """
        Retrieve detailed information for a specific TV series.

        This method fetches comprehensive series data including seasons, episodes,
        statistics, and metadata for a single series identified by its Sonarr ID.
        Results are cached if cache_manager is available.

        Args:
            series_id: Unique Sonarr series identifier

        Returns:
            Dictionary containing complete series information including seasons,
            episode counts, file statistics, and metadata

        Examples:
            >>> series = sonarr.get_series_by_id(123)
            >>> print(series['title'])  # "Breaking Bad"
            >>> print(len(series['seasons']))  # Number of seasons

        Raises:
            Exception: If series doesn't exist or API communication fails
        """
        # Use cache if available
        if self.cache_manager and self.cache_manager.is_enabled():
            return self.cache_manager.get_sonarr_series_detail(
                series_id, lambda: self._api.get_series(series_id)
            )

        return self._api.get_series(series_id)

    def get_episode(self, series_id: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve episodes with optional series filtering and comprehensive metadata.

        This method provides access to episode data with support for series-specific
        filtering and various query parameters. It can retrieve all episodes or
        episodes for a specific series.

        Args:
            series_id: Optional series ID to filter episodes by
            **kwargs: Additional query parameters for episode filtering

        Returns:
            List of episode dictionaries containing metadata, file information,
            and watch status

        Examples:
            Get all episodes:
            >>> episodes = sonarr.get_episode()

            Get episodes for specific series:
            >>> series_episodes = sonarr.get_episode(series_id=123)

            Get episodes with custom filters:
            >>> monitored = sonarr.get_episode(monitored=True)

        Note:
            For large series collections, consider using series-specific queries
            to improve performance and reduce API response times.
        """
        if series_id:
            return self._api.get_episode(series=series_id, **kwargs)
        return self._api.get_episode(**kwargs)

    def get_episodes_by_series_id(self, series_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all episodes for a specific series using direct API access.

        This method uses direct HTTP calls to Sonarr's API to bypass potential
        limitations in the pyarr library. It provides comprehensive episode data
        including file information and metadata, with multiple fallback mechanisms
        for maximum reliability. Results are cached if cache_manager is available.

        Args:
            series_id: Sonarr series ID to retrieve episodes for

        Returns:
            List of episode dictionaries with complete metadata, file information,
            and season organization data

        Examples:
            >>> episodes = sonarr.get_episodes_by_series_id(123)
            >>> print(f"Found {len(episodes)} episodes")
            >>> for ep in episodes:
            ...     print(f"S{ep['seasonNumber']}E{ep['episodeNumber']}: {ep['title']}")

        Note:
            This method implements multiple fallback strategies:
            1. Direct HTTP API call (primary)
            2. pyarr with seriesId parameter (fallback 1)
            3. pyarr with series parameter (fallback 2)
            4. Empty list if all methods fail (graceful degradation)
        """
        # Use cache if available
        if self.cache_manager and self.cache_manager.is_enabled():
            return self.cache_manager.get_sonarr_episodes(
                series_id, lambda: self._fetch_episodes(series_id)
            )

        return self._fetch_episodes(series_id)

    def _fetch_episodes(self, series_id: int) -> List[Dict[str, Any]]:
        """
        Internal method to fetch episodes (extracted for caching).

        Args:
            series_id: Sonarr series ID

        Returns:
            List of episode dictionaries
        """
        try:
            # Primary method: Direct HTTP call to Sonarr API bypassing pyarr limitations
            url = f"{self._base_url}/api/v3/episode"
            params = {"seriesId": series_id, "includeImages": "false", "apikey": self._api_key}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            episodes = response.json()

            if isinstance(episodes, list):
                return episodes
            elif isinstance(episodes, dict):
                return [episodes]
            else:
                return []

        except Exception:
            # Fallback 1: pyarr with seriesId parameter
            try:
                episodes = self._api.get_episode(seriesId=series_id)
                if isinstance(episodes, list):
                    return episodes
                elif isinstance(episodes, dict):
                    return [episodes]
                else:
                    return []
            except Exception:
                try:
                    # Fallback 2: pyarr with series parameter (older versions)
                    episodes = self._api.get_episode(series=series_id)
                    if isinstance(episodes, list):
                        return episodes
                    elif isinstance(episodes, dict):
                        return [episodes]
                    else:
                        return []
                except Exception:
                    # Graceful degradation: return empty list if all methods fail
                    return []

    def get_tag(self, tag_id: int) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific Sonarr tag.

        Tags in Sonarr are used to organize and categorize series. This method
        retrieves the complete tag information including label and associated metadata.
        Results are cached if cache_manager is available.

        Args:
            tag_id: Unique identifier of the tag to retrieve

        Returns:
            Dictionary containing tag information with keys like 'id', 'label'

        Examples:
            >>> tag = sonarr.get_tag(5)
            >>> print(tag['label'])  # "user123 - john_doe"

        Raises:
            Exception: If tag doesn't exist or API communication fails
        """
        # Use cache if available
        if self.cache_manager and self.cache_manager.is_enabled():
            return self.cache_manager.get_sonarr_tag(tag_id, lambda: self._api.get_tag(tag_id))

        return self._api.get_tag(tag_id)

    def delete_series(
        self, series_id: int, delete_files: bool = True, add_exclusion: bool = False
    ) -> bool:
        """
        Delete a TV series from Sonarr with comprehensive options.

        This method safely removes a series from Sonarr's database and optionally
        deletes the associated files from disk. It provides fine-grained control
        over the deletion process with proper error handling.

        Args:
            series_id: Unique Sonarr series ID to delete
            delete_files: Whether to delete series files from disk (default: True)
            add_exclusion: Whether to add series to exclusion list (default: False)

        Returns:
            True if deletion was successful, False if it failed

        Examples:
            Delete series and files:
            >>> success = sonarr.delete_series(123)

            Delete from Sonarr but keep files:
            >>> success = sonarr.delete_series(123, delete_files=False)

            Delete and exclude from future imports:
            >>> success = sonarr.delete_series(123, add_exclusion=True)

        Note:
            This operation is irreversible when delete_files=True. Use with caution.
            All episodes and season data will be permanently removed.
        """
        try:
            return self._api.del_series(
                series_id, delete_files=delete_files, add_exclusion=add_exclusion
            )
        except Exception:
            # Log the exception in production code, but return False for now
            return False

    def delete_episode_file(self, episode_file_id: int) -> bool:
        """
        Delete individual episode file from Sonarr.

        Uses DELETE /api/v3/episodefile/{id} endpoint to remove a specific
        episode file from both Sonarr's database and disk storage.

        Args:
            episode_file_id: Unique episode file ID to delete

        Returns:
            True if deletion was successful, False otherwise

        Examples:
            Delete a single episode file:
            >>> success = sonarr.delete_episode_file(12345)

        Note:
            This operation is irreversible. The file will be permanently
            deleted from disk. Multi-episode files will delete all episodes
            contained in that file.
        """
        try:
            url = f"{self._base_url}/api/v3/episodefile/{episode_file_id}"
            response = requests.delete(url, params={"apikey": self._api_key}, timeout=30)
            return response.status_code in [200, 204]
        except Exception as e:
            self.logger.error(f"Failed to delete episode file {episode_file_id}: {e}")
            return False

    def unmonitor_episodes(self, episode_ids: List[int]) -> bool:
        """
        Unmonitor specific episodes in Sonarr.

        Uses PUT /api/v3/episode/monitor endpoint to set multiple episodes
        to unmonitored state, preventing them from being re-downloaded.

        Args:
            episode_ids: List of episode IDs to unmonitor

        Returns:
            True if successful, False otherwise

        Examples:
            Unmonitor multiple episodes:
            >>> success = sonarr.unmonitor_episodes([101, 102, 103])

        Note:
            Episodes must exist in Sonarr. Invalid IDs will be ignored.
            Unmonitored episodes will not be automatically downloaded.
        """
        if not episode_ids:
            return True

        try:
            url = f"{self._base_url}/api/v3/episode/monitor"
            response = requests.put(
                url,
                params={"apikey": self._api_key},
                json={"episodeIds": episode_ids, "monitored": False},
                timeout=30,
            )
            return response.status_code == 202
        except Exception as e:
            self.logger.error(f"Failed to unmonitor episodes: {e}")
            return False

    def unmonitor_season(self, series_id: int, season_number: int) -> bool:
        """
        Unmonitor all episodes in a specific season.

        Retrieves all episodes for the specified season and sets them to
        unmonitored state, preventing automatic downloads.

        Args:
            series_id: Unique Sonarr series identifier
            season_number: Season number to unmonitor (0 for specials)

        Returns:
            True if successful, False otherwise

        Examples:
            Unmonitor season 1:
            >>> success = sonarr.unmonitor_season(123, 1)

            Unmonitor specials:
            >>> success = sonarr.unmonitor_season(123, 0)

        Note:
            This affects all episodes in the season, regardless of their
            current monitored state or whether they have files.
        """
        try:
            # Get all episodes for the series
            episodes = self.get_episodes(series_id=series_id)
            episode_ids = [ep["id"] for ep in episodes if ep.get("seasonNumber") == season_number]

            if not episode_ids:
                self.logger.warning(
                    f"No episodes found for series {series_id} season {season_number}"
                )
                return True

            return self.unmonitor_episodes(episode_ids)
        except Exception as e:
            self.logger.error(
                f"Failed to unmonitor season {season_number} of series {series_id}: {e}"
            )
            return False

    def delete_season_files(
        self, series_id: int, season_number: int, unmonitor: bool = True
    ) -> bool:
        """
        Delete all episode files for a specific season.

        Removes all episode files belonging to the specified season from both
        Sonarr's database and disk storage. Optionally unmonitors the season
        to prevent re-downloading.

        Args:
            series_id: Unique Sonarr series identifier
            season_number: Season number to delete (0 for specials)
            unmonitor: Whether to unmonitor the season after deletion (default: True)

        Returns:
            True if all files deleted successfully, False if any deletion failed

        Examples:
            Delete season 1 and unmonitor:
            >>> success = sonarr.delete_season_files(123, 1)

            Delete season 2 but keep monitored:
            >>> success = sonarr.delete_season_files(123, 2, unmonitor=False)

        Note:
            This operation is irreversible. All files for the season will be
            permanently deleted from disk. Multi-episode files spanning multiple
            seasons will only be deleted if all contained episodes are in the
            target season.
        """
        try:
            # Get episode files for this series
            episode_files = self.get_episode_files(series_id=series_id)

            # Filter to files containing episodes from this season only
            season_file_ids = set()
            for ep_file in episode_files:
                # Check if ALL episodes in this file belong to the target season
                episodes_in_file = ep_file.get("episodes", [])
                if not episodes_in_file:
                    continue

                all_in_season = all(
                    ep.get("seasonNumber") == season_number for ep in episodes_in_file
                )

                if all_in_season:
                    season_file_ids.add(ep_file["id"])

            if not season_file_ids:
                self.logger.warning(
                    f"No episode files found for series {series_id} season {season_number}"
                )
                return True

            # Delete each unique file
            all_success = True
            for file_id in season_file_ids:
                if not self.delete_episode_file(file_id):
                    all_success = False
                    self.logger.error(f"Failed to delete episode file {file_id}")

            # Unmonitor season if requested and deletions were successful
            if unmonitor and all_success:
                self.unmonitor_season(series_id, season_number)

            return all_success
        except Exception as e:
            self.logger.error(
                f"Failed to delete season {season_number} files for series {series_id}: {e}"
            )
            return False

    def get_season_info(self, series_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve comprehensive season information for a specific TV series.

        This method extracts detailed season data from a series, including episode
        counts, file statistics, and monitoring status for each season.

        Args:
            series_id: Unique Sonarr series identifier

        Returns:
            List of season dictionaries containing episode counts, file statistics,
            and metadata for each season in the series

        Examples:
            >>> seasons = sonarr.get_season_info(123)
            >>> for season in seasons:
            ...     print(f"Season {season['seasonNumber']}: {season['statistics']['episodeCount']} episodes")

        Note:
            Season 0 typically contains specials and may have different
            episode counting behavior than regular seasons.
        """
        try:
            series = self.get_series_by_id(series_id)
            return series.get("seasons", [])
        except Exception:
            return []

    def get_episodes_with_files(self, series_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve episodes with comprehensive file and metadata information.

        This method provides detailed episode data including file status, download
        information, and metadata. It can retrieve episodes for all series or
        filter by a specific series ID.

        Args:
            series_id: Optional series ID to filter episodes by

        Returns:
            List of standardized episode dictionaries containing file information,
            metadata, and download status

        Examples:
            Get all episodes with files:
            >>> all_episodes = sonarr.get_episodes_with_files()

            Get episodes for specific series:
            >>> series_episodes = sonarr.get_episodes_with_files(series_id=123)
            >>> downloaded = [ep for ep in series_episodes if ep['has_file']]

        Note:
            This method includes all episodes regardless of file availability,
            with the 'has_file' field indicating download status.
        """
        try:
            # Get episodes using appropriate method based on series_id
            if series_id:
                episodes = self._api.get_episode(series=series_id)
            else:
                episodes = self._api.get_episode()

            # Ensure episodes is a list for consistent processing
            if not isinstance(episodes, list):
                episodes = [episodes] if episodes else []

            # Transform to standardized format with comprehensive information
            episodes_with_info = []
            for episode in episodes:
                episodes_with_info.append(
                    {
                        "id": episode.get("id"),
                        "series_id": episode.get("seriesId"),
                        "season_number": episode.get("seasonNumber"),
                        "episode_number": episode.get("episodeNumber"),
                        "title": episode.get("title"),
                        "has_file": episode.get("hasFile", False),
                        "episode_file_id": episode.get("episodeFileId"),
                        "air_date": episode.get("airDate"),
                        "overview": episode.get("overview", ""),
                        "runtime": episode.get("runtime", 0),
                        "monitored": episode.get("monitored", False),
                        "downloaded": episode.get("hasFile", False),
                    }
                )

            return episodes_with_info
        except Exception:
            return []

    def get_episode_files(self, series_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve comprehensive episode file information including size and quality data.

        This method uses direct API access to get detailed file information for episodes,
        including file size, quality profiles, and file paths. Essential for storage
        analysis and file management operations.

        Args:
            series_id: Optional series ID to filter episode files by specific series

        Returns:
            List of episode file dictionaries containing file size, quality,
            path information, and episode associations

        Examples:
            Get all episode files:
            >>> files = sonarr.get_episode_files()
            >>> total_size = sum(f.get('size', 0) for f in files)

            Get files for specific series:
            >>> series_files = sonarr.get_episode_files(series_id=123)
            >>> print(f"Series has {len(series_files)} downloaded episodes")

        Note:
            File sizes are returned in bytes. Use appropriate formatting
            for human-readable display.
        """
        try:
            # Direct HTTP call to Sonarr API for comprehensive episode file data
            url = f"{self._base_url}/api/v3/episodefile"
            params = {"apikey": self._api_key}

            if series_id:
                params["seriesId"] = series_id

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            episode_files = response.json()

            if isinstance(episode_files, list):
                return episode_files
            elif isinstance(episode_files, dict):
                return [episode_files]
            else:
                return []

        except Exception:
            return []

    def get_series_episodes_summary(self, series_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive episode summary for a series organized by season.

        This method provides detailed analytics about a series' episodes, including
        season-by-season breakdown of episode counts, download status, and overall
        series statistics. Essential for series management and progress tracking.

        Args:
            series_id: Unique Sonarr series identifier

        Returns:
            Dictionary containing complete series summary with season breakdowns,
            episode counts, and download statistics

        Examples:
            >>> summary = sonarr.get_series_episodes_summary(123)
            >>> print(f"Series has {summary['total_seasons']} seasons")
            >>> print(f"Downloaded: {summary['downloaded_episodes']}/{summary['total_episodes']}")
            >>>
            >>> for season in summary['seasons']:
            ...     s_num = season['season_number']
            ...     downloaded = season['downloaded_episodes']
            ...     total = season['total_episodes']
            ...     print(f"Season {s_num}: {downloaded}/{total} episodes")

        Note:
            The summary includes all seasons including specials (season 0)
            and provides both individual season and series-wide statistics.
        """
        try:
            episodes = self.get_episodes_with_files(series_id)
            seasons_info = {}

            # Process episodes and organize by season
            for episode in episodes:
                season_num = episode.get("season_number")
                if season_num not in seasons_info:
                    seasons_info[season_num] = {
                        "season_number": season_num,
                        "episodes": [],
                        "total_episodes": 0,
                        "downloaded_episodes": 0,
                    }

                seasons_info[season_num]["episodes"].append(episode)
                seasons_info[season_num]["total_episodes"] += 1
                if episode.get("has_file"):
                    seasons_info[season_num]["downloaded_episodes"] += 1

            # Calculate series-wide statistics
            total_downloaded = sum(s["downloaded_episodes"] for s in seasons_info.values())
            total_episodes = sum(s["total_episodes"] for s in seasons_info.values())

            return {
                "series_id": series_id,
                "seasons": list(seasons_info.values()),
                "total_seasons": len(seasons_info),
                "total_episodes": total_episodes,
                "downloaded_episodes": total_downloaded,
            }
        except Exception:
            # Return empty summary structure on any error
            return {
                "series_id": series_id,
                "seasons": [],
                "total_seasons": 0,
                "total_episodes": 0,
                "downloaded_episodes": 0,
            }
