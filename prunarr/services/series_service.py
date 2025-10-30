"""
Series service for handling all series-related operations.

This service encapsulates business logic for TV series management including
retrieving series with watch status, determining removal eligibility,
and managing episode-level detailed information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from prunarr.cache import CacheManager
    from prunarr.services.media_matcher import MediaMatcher
    from prunarr.services.user_service import UserService
    from prunarr.services.watch_calculator import WatchCalculator
    from prunarr.sonarr import SonarrAPI
    from prunarr.tautulli import TautulliAPI


class SeriesService:
    """
    Service for TV series-related operations.

    This service handles all business logic related to series including:
    - Retrieving series from Sonarr with enriched information
    - Determining watch status from Tautulli episode history
    - Calculating removal eligibility for series/seasons
    - Managing user associations through tags
    - Providing detailed episode-level information
    """

    def __init__(
        self,
        sonarr: "SonarrAPI",
        tautulli: "TautulliAPI",
        user_service: "UserService",
        media_matcher: "MediaMatcher",
        watch_calculator: "WatchCalculator",
        cache_manager: Optional["CacheManager"] = None,
        logger=None,
    ):
        """
        Initialize SeriesService with required dependencies.

        Args:
            sonarr: Sonarr API client
            tautulli: Tautulli API client
            user_service: Service for user tag extraction
            media_matcher: Service for matching media with watch history
            watch_calculator: Service for calculating watch status
            cache_manager: Optional cache manager
            logger: Optional logger instance
        """
        self.sonarr = sonarr
        self.tautulli = tautulli
        self.user_service = user_service
        self.media_matcher = media_matcher
        self.watch_calculator = watch_calculator
        self.cache_manager = cache_manager
        self.logger = logger

    def get_all_series(self, include_untagged: bool = True) -> List[Dict[str, Any]]:
        """
        Get all Sonarr series with enhanced information.

        Args:
            include_untagged: Include series without user tags

        Returns:
            List of series with id, title, tvdb_id, user, year, and file info
        """
        if self.logger:
            self.logger.debug(f"get_all_series: include_untagged={include_untagged}")

        result: List[Dict[str, Any]] = []
        series_list = self.sonarr.get_series()

        if self.logger:
            self.logger.debug(f"Fetched {len(series_list)} series from Sonarr API")

        for series in series_list:
            tag_ids = series.get("tags", [])

            # Determine user from tags
            username = (
                self.user_service.extract_username_from_tags(tag_ids, self.sonarr)
                if tag_ids
                else None
            )

            # Skip untagged series if not requested
            if not include_untagged and not username:
                continue

            # Get non-user tag labels for display
            tag_labels = (
                self.user_service.get_non_user_tag_labels(tag_ids, self.sonarr) if tag_ids else []
            )

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
                    "tag_labels": tag_labels,
                    "statistics": series.get("statistics", {}),
                }
            )

        return result

    def get_series_with_watch_status(
        self,
        include_untagged: bool = True,
        username_filter: Optional[str] = None,
        series_filter: Optional[str] = None,
        season_filter: Optional[int] = None,
        check_streaming: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all series with their watch status from Tautulli.

        Args:
            include_untagged: Include series without user tags
            username_filter: Filter by specific username
            series_filter: Filter by series title (partial match)
            season_filter: Filter by specific season number
            check_streaming: Whether to check and cache streaming availability

        Returns:
            List of series with watch status, episode details, and watch progress
        """
        if self.logger:
            self.logger.debug(
                f"get_series_with_watch_status: include_untagged={include_untagged}, "
                f"username_filter={username_filter}, series_filter={series_filter}, "
                f"season_filter={season_filter}, check_streaming={check_streaming}"
            )

        # Get and filter series
        all_series = self.get_all_series(include_untagged=include_untagged)

        if self.logger:
            self.logger.debug(f"Retrieved {len(all_series)} series from Sonarr")

        if series_filter:
            all_series = [
                s for s in all_series if series_filter.lower() in s.get("title", "").lower()
            ]
            if self.logger:
                self.logger.debug(
                    f"After series_filter '{series_filter}': {len(all_series)} series"
                )

        if username_filter:
            all_series = [s for s in all_series if s.get("user") == username_filter]
            if self.logger:
                self.logger.debug(
                    f"After username_filter '{username_filter}': {len(all_series)} series"
                )

        # Build watch lookup
        tautulli_history = self.tautulli.get_episode_completed_history()

        if self.logger:
            self.logger.debug(
                f"Retrieved {len(tautulli_history)} episode watch history records from Tautulli"
            )

        series_tvdb_cache = self.tautulli.build_series_metadata_cache(tautulli_history)

        if self.logger:
            self.logger.debug(f"Built TVDB cache with {len(series_tvdb_cache)} unique series")

        watch_lookup = self.media_matcher.build_episode_watch_lookup(
            tautulli_history, series_tvdb_cache
        )

        if self.logger:
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
            total_watched_episodes = self.watch_calculator.count_watched_episodes(
                series_watch_info, series_user, season_filter
            )

            # Determine watch status
            watch_status = self.watch_calculator.determine_series_watch_status(
                total_watched_episodes, actual_total_episodes
            )

            # Calculate most recent watch
            most_recent_watch, days_since_watched = (
                self.watch_calculator.calculate_most_recent_watch(series_watch_info)
            )

            # Get available seasons string
            available_seasons_str = self._get_available_seasons_str(series_id)

            # Calculate total series filesize
            total_size_on_disk = sum(
                season.get("statistics", {}).get("sizeOnDisk", 0)
                for season in series.get("seasons", [])
            )

            # Check streaming availability from cache if enabled
            streaming_available = None
            if check_streaming and self.cache_manager and tvdb_id:
                cache_key = f"streaming_series_{tvdb_id}"
                if self.cache_manager.store:
                    cached_entry = self.cache_manager.store.get(cache_key)
                    if cached_entry:
                        streaming_available = cached_entry.get("data")
                        if self.logger:
                            self.logger.debug(
                                f"Found cached streaming status for {series.get('title')}: {streaming_available}"
                            )

            series_data = {
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

            # Only add streaming_available if we checked
            if streaming_available is not None:
                series_data["streaming_available"] = streaming_available

            series_with_status.append(series_data)

        return series_with_status

    def get_series_ready_for_removal(
        self,
        days_watched: int,
        removal_mode: str = "series",
        check_streaming: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get series/seasons/episodes ready for removal based on watch criteria.

        Args:
            days_watched: Minimum number of days since last watched
            removal_mode: "series", "season", or "episode"
            check_streaming: Whether to check and cache streaming availability

        Returns:
            List of series, seasons, or episodes ready for removal
        """
        if self.logger:
            self.logger.debug(
                f"get_series_ready_for_removal: days_watched={days_watched}, "
                f"removal_mode={removal_mode}, check_streaming={check_streaming}"
            )

        # Handle episode mode with dedicated method
        if removal_mode == "episode":
            return self.get_episodes_ready_for_removal(days_watched, check_streaming)

        series_with_status = self.get_series_with_watch_status(
            include_untagged=False, check_streaming=check_streaming
        )
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

        if self.logger:
            self.logger.debug(f"Found {len(items_to_remove)} items ready for removal")

        return items_to_remove

    def _get_episode_watch_info(
        self, series: Dict[str, Any], episode_key: str, user: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get watch information for a specific episode.

        Args:
            series: Series data with episodes_watched information
            episode_key: Episode key in format "S01E03"
            user: Username to check watch status for

        Returns:
            Dict with days_since_watched and most_recent_watch, or None if not watched
        """
        episodes_watched = series.get("episodes_watched", {})
        user_episodes = episodes_watched.get(user, {})
        return user_episodes.get(episode_key)

    def _check_all_episodes_watched(
        self,
        episodes_in_file: List[Dict[str, Any]],
        series: Dict[str, Any],
        user: str,
        days_watched: int,
    ) -> bool:
        """
        Check if all episodes in a multi-episode file are watched.

        This ensures safety when deleting files containing multiple episodes.
        Only returns True if ALL episodes meet the watch criteria.

        Args:
            episodes_in_file: List of episode objects in the file
            series: Series data with watch status
            user: Username to check
            days_watched: Minimum days since watched

        Returns:
            True if all episodes are watched by user for days_watched+ days
        """
        from prunarr.utils import make_episode_key

        for ep in episodes_in_file:
            episode_key = make_episode_key(ep.get("seasonNumber"), ep.get("episodeNumber"))
            watch_info = self._get_episode_watch_info(series, episode_key, user)

            if not watch_info or watch_info["days_since_watched"] < days_watched:
                return False

        return True

    def get_episodes_ready_for_removal(
        self,
        days_watched: int,
        check_streaming: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get individual episodes ready for removal.

        Only includes episodes where:
        - Episode is fully watched by the requester
        - Episode was watched X+ days ago
        - ALL episodes in the same file are also watched (multi-episode safety)

        Args:
            days_watched: Minimum days since last watched
            check_streaming: Whether to check streaming availability

        Returns:
            List of episodes with metadata including:
            - series_id, series_title, series_user
            - episode_id, episode_file_id, episode_title
            - season_number, episode_number, episode_key
            - watch_status, days_since_watched, most_recent_watch
            - file_size, streaming_available, tags
        """
        from prunarr.utils import make_episode_key

        if self.logger:
            self.logger.debug(
                f"get_episodes_ready_for_removal: days_watched={days_watched}, "
                f"check_streaming={check_streaming}"
            )

        series_with_status = self.get_series_with_watch_status(
            include_untagged=False, check_streaming=check_streaming
        )

        episodes_to_remove = []

        for series in series_with_status:
            series_user = series.get("user")
            if not series_user:
                continue

            series_id = series.get("id")
            series_title = series.get("title")

            # Get detailed episode information
            episodes = self.sonarr.get_episodes(series_id=series_id)
            episode_files = self.sonarr.get_episode_files(series_id=series_id)

            # Create file_id -> episodes mapping
            file_to_episodes = {}
            for ep_file in episode_files:
                file_id = ep_file["id"]
                file_to_episodes[file_id] = []
                # Get full episode objects for episodes in this file
                for ep_in_file in ep_file.get("episodes", []):
                    # Find the full episode object
                    for full_ep in episodes:
                        if full_ep["id"] == ep_in_file["id"]:
                            file_to_episodes[file_id].append(full_ep)
                            break

            # Check each episode
            for episode in episodes:
                if not episode.get("hasFile"):
                    continue

                episode_file_id = episode.get("episodeFileId")
                if not episode_file_id:
                    continue

                # Check if episode was watched by requester
                episode_key = make_episode_key(
                    episode.get("seasonNumber"), episode.get("episodeNumber")
                )

                # Get watch info from series data
                watch_info = self._get_episode_watch_info(series, episode_key, series_user)

                if not watch_info or watch_info["days_since_watched"] < days_watched:
                    continue

                # SAFETY: Check if all episodes in this file are watched
                episodes_in_file = file_to_episodes.get(episode_file_id, [])
                all_watched = self._check_all_episodes_watched(
                    episodes_in_file, series, series_user, days_watched
                )

                if not all_watched:
                    if self.logger:
                        self.logger.debug(
                            f"Skipping {series_title} {episode_key} - not all episodes in file watched"
                        )
                    continue  # Skip - not all episodes in file are watched

                # Get file size from episode file
                file_size = 0
                for ep_file in episode_files:
                    if ep_file["id"] == episode_file_id:
                        file_size = ep_file.get("size", 0)
                        break

                # Add to removal list
                episodes_to_remove.append(
                    {
                        "series_id": series_id,
                        "series_title": series_title,
                        "series_user": series_user,
                        "episode_id": episode["id"],
                        "episode_file_id": episode_file_id,
                        "episode_title": episode.get("title"),
                        "season_number": episode.get("seasonNumber"),
                        "episode_number": episode.get("episodeNumber"),
                        "episode_key": episode_key,
                        "days_since_watched": watch_info["days_since_watched"],
                        "most_recent_watch": watch_info["most_recent_watch"],
                        "file_size": file_size,
                        "streaming_available": series.get("streaming_available"),
                        "tags": series.get("tags", []),
                    }
                )

        if self.logger:
            self.logger.debug(f"Found {len(episodes_to_remove)} episodes ready for removal")

        return episodes_to_remove

    def find_series_by_identifier(self, identifier: str) -> List[Dict[str, Any]]:
        """
        Find series by either ID or title with fuzzy matching.

        Args:
            identifier: Either a numeric series ID or a series title (partial matches supported)

        Returns:
            List of matching series (may be empty, single match, or multiple matches)
        """
        all_series = self.get_all_series(include_untagged=True)

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

    def _get_available_seasons_str(self, series_id: int) -> str:
        """
        Get formatted string of available seasons for display.

        Args:
            series_id: Sonarr series ID

        Returns:
            Comma-separated string of available season numbers
        """
        try:
            series_data = self.sonarr.get_series(series_id)
            if not series_data or not isinstance(series_data, list) or len(series_data) == 0:
                return "N/A"

            series_info = series_data[0]
            seasons = series_info.get("seasons", [])
            available_seasons = [
                str(s.get("seasonNumber"))
                for s in seasons
                if s.get("statistics", {}).get("episodeFileCount", 0) > 0
            ]

            return ", ".join(available_seasons) if available_seasons else "None"
        except Exception:
            return "N/A"
