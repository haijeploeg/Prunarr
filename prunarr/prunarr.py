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
from typing import Any, Dict, List, Optional
import re
from datetime import datetime, timedelta

from prunarr.config import Settings
from prunarr.radarr import RadarrAPI
from prunarr.sonarr import SonarrAPI
from prunarr.tautulli import TautulliAPI


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

    def __init__(self, settings: Settings) -> None:
        """
        Initialize PrunArr orchestrator with API clients and configuration.

        Args:
            settings: Validated application settings containing API credentials
                     and configuration options

        Examples:
            >>> from prunarr.config import load_settings
            >>> settings = load_settings("config.yaml")
            >>> prunarr = PrunArr(settings)
            >>> movies = prunarr.get_movies_with_watch_status()
        """
        self.settings = settings
        self.radarr = RadarrAPI(settings.radarr_url, settings.radarr_api_key)
        self.sonarr = SonarrAPI(settings.sonarr_url, settings.sonarr_api_key)
        self.tautulli = TautulliAPI(settings.tautulli_url, settings.tautulli_api_key)
        self.tag_pattern = re.compile(settings.user_tag_regex)

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

        # Process each tag ID to find user identification
        for tag_id in tag_ids:
            try:
                tag = api_client.get_tag(tag_id)
                label = tag.get("label", "")
                match = self.tag_pattern.match(label)
                if match:
                    return match.group(1)
            except Exception:
                # Continue processing remaining tags if one fails
                continue
        return None

    @property
    def radarr_movies(self) -> List[Dict[str, Any]]:
        """
        Retourneert alle Radarr films die:
        - een movieFile hebben (dus gedownload)
        - tags bevatten die overeenkomen met het 'userid - username' format
        Per item returnen we id, title, imdb_id en user.
        """
        result: List[Dict[str, Any]] = []
        movies = self.radarr.get_movie()
        for movie in movies:
            movie_file = movie.get("movieFile")
            tag_ids = movie.get("tags", [])
            if not movie_file or not tag_ids:
                continue
            username = self.get_user_tags(tag_ids)
            if username:
                result.append(
                    {
                        "id": movie.get("id"),
                        "title": movie.get("title"),
                        "imdb_id": movie.get("imdbId"),
                        "user": username,
                    }
                )
        return result

    def get_all_radarr_movies(self, include_untagged: bool = True) -> List[Dict[str, Any]]:
        """
        Get all Radarr movies with enhanced information.

        Args:
            include_untagged: Include movies without user tags

        Returns:
            List of movies with id, title, imdb_id, user, year, and file info
        """
        result: List[Dict[str, Any]] = []
        movies = self.radarr.get_movie()

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

            result.append({
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
            })

        return result

    def get_movies_with_watch_status(
        self,
        include_untagged: bool = True,
        username_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all movies with their watch status from Tautulli.

        Args:
            include_untagged: Include movies without user tags
            username_filter: Filter by specific username

        Returns:
            List of movies with watch status, last watched date, and days since watched
        """
        # Get all movies from Radarr
        all_movies = self.get_all_radarr_movies(include_untagged=include_untagged)

        # Get watch history from Tautulli
        tautulli_history = self.tautulli.get_movie_completed_history()

        # Create lookup for watch history by imdb_id (collect all watchers)
        watch_lookup = {}
        for record in tautulli_history:
            rating_key = record.get("rating_key")
            if rating_key:
                imdb_id = self.tautulli.get_imdb_id_from_rating_key(str(rating_key))
                if imdb_id and record.get("watched_at"):
                    user = record.get("user")
                    watched_at = record.get("watched_at")

                    if imdb_id not in watch_lookup:
                        watch_lookup[imdb_id] = {
                            "watchers": {},
                            "most_recent_watch": watched_at
                        }

                    # Track each user's most recent watch of this movie
                    if user not in watch_lookup[imdb_id]["watchers"] or int(watched_at) > int(watch_lookup[imdb_id]["watchers"][user]["watched_at"]):
                        watch_lookup[imdb_id]["watchers"][user] = {
                            "watched_at": watched_at,
                            "watched_status": "watched"
                        }

                    # Update overall most recent watch time
                    if int(watched_at) > int(watch_lookup[imdb_id]["most_recent_watch"]):
                        watch_lookup[imdb_id]["most_recent_watch"] = watched_at

        # Combine movie data with watch status
        now = datetime.now()
        movies_with_status = []

        for movie in all_movies:
            # Apply username filter
            if username_filter and movie.get("user") != username_filter:
                continue

            imdb_id = movie.get("imdb_id")
            watch_info = watch_lookup.get(imdb_id, {})
            watchers = watch_info.get("watchers", {})

            # Calculate days since watched (use most recent watch)
            most_recent_watch_ts = watch_info.get("most_recent_watch")
            days_since_watched = None
            watched_date = None

            if most_recent_watch_ts:
                watched_date = datetime.fromtimestamp(int(most_recent_watch_ts))
                days_since_watched = (now - watched_date).days

            # Determine watch status and who watched it
            movie_user = movie.get("user")
            all_watchers = list(watchers.keys())

            if not all_watchers:
                watch_status = "unwatched"
                watched_by_display = None
            elif movie_user and movie_user in all_watchers:
                # Movie requester has watched it
                watch_status = "watched"
                watched_by_display = ", ".join(sorted(all_watchers))
            elif movie_user and movie_user not in all_watchers:
                # Movie has requester but they haven't watched it
                watch_status = "watched_by_other"
                watched_by_display = ", ".join(sorted(all_watchers))
            else:
                # Untagged movie that has been watched
                watch_status = "watched"
                watched_by_display = ", ".join(sorted(all_watchers))

            movie_with_status = {
                **movie,
                "watch_status": watch_status,
                "watched_by": watched_by_display,
                "watched_at": watched_date,
                "days_since_watched": days_since_watched,
                "all_watchers": all_watchers,  # Keep for potential future use
            }

            movies_with_status.append(movie_with_status)

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
        movies_to_remove = []

        for movie in movies_with_status:
            # Only consider movies with user tags that were watched by the same user
            if (movie.get("watch_status") == "watched" and
                movie.get("days_since_watched") is not None and
                movie.get("days_since_watched") >= days_watched):
                movies_to_remove.append(movie)

        return movies_to_remove

    def get_movie_by_imdb_id(self, imdb_id: Optional[str], movies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Zoek in lijst van radarr-movies op imdb_id (tt...)."""
        if not imdb_id:
            return None
        return next((m for m in movies if m.get("imdb_id") == imdb_id), None)

    def get_watch_history(self, days_before_removal: int = 60) -> List[Dict[str, Any]]:
        """
        Combineer Tautulli kijkgeschiedenis met Radarr-requested movies.
        Return een lijst met Radarr-details van films die:
         - door dezelfde gebruiker zijn bekeken als in de tag
         - en waarbij het bekeken-verschil >= days_before_removal

        Args:
            days_before_removal: Number of days since watched before movie is eligible for removal
        """
        tautulli_history = self.tautulli.get_movie_completed_history()
        requested_movies = self.radarr_movies

        movies_to_delete: List[Dict[str, Any]] = []
        now = datetime.now()

        for record in tautulli_history:
            watched_by = record.get("user")
            watched_at_ts = record.get("watched_at")
            # watched_at in tautulli is epoch seconds — guard against None
            if not watched_at_ts:
                continue
            watched_at = datetime.fromtimestamp(int(watched_at_ts))
            time_diff = now - watched_at

            rating_key = record.get("rating_key")
            imdb_id = None
            if rating_key is not None:
                imdb_id = self.tautulli.get_imdb_id_from_rating_key(str(rating_key))

            radarr_details = self.get_movie_by_imdb_id(imdb_id, requested_movies)
            if not radarr_details:
                continue

            if watched_by == radarr_details.get("user") and time_diff >= timedelta(days=days_before_removal):
                movies_to_delete.append(radarr_details)

        return movies_to_delete

    # Series-related methods

    def get_all_sonarr_series(self, include_untagged: bool = True) -> List[Dict[str, Any]]:
        """
        Get all Sonarr series with enhanced information.

        Args:
            include_untagged: Include series without user tags

        Returns:
            List of series with id, title, tvdb_id, user, year, and file info
        """
        result: List[Dict[str, Any]] = []
        series_list = self.sonarr.get_series()

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

            result.append({
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
                "statistics": series.get("statistics", {}),  # Include statistics for episode counts
            })

        return result

    def get_series_with_watch_status(
        self,
        include_untagged: bool = True,
        username_filter: Optional[str] = None,
        series_filter: Optional[str] = None,
        season_filter: Optional[int] = None,
        debug: bool = False
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
        # Get all series from Sonarr
        all_series = self.get_all_sonarr_series(include_untagged=include_untagged)

        # Apply series title filter
        if series_filter:
            all_series = [s for s in all_series if series_filter.lower() in s.get("title", "").lower()]

        # Apply username filter
        if username_filter:
            all_series = [s for s in all_series if s.get("user") == username_filter]

        # Get episode watch history from Tautulli
        tautulli_history = self.tautulli.get_episode_completed_history()
        if debug:
            print(f"[DEBUG] Found {len(tautulli_history)} episode watch records from Tautulli")

        # Build series metadata cache for efficient TVDB ID lookups
        series_tvdb_cache = self.tautulli.build_series_metadata_cache(tautulli_history)
        if debug:
            print(f"[DEBUG] Built TVDB cache with {len(series_tvdb_cache)} series mappings")
            if series_tvdb_cache:
                print(f"[DEBUG] Sample TVDB mappings: {dict(list(series_tvdb_cache.items())[:3])}")

        # Create lookup for watch history by tvdb_id and episode info
        watch_lookup = {}
        matched_episodes = 0
        for record in tautulli_history:
            grandparent_key = record.get("grandparent_rating_key")
            if grandparent_key:
                # Get TVDB ID from cache using grandparent_rating_key
                tvdb_id = series_tvdb_cache.get(str(grandparent_key))
                if tvdb_id:
                    series_key = str(tvdb_id)
                    season_num = record.get("season_num")
                    episode_num = record.get("episode_num")
                    user = record.get("user")
                    watched_at = record.get("watched_at")

                    # Skip records with missing essential data
                    if not all([season_num, episode_num, user, watched_at]):
                        continue

                    matched_episodes += 1
                    if series_key not in watch_lookup:
                        watch_lookup[series_key] = {}

                    episode_key = f"s{season_num}e{episode_num}"
                    if episode_key not in watch_lookup[series_key]:
                        watch_lookup[series_key][episode_key] = {}

                    # Track each user's most recent watch of this episode
                    if user not in watch_lookup[series_key][episode_key] or int(watched_at) > int(watch_lookup[series_key][episode_key][user]["watched_at"]):
                        watch_lookup[series_key][episode_key][user] = {
                            "watched_at": watched_at,
                            "season_num": season_num,
                            "episode_num": episode_num
                        }

        if debug:
            print(f"[DEBUG] Matched {matched_episodes} episodes to TVDB IDs")
            print(f"[DEBUG] Watch lookup contains {len(watch_lookup)} series with episode data")

        # Combine series data with watch status
        now = datetime.now()
        series_with_status = []

        for series in all_series:
            series_id = series.get("id")
            series_title = series.get("title", "Unknown")
            tvdb_id = str(series.get("tvdb_id", ""))
            series_watch_info = watch_lookup.get(tvdb_id, {})

            if debug:
                print(f"[DEBUG] Processing series: '{series_title}' (ID: {series_id}, TVDB: {tvdb_id})")
                print(f"[DEBUG]   Watch info available: {len(series_watch_info)} episodes")

            # Use season data from series object instead of separate episode API call
            series_seasons = series.get("seasons", [])
            if debug:
                print(f"[DEBUG]   Series seasons: {len(series_seasons)} seasons found")

            # Calculate watch statistics using season data and watch history
            seasons_data = []
            total_watched_episodes = 0

            # Get episode counts from Sonarr statistics
            statistics = series.get("statistics", {})
            total_available_episodes = statistics.get("episodeCount", 0)  # Episodes that have aired
            total_downloaded_episodes = statistics.get("episodeFileCount", 0)  # Episodes with files

            series_user = series.get("user")

            # Count episodes watched by going through watch history for this series
            for episode_key, episode_watchers in series_watch_info.items():
                # Parse season/episode from key like "s1e5"
                try:
                    season_num = int(episode_key.split('e')[0][1:])
                    episode_num = int(episode_key.split('e')[1])
                except (ValueError, IndexError):
                    continue

                # Apply season filter
                if season_filter is not None and season_num != season_filter:
                    continue

                # Skip season 0 (specials) for most calculations unless specifically requested
                if season_filter is None and season_num == 0:
                    continue

                # Check if series user watched this episode
                if series_user and series_user in episode_watchers:
                    total_watched_episodes += 1

            # Create simplified seasons data based on available watch info
            seasons_count = len(set(
                int(ep_key.split('e')[0][1:])
                for ep_key in series_watch_info.keys()
                if ep_key.split('e')[0][1:].isdigit() and int(ep_key.split('e')[0][1:]) > 0
            )) if series_watch_info else 0

            # Use the most accurate episode count available
            total_episodes_in_watch_history = len(series_watch_info)

            # Priority: Sonarr's episodeCount (aired episodes) > watch history > downloaded episodes
            if total_available_episodes > 0:
                actual_total_episodes = total_available_episodes
            elif total_episodes_in_watch_history > 0:
                actual_total_episodes = total_episodes_in_watch_history
            else:
                actual_total_episodes = total_downloaded_episodes

            if debug:
                print(f"[DEBUG]   Watched episodes: {total_watched_episodes}")
                print(f"[DEBUG]   Total episodes (available/aired): {total_available_episodes}")
                print(f"[DEBUG]   Total episodes (downloaded): {total_downloaded_episodes}")
                print(f"[DEBUG]   Total episodes (from watch history): {total_episodes_in_watch_history}")
                print(f"[DEBUG]   Using total episodes: {actual_total_episodes}")

            # Determine overall watch status
            if actual_total_episodes == 0:
                watch_status = "no_episodes"
            elif total_watched_episodes == 0:
                watch_status = "unwatched"
            elif total_watched_episodes == actual_total_episodes:
                watch_status = "fully_watched"
            else:
                watch_status = "partially_watched"

            # Calculate most recent watch date
            most_recent_watch = None
            days_since_watched = None
            if series_watch_info:
                most_recent_ts = 0
                for episode_watchers in series_watch_info.values():
                    for user_watch in episode_watchers.values():
                        if int(user_watch["watched_at"]) > most_recent_ts:
                            most_recent_ts = int(user_watch["watched_at"])

                if most_recent_ts > 0:
                    most_recent_watch = datetime.fromtimestamp(most_recent_ts)
                    days_since_watched = (now - most_recent_watch).days

            # Calculate total series filesize from all seasons
            seasons = series.get("seasons", [])
            total_size_on_disk = sum(season.get("statistics", {}).get("sizeOnDisk", 0) for season in seasons)

            # Update series data with actual episode counts and filesize
            series_with_status.append({
                **series,
                "watch_status": watch_status,
                "watched_episodes": total_watched_episodes,
                "total_episodes": actual_total_episodes,
                "completion_percentage": (total_watched_episodes / actual_total_episodes * 100) if actual_total_episodes > 0 else 0,
                "most_recent_watch": most_recent_watch,
                "days_since_watched": days_since_watched,
                "seasons_count": seasons_count,
                "total_size_on_disk": total_size_on_disk
            })

        return series_with_status

    def get_series_ready_for_removal(
        self,
        days_watched: int,
        removal_mode: str = "series"  # "series" or "season"
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
                if (series.get("watch_status") == "fully_watched" and
                    series.get("days_since_watched") is not None and
                    series.get("days_since_watched") >= days_watched):
                    items_to_remove.append({
                        **series,
                        "removal_type": "series"
                    })

            elif removal_mode == "season":
                # Remove individual seasons that are fully watched
                for season_data in series.get("seasons_data", []):
                    if (season_data.get("completion_percentage") == 100 and
                        series.get("days_since_watched") is not None and
                        series.get("days_since_watched") >= days_watched):
                        items_to_remove.append({
                            **series,
                            "removal_type": "season",
                            "season_number": season_data.get("season_number"),
                            "season_data": season_data
                        })

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
        show_all_watchers: bool = False
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
            include_untagged=True,
            username_filter=None,
            series_filter=None,
            season_filter=None
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

                if user not in watch_lookup[episode_key] or int(watched_at) > int(watch_lookup[episode_key][user]["watched_at"]):
                    watch_lookup[episode_key][user] = {
                        "watched_at": watched_at,
                        "watched_date": datetime.fromtimestamp(int(watched_at)),
                        "season_num": season_num,
                        "episode_num": episode_num
                    }

        # Get episode info from series seasons metadata (this gives us ALL episodes, not just downloaded ones)
        seasons_metadata = series_info.get("seasons", [])

        if hasattr(self, '_debug_logger'):
            self._debug_logger.debug(f"Series seasons metadata: {seasons_metadata}")

        # Build complete episode list from season metadata
        episode_metadata_lookup = {}
        for season in seasons_metadata:
            season_num = season.get("seasonNumber", 0)
            # Try different field names for episode count
            total_episode_count = (season.get("totalEpisodeCount", 0) or
                                 season.get("episodeCount", 0) or
                                 season.get("statistics", {}).get("totalEpisodeCount", 0))

            if hasattr(self, '_debug_logger'):
                self._debug_logger.debug(f"Season {season_num}: {total_episode_count} total episodes (season data: {season})")

            # Create episode entries for all episodes in this season
            episode_file_count = season.get("statistics", {}).get("episodeFileCount", 0)
            for ep_num in range(1, total_episode_count + 1):
                episode_key = f"s{season_num}e{ep_num}"

                # Estimate if this episode has a file based on episode file count
                # This is not perfect but better than showing all as missing
                has_file_estimated = ep_num <= episode_file_count

                episode_metadata_lookup[episode_key] = {
                    'season_number': season_num,
                    'episode_number': ep_num,
                    'title': f"Episode {ep_num}",  # Default title, we'll update if we have better data
                    'air_date': '',
                    'runtime': 0,
                    'has_file': has_file_estimated,  # Estimate based on file count
                    'monitored': season.get("monitored", False),
                    'overview': '',
                }

        # Now get real episode details from Sonarr using the fixed wrapper method
        try:
            # Use the fixed wrapper method to get all episodes for this series
            all_episodes = self.sonarr.get_episodes_by_series_id(series_id)

            if hasattr(self, '_debug_logger'):
                self._debug_logger.debug(f"get_episodes_by_series_id returned {len(all_episodes)} episodes for series {series_id}")
                if all_episodes:
                    self._debug_logger.debug(f"Sample episode: {all_episodes[0]}")

            if hasattr(self, '_debug_logger'):
                self._debug_logger.debug(f"Processing {len(all_episodes)} episodes from API")
                if len(all_episodes) > 0:
                    self._debug_logger.debug(f"Sample episode data: {all_episodes[0]}")

            for ep in all_episodes:
                if not isinstance(ep, dict):
                    if hasattr(self, '_debug_logger'):
                        self._debug_logger.debug(f"Skipping non-dict episode: {ep}")
                    continue

                season_num = ep.get('seasonNumber', ep.get('season_number'))
                episode_num = ep.get('episodeNumber', ep.get('episode_number'))
                series_id_in_ep = ep.get('seriesId')

                if hasattr(self, '_debug_logger'):
                    self._debug_logger.debug(f"Episode: s{season_num}e{episode_num}, seriesId={series_id_in_ep}, title='{ep.get('title', 'N/A')}'")

                # Only process episodes that belong to our series
                if series_id_in_ep != series_id:
                    if hasattr(self, '_debug_logger'):
                        self._debug_logger.debug(f"Skipping episode from different series: {series_id_in_ep} != {series_id}")
                    continue

                if season_num is not None and episode_num is not None:
                    episode_key = f"s{season_num}e{episode_num}"
                    if episode_key in episode_metadata_lookup:
                        # Update with real episode data from Sonarr
                        episode_metadata_lookup[episode_key].update({
                            'title': ep.get('title', f"Episode {episode_num}"),
                            'air_date': ep.get('airDate', ep.get('air_date', '')),
                            'runtime': ep.get('runtime', 0),
                            'has_file': ep.get('hasFile', ep.get('has_file', False)),
                            'episode_file_id': ep.get('episodeFileId'),
                            'overview': ep.get('overview', ''),
                            'monitored': ep.get('monitored', False),
                        })

                        if hasattr(self, '_debug_logger'):
                            self._debug_logger.debug(f"Updated {episode_key}: title='{episode_metadata_lookup[episode_key]['title']}', has_file={episode_metadata_lookup[episode_key]['has_file']}")
                    else:
                        if hasattr(self, '_debug_logger'):
                            self._debug_logger.debug(f"Episode {episode_key} not in our lookup table")

        except Exception as e:
            if hasattr(self, '_debug_logger'):
                self._debug_logger.debug(f"Could not get episode details: {e}")

        if hasattr(self, '_debug_logger'):
            self._debug_logger.debug(f"Built complete episode lookup with {len(episode_metadata_lookup)} episodes")

        # Organize episodes by season - process ALL episodes from Sonarr, not just watched ones
        seasons_data = {}
        series_user = series_info.get("user")
        now = datetime.now()

        # Process all episodes from Sonarr
        for episode_key, ep_metadata in episode_metadata_lookup.items():
            episode_watchers = watch_lookup.get(episode_key, {})
            # Extract season and episode numbers from ep_metadata directly
            season_num = ep_metadata.get('season_number')
            episode_num = ep_metadata.get('episode_number')

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
                "title": ep_metadata.get('title', 'Unknown Episode'),
                "air_date": ep_metadata.get('air_date', ''),
                "runtime": ep_metadata.get('runtime', 0),
                "has_file": ep_metadata.get('has_file', False),
                "episode_file_id": ep_metadata.get('episode_file_id'),
                "watched": watched_by_user,
                "watched_at": episode_watchers.get(series_user, {}).get('watched_at') if watched_by_user else None,
                "watched_by": series_user if watched_by_user else "",
                "watch_status": watch_status,
                "watched_by_user": watched_by_user,
                "watched_by_others": watched_by_others,
                "all_watchers": all_watchers,
                "most_recent_watch": most_recent_watch,
                "days_since_watched": days_since_watched,
                "watchers_detail": episode_watchers if show_all_watchers else {}
            }

            # Add to seasons data
            if season_num not in seasons_data:
                seasons_data[season_num] = {
                    "season_number": season_num,
                    "episodes": [],
                    "watched_by_user": 0,
                    "watched_by_others": 0,
                    "unwatched": 0,
                    "total_episodes": 0
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
                "show_all_watchers": show_all_watchers
            }
        }