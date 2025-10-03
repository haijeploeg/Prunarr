"""
Core orchestration module for PrunArr CLI application.

This module contains the main PrunArr class that orchestrates interactions between
Radarr, Sonarr, and Tautulli APIs to provide comprehensive media library management
and cleanup functionality. It handles complex operations like cross-referencing
watch status with media libraries and user-based content management.

The PrunArr class serves as the central coordinator for:
- Cross-API data correlation and analysis
- User tag parsing and management
- Watch status determination and tracking
- Media library organization and cleanup operations
- Series and movie management with detailed statistics
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from prunarr.config import Settings
from prunarr.logger import get_logger
from prunarr.radarr import RadarrAPI
from prunarr.sonarr import SonarrAPI
from prunarr.tautulli import TautulliAPI
from prunarr.utils import make_episode_key
from prunarr.services import MediaMatcher, UserService, WatchCalculator
from prunarr.cache import CacheManager, CacheConfig


class PrunArr:
    """
    Core orchestration class for media library management and cleanup operations.

    This class serves as the central coordinator between Radarr, Sonarr, and Tautulli,
    providing comprehensive media management capabilities including watch status tracking,
    user-based organization, and automated cleanup operations.

    The PrunArr orchestrator handles:
    - Multi-API coordination and data correlation
    - User tag extraction and validation using configurable regex patterns
    - Watch status determination across different media types
    - Complex filtering and organization operations
    - Series and movie statistics with file size tracking
    - Cleanup eligibility determination based on watch history

    Attributes:
        settings: Application configuration and API credentials
        radarr: Radarr API client for movie management
        sonarr: Sonarr API client for TV series management
        tautulli: Tautulli API client for watch history analysis
        tag_pattern: Compiled regex for user tag extraction
    """

    def __init__(self, settings: Settings, debug: bool = False) -> None:
        """
        Initialize PrunArr orchestrator with API clients and configuration.

        Args:
            settings: Validated application settings containing API credentials
                     and configuration options
            debug: Enable debug logging

        Examples:
            >>> from prunarr.config import load_settings
            >>> settings = load_settings("config.yaml")
            >>> prunarr = PrunArr(settings)
            >>> movies = prunarr.get_movies_with_watch_status()
        """
        self.settings = settings
        # Get log level from settings, but --debug flag always overrides
        log_level = settings.log_level if hasattr(settings, "log_level") else "ERROR"
        self.logger = get_logger("prunarr.core", debug=debug, log_level=log_level)

        # Initialize cache manager from settings
        cache_config = CacheConfig(
            enabled=settings.cache_enabled,
            cache_dir=settings.cache_dir,
            ttl_movies=settings.cache_ttl_movies,
            ttl_series=settings.cache_ttl_series,
            ttl_history=settings.cache_ttl_history,
            ttl_tags=settings.cache_ttl_tags,
            ttl_metadata=settings.cache_ttl_metadata,
            max_size_mb=settings.cache_max_size_mb,
        )
        self.cache_manager = (
            CacheManager(cache_config, debug=debug, log_level=log_level)
            if cache_config.enabled
            else None
        )

        if self.cache_manager:
            self.logger.debug(
                f"Cache enabled: {cache_config.cache_dir} (TTL: movies={cache_config.ttl_movies}s, series={cache_config.ttl_series}s, history={cache_config.ttl_history}s)"
            )
        else:
            self.logger.debug("Cache disabled")

        # Initialize API clients with cache manager, debug flag, and log level
        self.radarr = RadarrAPI(
            settings.radarr_url,
            settings.radarr_api_key,
            self.cache_manager,
            debug=debug,
            log_level=log_level,
        )
        self.sonarr = SonarrAPI(
            settings.sonarr_url,
            settings.sonarr_api_key,
            self.cache_manager,
            debug=debug,
            log_level=log_level,
        )
        self.tautulli = TautulliAPI(
            settings.tautulli_url,
            settings.tautulli_api_key,
            self.cache_manager,
            debug=debug,
            log_level=log_level,
        )
        self.tag_pattern = re.compile(settings.user_tag_regex)

        # Initialize service layer
        self.user_service = UserService(settings.user_tag_regex)
        self.media_matcher = MediaMatcher()
        self.watch_calculator = WatchCalculator()

    def check_and_log_cache_status(self, cache_key: str, logger) -> bool:
        """
        Check if data was cached and log hint if so.

        This helper method consolidates the common pattern of checking
        cache status and logging a hint to the user when cached data is used.

        Args:
            cache_key: Cache key to check (e.g., KEY_RADARR_MOVIES, KEY_SONARR_SERIES)
            logger: Logger instance to use for logging the cache hint

        Returns:
            True if data was cached, False otherwise

        Examples:
            >>> was_cached = prunarr.check_and_log_cache_status(
            ...     prunarr.cache_manager.KEY_RADARR_MOVIES,
            ...     logger
            ... )
            >>> if was_cached:
            ...     # Data came from cache
            ...     pass
        """
        if not self.cache_manager or not self.cache_manager.is_enabled():
            return False

        cache_info = self.cache_manager.get_cache_info(cache_key)
        was_cached = cache_info is not None

        if was_cached:
            logger.info("[dim](using cached data)[/dim]")

        return was_cached

    def get_user_tags(self, tag_ids: List[int], api_client=None) -> Optional[str]:
        """
        Extract username from media tags using configurable regex pattern.

        This method processes media tags to identify user associations based on the
        configured tag format. It supports flexible tag patterns through regex
        configuration, enabling various user identification schemes.

        Args:
            tag_ids: List of tag IDs to examine for user identification
            api_client: API client instance (Radarr or Sonarr) for tag retrieval.
                       Defaults to Radarr if not specified.

        Returns:
            Username string if a matching tag is found, None otherwise

        Examples:
            For tag format "123 - john_doe":
            >>> username = prunarr.get_user_tags([5, 10, 15])
            >>> print(username)  # "john_doe"

            With Sonarr API client:
            >>> username = prunarr.get_user_tags([5], api_client=prunarr.sonarr)

        Note:
            The method uses the first matching tag and stops processing.
            Tag format is determined by the user_tag_regex configuration setting.
        """
        if api_client is None:
            api_client = self.radarr

        # Delegate to user service for tag extraction
        return self.user_service.extract_username_from_tags(tag_ids, api_client)

    def get_all_radarr_movies(self, include_untagged: bool = True) -> List[Dict[str, Any]]:
        """
        Get all Radarr movies with enhanced information.

        Args:
            include_untagged: Include movies without user tags

        Returns:
            List of movies with id, title, imdb_id, user, year, and file info
        """
        self.logger.debug(f"get_all_radarr_movies: include_untagged={include_untagged}")
        result: List[Dict[str, Any]] = []
        movies = self.radarr.get_movie()
        self.logger.debug(f"Fetched {len(movies)} movies from Radarr API")

        for movie in movies:
            movie_file = movie.get("movieFile")
            tag_ids = movie.get("tags", [])

            # Skip movies without downloaded files
            if not movie_file:
                continue

            # Determine user from tags
            username = self.get_user_tags(tag_ids) if tag_ids else None

            # Skip untagged movies if not requested
            if not include_untagged and not username:
                continue

            result.append(
                {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "imdb_id": movie.get("imdbId"),
                    "user": username,
                    "has_file": bool(movie_file),
                    "file_size": movie_file.get("size", 0) if movie_file else 0,
                    "added": movie.get("added"),
                    "monitored": movie.get("monitored", False),
                    "tags": tag_ids,
                }
            )

        return result

    def _build_movie_watch_lookup(self, tautulli_history: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """Build lookup dictionary for movie watch history by IMDB ID (helper)."""
        # Delegate to media matcher service
        return self.media_matcher.build_movie_watch_lookup(tautulli_history, self.tautulli)

    def _determine_movie_watch_status(
        self, movie_user: Optional[str], all_watchers: List[str]
    ) -> tuple[str, Optional[str]]:
        """Determine watch status and watched_by display for a movie (helper)."""
        # Delegate to watch calculator service
        return self.watch_calculator.determine_movie_watch_status(movie_user, all_watchers)

    def get_movies_with_watch_status(
        self, include_untagged: bool = True, username_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all movies with their watch status from Tautulli.

        Args:
            include_untagged: Include movies without user tags
            username_filter: Filter by specific username

        Returns:
            List of movies with watch status, last watched date, and days since watched
        """
        self.logger.debug(
            f"get_movies_with_watch_status: include_untagged={include_untagged}, username_filter={username_filter}"
        )

        all_movies = self.get_all_radarr_movies(include_untagged=include_untagged)
        self.logger.debug(f"Retrieved {len(all_movies)} movies from Radarr")

        tautulli_history = self.tautulli.get_movie_completed_history()
        self.logger.debug(
            f"Retrieved {len(tautulli_history)} movie watch history records from Tautulli"
        )

        watch_lookup = self._build_movie_watch_lookup(tautulli_history)
        self.logger.debug(f"Built watch lookup for {len(watch_lookup)} unique movies")

        now = datetime.now()
        movies_with_status = []

        for movie in all_movies:
            if username_filter and movie.get("user") != username_filter:
                continue

            imdb_id = movie.get("imdb_id")
            watch_info = watch_lookup.get(imdb_id, {})
            watchers = watch_info.get("watchers", {})

            # Calculate days since watched
            most_recent_watch_ts = watch_info.get("most_recent_watch")
            watched_date = None
            days_since_watched = None

            if most_recent_watch_ts:
                watched_date = datetime.fromtimestamp(int(most_recent_watch_ts))
                days_since_watched = (now - watched_date).days

            # Determine watch status
            all_watchers = list(watchers.keys())
            watch_status, watched_by_display = self._determine_movie_watch_status(
                movie.get("user"), all_watchers
            )

            movies_with_status.append(
                {
                    **movie,
                    "watch_status": watch_status,
                    "watched_by": watched_by_display,
                    "watched_at": watched_date,
                    "days_since_watched": days_since_watched,
                    "all_watchers": all_watchers,
                }
            )

        return movies_with_status

    def get_movies_ready_for_removal(self, days_watched: int) -> List[Dict[str, Any]]:
        """
        Get movies that are ready for removal based on days watched criteria.

        Args:
            days_watched: Minimum number of days since movie was watched

        Returns:
            List of movies ready for removal
        """
        movies_with_status = self.get_movies_with_watch_status(include_untagged=False)

        return [
            movie
            for movie in movies_with_status
            if movie.get("watch_status") == "watched"
            and movie.get("days_since_watched") is not None
            and movie.get("days_since_watched") >= days_watched
        ]

    # Episode watch lookup helpers

    def _build_episode_watch_lookup(
        self, tautulli_history: List[Dict[str, Any]], series_tvdb_cache: Dict[str, str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Build watch lookup dictionary for episodes (helper).

        Args:
            tautulli_history: Episode history from Tautulli
            series_tvdb_cache: Mapping of rating_key to tvdb_id

        Returns:
            Dictionary mapping tvdb_id -> episode_key -> user -> watch_data
        """
        # Delegate to media matcher service
        return self.media_matcher.build_episode_watch_lookup(tautulli_history, series_tvdb_cache)

    def _count_watched_episodes(
        self,
        series_watch_info: Dict[str, Dict],
        series_user: Optional[str],
        season_filter: Optional[int] = None,
    ) -> int:
        """
        Count episodes watched by a specific user (helper).

        Args:
            series_watch_info: Watch info for all episodes in series
            series_user: Username to count watches for
            season_filter: Optional season filter

        Returns:
            Number of episodes watched by the user
        """
        # Delegate to watch calculator service
        return self.watch_calculator.count_watched_episodes(
            series_watch_info, series_user, season_filter
        )

    def _calculate_most_recent_watch(
        self, series_watch_info: Dict[str, Dict]
    ) -> tuple[Optional[datetime], Optional[int]]:
        """
        Calculate most recent watch date and days since (helper).

        Args:
            series_watch_info: Watch info for all episodes in series

        Returns:
            Tuple of (most_recent_watch_datetime, days_since_watched)
        """
        # Delegate to watch calculator service
        return self.watch_calculator.calculate_most_recent_watch(series_watch_info)

    def _determine_series_watch_status(self, watched_episodes: int, total_episodes: int) -> str:
        """
        Determine overall watch status for a series (helper).

        Args:
            watched_episodes: Number of episodes watched
            total_episodes: Total number of episodes

        Returns:
            Watch status string (fully_watched, partially_watched, unwatched, no_episodes)
        """
        # Delegate to watch calculator service
        return self.watch_calculator.determine_series_watch_status(watched_episodes, total_episodes)

    def _get_available_seasons_str(self, series_id: int) -> str:
        """
        Get comma-separated string of available seasons (helper).

        Args:
            series_id: Sonarr series ID

        Returns:
            Comma-separated season numbers (e.g., "1,2,3,5")
        """
        try:
            season_info = self.sonarr.get_season_info(series_id)
            available_seasons = []

            for season in season_info:
                season_num = season.get("seasonNumber", 0)
                stats = season.get("statistics", {})
                episode_file_count = stats.get("episodeFileCount", 0)

                # Include season if it has downloaded episodes
                if episode_file_count > 0 and (season_num > 0 or episode_file_count > 0):
                    available_seasons.append(season_num)

            available_seasons.sort()
            return ",".join(map(str, available_seasons)) if available_seasons else ""
        except Exception:
            return ""

    def _build_episode_metadata_lookup(self, seasons_metadata: List[Dict]) -> Dict[str, Dict]:
        """Build episode metadata lookup from season metadata (helper)."""
        episode_metadata_lookup = {}

        for season in seasons_metadata:
            season_num = season.get("seasonNumber", 0)
            total_episode_count = (
                season.get("totalEpisodeCount", 0)
                or season.get("episodeCount", 0)
                or season.get("statistics", {}).get("totalEpisodeCount", 0)
            )

            episode_file_count = season.get("statistics", {}).get("episodeFileCount", 0)

            for ep_num in range(1, total_episode_count + 1):
                episode_key = make_episode_key(season_num, ep_num)
                episode_metadata_lookup[episode_key] = {
                    "season_number": season_num,
                    "episode_number": ep_num,
                    "title": f"Episode {ep_num}",
                    "air_date": "",
                    "runtime": 0,
                    "has_file": ep_num <= episode_file_count,  # Estimate
                    "monitored": season.get("monitored", False),
                    "overview": "",
                }

        return episode_metadata_lookup

    def _update_episode_metadata_from_sonarr(
        self, episode_metadata_lookup: Dict, series_id: int
    ) -> None:
        """Update episode metadata with actual data from Sonarr (helper)."""
        try:
            all_episodes = self.sonarr.get_episodes_by_series_id(series_id)

            for ep in all_episodes:
                if not isinstance(ep, dict) or ep.get("seriesId") != series_id:
                    continue

                season_num = ep.get("seasonNumber", ep.get("season_number"))
                episode_num = ep.get("episodeNumber", ep.get("episode_number"))

                if season_num is not None and episode_num is not None:
                    episode_key = make_episode_key(season_num, episode_num)
                    if episode_key in episode_metadata_lookup:
                        episode_metadata_lookup[episode_key].update(
                            {
                                "title": ep.get("title", f"Episode {episode_num}"),
                                "air_date": ep.get("airDate", ep.get("air_date", "")),
                                "runtime": ep.get("runtime", 0),
                                "has_file": ep.get("hasFile", ep.get("has_file", False)),
                                "episode_file_id": ep.get("episodeFileId"),
                                "overview": ep.get("overview", ""),
                                "monitored": ep.get("monitored", False),
                            }
                        )
        except Exception:
            pass  # Gracefully handle failures

    def _build_episode_detail(
        self,
        ep_metadata: Dict,
        episode_watchers: Dict,
        series_user: Optional[str],
        show_all_watchers: bool,
    ) -> Dict[str, Any]:
        """Build detailed episode information dictionary (helper)."""
        season_num = ep_metadata.get("season_number")
        episode_num = ep_metadata.get("episode_number")
        episode_key = make_episode_key(season_num, episode_num)

        watched_by_user = series_user and series_user in episode_watchers
        watched_by_others = bool([u for u in episode_watchers.keys() if u != series_user])
        all_watchers = list(episode_watchers.keys())

        # Calculate most recent watch
        most_recent_watch = None
        days_since_watched = None
        if episode_watchers:
            most_recent_ts = max(int(w["watched_at"]) for w in episode_watchers.values())
            most_recent_watch = datetime.fromtimestamp(most_recent_ts)
            days_since_watched = (datetime.now() - most_recent_watch).days

        # Determine watch status
        if watched_by_user:
            watch_status = "watched_by_user"
        elif watched_by_others:
            watch_status = "watched_by_others"
        else:
            watch_status = "unwatched"

        return {
            "season_number": season_num,
            "episode_number": episode_num,
            "episode_key": episode_key,
            "title": ep_metadata.get("title", "Unknown Episode"),
            "air_date": ep_metadata.get("air_date", ""),
            "runtime": ep_metadata.get("runtime", 0),
            "has_file": ep_metadata.get("has_file", False),
            "episode_file_id": ep_metadata.get("episode_file_id"),
            "watched": watched_by_user,
            "watched_at": (
                episode_watchers.get(series_user, {}).get("watched_at") if watched_by_user else None
            ),
            "watched_by": series_user if watched_by_user else "",
            "watch_status": watch_status,
            "watched_by_user": watched_by_user,
            "watched_by_others": watched_by_others,
            "all_watchers": all_watchers,
            "most_recent_watch": most_recent_watch,
            "days_since_watched": days_since_watched,
            "watchers_detail": episode_watchers if show_all_watchers else {},
        }

    # Series-related methods

    def get_all_sonarr_series(self, include_untagged: bool = True) -> List[Dict[str, Any]]:
        """
        Get all Sonarr series with enhanced information.

        Args:
            include_untagged: Include series without user tags

        Returns:
            List of series with id, title, tvdb_id, user, year, and file info
        """
        self.logger.debug(f"get_all_sonarr_series: include_untagged={include_untagged}")
        result: List[Dict[str, Any]] = []
        series_list = self.sonarr.get_series()
        self.logger.debug(f"Fetched {len(series_list)} series from Sonarr API")

        for series in series_list:
            tag_ids = series.get("tags", [])

            # Determine user from tags
            username = self.get_user_tags(tag_ids, self.sonarr) if tag_ids else None

            # Skip untagged series if not requested
            if not include_untagged and not username:
                continue

            # Get season info
            seasons = series.get("seasons", [])
            total_episodes = sum(season.get("totalEpisodeCount", 0) for season in seasons)
            downloaded_episodes = sum(season.get("episodeFileCount", 0) for season in seasons)

            result.append(
                {
                    "id": series.get("id"),
                    "title": series.get("title"),
                    "year": series.get("year"),
                    "tvdb_id": series.get("tvdbId"),
                    "imdb_id": series.get("imdbId"),
                    "user": username,
                    "has_file": downloaded_episodes > 0,
                    "total_episodes": total_episodes,
                    "downloaded_episodes": downloaded_episodes,
                    "added": series.get("added"),
                    "monitored": series.get("monitored", False),
                    "status": series.get("status"),
                    "seasons": seasons,
                    "tags": tag_ids,
                    "statistics": series.get(
                        "statistics", {}
                    ),  # Include statistics for episode counts
                }
            )

        return result

    def get_series_with_watch_status(
        self,
        include_untagged: bool = True,
        username_filter: Optional[str] = None,
        series_filter: Optional[str] = None,
        season_filter: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all series with their watch status from Tautulli.

        Args:
            include_untagged: Include series without user tags
            username_filter: Filter by specific username
            series_filter: Filter by series title (partial match)
            season_filter: Filter by specific season number

        Returns:
            List of series with watch status, episode details, and watch progress
        """
        self.logger.debug(
            f"get_series_with_watch_status: include_untagged={include_untagged}, username_filter={username_filter}, series_filter={series_filter}, season_filter={season_filter}"
        )

        # Get and filter series
        all_series = self.get_all_sonarr_series(include_untagged=include_untagged)
        self.logger.debug(f"Retrieved {len(all_series)} series from Sonarr")

        if series_filter:
            all_series = [
                s for s in all_series if series_filter.lower() in s.get("title", "").lower()
            ]
            self.logger.debug(f"After series_filter '{series_filter}': {len(all_series)} series")

        if username_filter:
            all_series = [s for s in all_series if s.get("user") == username_filter]
            self.logger.debug(
                f"After username_filter '{username_filter}': {len(all_series)} series"
            )

        # Build watch lookup
        tautulli_history = self.tautulli.get_episode_completed_history()
        self.logger.debug(
            f"Retrieved {len(tautulli_history)} episode watch history records from Tautulli"
        )

        series_tvdb_cache = self.tautulli.build_series_metadata_cache(tautulli_history)
        self.logger.debug(f"Built TVDB cache with {len(series_tvdb_cache)} unique series")

        watch_lookup = self._build_episode_watch_lookup(tautulli_history, series_tvdb_cache)
        self.logger.debug(f"Built episode watch lookup for {len(watch_lookup)} series")

        # Process each series
        series_with_status = []

        for series in all_series:
            series_id = series.get("id")
            tvdb_id = str(series.get("tvdb_id", ""))
            series_watch_info = watch_lookup.get(tvdb_id, {})
            series_user = series.get("user")

            # Get episode counts
            statistics = series.get("statistics", {})
            total_available_episodes = statistics.get("episodeCount", 0)
            total_downloaded_episodes = statistics.get("episodeFileCount", 0)
            total_episodes_in_watch_history = len(series_watch_info)

            # Determine best episode count source
            actual_total_episodes = (
                total_available_episodes
                or total_episodes_in_watch_history
                or total_downloaded_episodes
            )

            # Count watched episodes
            total_watched_episodes = self._count_watched_episodes(
                series_watch_info, series_user, season_filter
            )

            # Determine watch status
            watch_status = self._determine_series_watch_status(
                total_watched_episodes, actual_total_episodes
            )

            # Calculate most recent watch
            most_recent_watch, days_since_watched = self._calculate_most_recent_watch(
                series_watch_info
            )

            # Get available seasons string
            available_seasons_str = self._get_available_seasons_str(series_id)

            # Calculate total series filesize
            total_size_on_disk = sum(
                season.get("statistics", {}).get("sizeOnDisk", 0)
                for season in series.get("seasons", [])
            )

            series_with_status.append(
                {
                    **series,
                    "watch_status": watch_status,
                    "watched_episodes": total_watched_episodes,
                    "total_episodes": actual_total_episodes,
                    "completion_percentage": (
                        (total_watched_episodes / actual_total_episodes * 100)
                        if actual_total_episodes > 0
                        else 0
                    ),
                    "most_recent_watch": most_recent_watch,
                    "days_since_watched": days_since_watched,
                    "available_seasons": available_seasons_str,
                    "total_size_on_disk": total_size_on_disk,
                }
            )

        return series_with_status

    def get_series_ready_for_removal(
        self, days_watched: int, removal_mode: str = "series"  # "series" or "season"
    ) -> List[Dict[str, Any]]:
        """
        Get series that are ready for removal based on watch criteria.

        Args:
            days_watched: Minimum number of days since series was watched
            removal_mode: "series" removes entire series, "season" removes individual seasons

        Returns:
            List of series or seasons ready for removal
        """
        series_with_status = self.get_series_with_watch_status(include_untagged=False)
        items_to_remove = []

        for series in series_with_status:
            series_user = series.get("user")
            if not series_user:
                continue

            if removal_mode == "series":
                # Remove entire series if fully watched by requester and old enough
                if (
                    series.get("watch_status") == "fully_watched"
                    and series.get("days_since_watched") is not None
                    and series.get("days_since_watched") >= days_watched
                ):
                    items_to_remove.append({**series, "removal_type": "series"})

            elif removal_mode == "season":
                # Remove individual seasons that are fully watched
                for season_data in series.get("seasons_data", []):
                    if (
                        season_data.get("completion_percentage") == 100
                        and series.get("days_since_watched") is not None
                        and series.get("days_since_watched") >= days_watched
                    ):
                        items_to_remove.append(
                            {
                                **series,
                                "removal_type": "season",
                                "season_number": season_data.get("season_number"),
                                "season_data": season_data,
                            }
                        )

        return items_to_remove

    def find_series_by_identifier(self, identifier: str) -> List[Dict[str, Any]]:
        """
        Find series by either ID or title with fuzzy matching.

        Args:
            identifier: Either a numeric series ID or a series title (partial matches supported)

        Returns:
            List of matching series (may be empty, single match, or multiple matches)
        """
        all_series = self.get_all_sonarr_series(include_untagged=True)

        # Check if identifier is numeric (series ID)
        if identifier.isdigit():
            series_id = int(identifier)
            matching_series = [s for s in all_series if s.get("id") == series_id]
            return matching_series

        # Search by title with fuzzy matching
        identifier_lower = identifier.lower().strip()
        exact_matches = []
        partial_matches = []

        for series in all_series:
            series_title = series.get("title", "").lower()

            # Exact match (case insensitive)
            if series_title == identifier_lower:
                exact_matches.append(series)
            # Partial match (identifier is contained in title)
            elif identifier_lower in series_title:
                partial_matches.append(series)

        # Return exact matches first, then partial matches
        return exact_matches + partial_matches

    def get_series_detailed_info(
        self,
        series_id: int,
        season_filter: Optional[int] = None,
        watched_only: bool = False,
        unwatched_only: bool = False,
        show_all_watchers: bool = False,
    ) -> Dict[str, Any]:
        """
        Get comprehensive detailed information about a series including episode-level watch data.

        Args:
            series_id: The Sonarr series ID
            season_filter: Filter to specific season number
            watched_only: Show only episodes watched by the requester
            unwatched_only: Show only episodes NOT watched by the requester
            show_all_watchers: Include detailed watcher information for each episode

        Returns:
            Dictionary with comprehensive series and episode details
        """
        # Get basic series info
        all_series = self.get_all_sonarr_series(include_untagged=True)
        series_info = next((s for s in all_series if s.get("id") == series_id), None)

        if not series_info:
            return {}

        # Get watch status data for this series
        series_with_status = self.get_series_with_watch_status(
            include_untagged=True, username_filter=None, series_filter=None, season_filter=None
        )

        series_watch_data = next((s for s in series_with_status if s.get("id") == series_id), None)
        if not series_watch_data:
            return {}

        # Get detailed watch information
        tvdb_id = str(series_info.get("tvdb_id", ""))
        tautulli_history = self.tautulli.get_episode_completed_history()
        series_tvdb_cache = self.tautulli.build_series_metadata_cache(tautulli_history)

        # Build watch lookup for this specific series
        watch_lookup = {}
        for record in tautulli_history:
            grandparent_key = record.get("grandparent_rating_key")
            if grandparent_key and series_tvdb_cache.get(str(grandparent_key)) == tvdb_id:
                season_num = record.get("season_num")
                episode_num = record.get("episode_num")
                user = record.get("user")
                watched_at = record.get("watched_at")

                if not all([season_num, episode_num, user, watched_at]):
                    continue

                episode_key = f"s{season_num}e{episode_num}"
                if episode_key not in watch_lookup:
                    watch_lookup[episode_key] = {}

                if user not in watch_lookup[episode_key] or int(watched_at) > int(
                    watch_lookup[episode_key][user]["watched_at"]
                ):
                    watch_lookup[episode_key][user] = {
                        "watched_at": watched_at,
                        "watched_date": datetime.fromtimestamp(int(watched_at)),
                        "season_num": season_num,
                        "episode_num": episode_num,
                    }

        # Get episode info from series seasons metadata (this gives us ALL episodes, not just downloaded ones)
        seasons_metadata = series_info.get("seasons", [])

        if hasattr(self, "_debug_logger"):
            self._debug_logger.debug(f"Series seasons metadata: {seasons_metadata}")

        # Build complete episode list from season metadata
        episode_metadata_lookup = {}
        for season in seasons_metadata:
            season_num = season.get("seasonNumber", 0)
            # Try different field names for episode count
            total_episode_count = (
                season.get("totalEpisodeCount", 0)
                or season.get("episodeCount", 0)
                or season.get("statistics", {}).get("totalEpisodeCount", 0)
            )

            if hasattr(self, "_debug_logger"):
                self._debug_logger.debug(
                    f"Season {season_num}: {total_episode_count} total episodes (season data: {season})"
                )

            # Create episode entries for all episodes in this season
            episode_file_count = season.get("statistics", {}).get("episodeFileCount", 0)
            for ep_num in range(1, total_episode_count + 1):
                episode_key = f"s{season_num}e{ep_num}"

                # Estimate if this episode has a file based on episode file count
                # This is not perfect but better than showing all as missing
                has_file_estimated = ep_num <= episode_file_count

                episode_metadata_lookup[episode_key] = {
                    "season_number": season_num,
                    "episode_number": ep_num,
                    "title": f"Episode {ep_num}",  # Default title, we'll update if we have better data
                    "air_date": "",
                    "runtime": 0,
                    "has_file": has_file_estimated,  # Estimate based on file count
                    "monitored": season.get("monitored", False),
                    "overview": "",
                }

        # Now get real episode details from Sonarr using the fixed wrapper method
        try:
            # Use the fixed wrapper method to get all episodes for this series
            all_episodes = self.sonarr.get_episodes_by_series_id(series_id)

            if hasattr(self, "_debug_logger"):
                self._debug_logger.debug(
                    f"get_episodes_by_series_id returned {len(all_episodes)} episodes for series {series_id}"
                )
                if all_episodes:
                    self._debug_logger.debug(f"Sample episode: {all_episodes[0]}")

            if hasattr(self, "_debug_logger"):
                self._debug_logger.debug(f"Processing {len(all_episodes)} episodes from API")
                if len(all_episodes) > 0:
                    self._debug_logger.debug(f"Sample episode data: {all_episodes[0]}")

            for ep in all_episodes:
                if not isinstance(ep, dict):
                    if hasattr(self, "_debug_logger"):
                        self._debug_logger.debug(f"Skipping non-dict episode: {ep}")
                    continue

                season_num = ep.get("seasonNumber", ep.get("season_number"))
                episode_num = ep.get("episodeNumber", ep.get("episode_number"))
                series_id_in_ep = ep.get("seriesId")

                if hasattr(self, "_debug_logger"):
                    self._debug_logger.debug(
                        f"Episode: s{season_num}e{episode_num}, seriesId={series_id_in_ep}, title='{ep.get('title', 'N/A')}'"
                    )

                # Only process episodes that belong to our series
                if series_id_in_ep != series_id:
                    if hasattr(self, "_debug_logger"):
                        self._debug_logger.debug(
                            f"Skipping episode from different series: {series_id_in_ep} != {series_id}"
                        )
                    continue

                if season_num is not None and episode_num is not None:
                    episode_key = f"s{season_num}e{episode_num}"
                    if episode_key in episode_metadata_lookup:
                        # Update with real episode data from Sonarr
                        episode_metadata_lookup[episode_key].update(
                            {
                                "title": ep.get("title", f"Episode {episode_num}"),
                                "air_date": ep.get("airDate", ep.get("air_date", "")),
                                "runtime": ep.get("runtime", 0),
                                "has_file": ep.get("hasFile", ep.get("has_file", False)),
                                "episode_file_id": ep.get("episodeFileId"),
                                "overview": ep.get("overview", ""),
                                "monitored": ep.get("monitored", False),
                            }
                        )

                        if hasattr(self, "_debug_logger"):
                            self._debug_logger.debug(
                                f"Updated {episode_key}: title='{episode_metadata_lookup[episode_key]['title']}', has_file={episode_metadata_lookup[episode_key]['has_file']}"
                            )
                    else:
                        if hasattr(self, "_debug_logger"):
                            self._debug_logger.debug(
                                f"Episode {episode_key} not in our lookup table"
                            )

        except Exception as e:
            if hasattr(self, "_debug_logger"):
                self._debug_logger.debug(f"Could not get episode details: {e}")

        if hasattr(self, "_debug_logger"):
            self._debug_logger.debug(
                f"Built complete episode lookup with {len(episode_metadata_lookup)} episodes"
            )

        # Organize episodes by season - process ALL episodes from Sonarr, not just watched ones
        seasons_data = {}
        series_user = series_info.get("user")
        now = datetime.now()

        # Process all episodes from Sonarr
        for episode_key, ep_metadata in episode_metadata_lookup.items():
            episode_watchers = watch_lookup.get(episode_key, {})
            # Extract season and episode numbers from ep_metadata directly
            season_num = ep_metadata.get("season_number")
            episode_num = ep_metadata.get("episode_number")

            if season_num is None or episode_num is None:
                continue

            # Apply season filter
            if season_filter is not None and season_num != season_filter:
                continue

            # Skip season 0 (specials) unless specifically requested
            if season_filter is None and season_num == 0:
                continue

            # Determine watch status for this episode
            watched_by_user = series_user and series_user in episode_watchers
            watched_by_others = bool([u for u in episode_watchers.keys() if u != series_user])
            all_watchers = list(episode_watchers.keys())

            # Apply filtering
            if watched_only and not watched_by_user:
                continue
            if unwatched_only and watched_by_user:
                continue

            # Calculate days since watched (most recent watch by any user)
            most_recent_watch = None
            days_since_watched = None
            if episode_watchers:
                most_recent_ts = max(int(w["watched_at"]) for w in episode_watchers.values())
                most_recent_watch = datetime.fromtimestamp(most_recent_ts)
                days_since_watched = (now - most_recent_watch).days

            # Determine watch status string
            if watched_by_user:
                watch_status = "watched_by_user"
            elif watched_by_others:
                watch_status = "watched_by_others"
            else:
                watch_status = "unwatched"

            # Build episode detail with both watch data and metadata
            episode_detail = {
                "season_number": season_num,
                "episode_number": episode_num,
                "episode_key": episode_key,
                "title": ep_metadata.get("title", "Unknown Episode"),
                "air_date": ep_metadata.get("air_date", ""),
                "runtime": ep_metadata.get("runtime", 0),
                "has_file": ep_metadata.get("has_file", False),
                "episode_file_id": ep_metadata.get("episode_file_id"),
                "watched": watched_by_user,
                "watched_at": (
                    episode_watchers.get(series_user, {}).get("watched_at")
                    if watched_by_user
                    else None
                ),
                "watched_by": series_user if watched_by_user else "",
                "watch_status": watch_status,
                "watched_by_user": watched_by_user,
                "watched_by_others": watched_by_others,
                "all_watchers": all_watchers,
                "most_recent_watch": most_recent_watch,
                "days_since_watched": days_since_watched,
                "watchers_detail": episode_watchers if show_all_watchers else {},
            }

            # Add to seasons data
            if season_num not in seasons_data:
                seasons_data[season_num] = {
                    "season_number": season_num,
                    "episodes": [],
                    "watched_by_user": 0,
                    "watched_by_others": 0,
                    "unwatched": 0,
                    "total_episodes": 0,
                }

            seasons_data[season_num]["episodes"].append(episode_detail)
            seasons_data[season_num]["total_episodes"] += 1

            if watched_by_user:
                seasons_data[season_num]["watched_by_user"] += 1
            elif watched_by_others:
                seasons_data[season_num]["watched_by_others"] += 1
            else:
                seasons_data[season_num]["unwatched"] += 1

        # Sort episodes within each season
        for season_data in seasons_data.values():
            season_data["episodes"].sort(key=lambda ep: ep["episode_number"])

        return {
            "series_info": series_info,
            "series_watch_data": series_watch_data,
            "seasons_data": seasons_data,
            "total_seasons": len(seasons_data),
            "total_episodes": sum(s["total_episodes"] for s in seasons_data.values()),
            "applied_filters": {
                "season_filter": season_filter,
                "watched_only": watched_only,
                "unwatched_only": unwatched_only,
                "show_all_watchers": show_all_watchers,
            },
        }
