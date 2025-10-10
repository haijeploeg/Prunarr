"""
Movie service for handling all movie-related operations.

This service encapsulates business logic for movie management including
retrieving movies with watch status, determining removal eligibility,
and enriching movie data with user associations and watch information.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from prunarr.cache import CacheManager
    from prunarr.radarr import RadarrAPI
    from prunarr.services.media_matcher import MediaMatcher
    from prunarr.services.user_service import UserService
    from prunarr.services.watch_calculator import WatchCalculator
    from prunarr.tautulli import TautulliAPI


class MovieService:
    """
    Service for movie-related operations.

    This service handles all business logic related to movies including:
    - Retrieving movies from Radarr with enriched information
    - Determining watch status from Tautulli history
    - Calculating removal eligibility based on watch criteria
    - Managing user associations through tags
    """

    def __init__(
        self,
        radarr: "RadarrAPI",
        tautulli: "TautulliAPI",
        user_service: "UserService",
        media_matcher: "MediaMatcher",
        watch_calculator: "WatchCalculator",
        cache_manager: Optional["CacheManager"] = None,
        logger=None,
    ):
        """
        Initialize MovieService with required dependencies.

        Args:
            radarr: Radarr API client
            tautulli: Tautulli API client
            user_service: Service for user tag extraction
            media_matcher: Service for matching media with watch history
            watch_calculator: Service for calculating watch status
            cache_manager: Optional cache manager
            logger: Optional logger instance
        """
        self.radarr = radarr
        self.tautulli = tautulli
        self.user_service = user_service
        self.media_matcher = media_matcher
        self.watch_calculator = watch_calculator
        self.cache_manager = cache_manager
        self.logger = logger

    def get_all_movies(self, include_untagged: bool = True) -> List[Dict[str, Any]]:
        """
        Get all Radarr movies with enhanced information.

        Args:
            include_untagged: Include movies without user tags

        Returns:
            List of movies with id, title, imdb_id, user, year, and file info
        """
        if self.logger:
            self.logger.debug(f"get_all_movies: include_untagged={include_untagged}")

        result: List[Dict[str, Any]] = []
        movies = self.radarr.get_movie()

        if self.logger:
            self.logger.debug(f"Fetched {len(movies)} movies from Radarr API")

        for movie in movies:
            movie_file = movie.get("movieFile")
            tag_ids = movie.get("tags", [])

            # Skip movies without downloaded files
            if not movie_file:
                continue

            # Determine user from tags
            username = (
                self.user_service.extract_username_from_tags(tag_ids, self.radarr)
                if tag_ids
                else None
            )

            # Skip untagged movies if not requested
            if not include_untagged and not username:
                continue

            # Get non-user tag labels for display
            tag_labels = (
                self.user_service.get_non_user_tag_labels(tag_ids, self.radarr) if tag_ids else []
            )

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
                    "tag_labels": tag_labels,
                }
            )

        return result

    def get_movies_with_watch_status(
        self,
        include_untagged: bool = True,
        username_filter: Optional[str] = None,
        check_streaming: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all movies with their watch status from Tautulli.

        Args:
            include_untagged: Include movies without user tags
            username_filter: Filter by specific username
            check_streaming: Whether to check and cache streaming availability

        Returns:
            List of movies with watch status, last watched date, and days since watched
        """
        if self.logger:
            self.logger.debug(
                f"get_movies_with_watch_status: include_untagged={include_untagged}, "
                f"username_filter={username_filter}, check_streaming={check_streaming}"
            )

        all_movies = self.get_all_movies(include_untagged=include_untagged)

        if self.logger:
            self.logger.debug(f"Retrieved {len(all_movies)} movies from Radarr")

        tautulli_history = self.tautulli.get_movie_completed_history()

        if self.logger:
            self.logger.debug(
                f"Retrieved {len(tautulli_history)} movie watch history records from Tautulli"
            )

        watch_lookup = self.media_matcher.build_movie_watch_lookup(tautulli_history, self.tautulli)

        if self.logger:
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
            watch_status, watched_by_display = self.watch_calculator.determine_movie_watch_status(
                movie.get("user"), all_watchers
            )

            # Check streaming availability from cache if enabled
            streaming_available = None
            if check_streaming and self.cache_manager and imdb_id:
                cache_key = f"streaming_movie_{imdb_id}"
                # Use cache manager's store.get() which returns the full cache entry
                if self.cache_manager.store:
                    cached_entry = self.cache_manager.store.get(cache_key)
                    if cached_entry:
                        streaming_available = cached_entry.get("data")
                        if self.logger:
                            self.logger.debug(
                                f"Found cached streaming status for {movie.get('title')}: {streaming_available}"
                            )

            movie_data = {
                **movie,
                "watch_status": watch_status,
                "watched_by": watched_by_display,
                "watched_at": watched_date,
                "days_since_watched": days_since_watched,
                "all_watchers": all_watchers,
            }

            # Only add streaming_available if we checked
            if streaming_available is not None:
                movie_data["streaming_available"] = streaming_available

            movies_with_status.append(movie_data)

        return movies_with_status

    def get_movies_ready_for_removal(self, days_watched: int) -> List[Dict[str, Any]]:
        """
        Get movies that are ready for removal based on days watched criteria.

        Args:
            days_watched: Minimum number of days since movie was watched

        Returns:
            List of movies eligible for removal
        """
        if self.logger:
            self.logger.debug(f"get_movies_ready_for_removal: days_watched={days_watched}")

        movies_with_status = self.get_movies_with_watch_status(include_untagged=False)

        if self.logger:
            self.logger.debug(f"Evaluating {len(movies_with_status)} movies for removal")

        movies_ready = []
        for movie in movies_with_status:
            # Only remove if watched by the original requester
            if movie.get("watch_status") != "watched":
                continue

            # Check days since watched
            if (
                movie.get("days_since_watched") is not None
                and movie.get("days_since_watched") >= days_watched
            ):
                movies_ready.append(movie)

        if self.logger:
            self.logger.debug(f"Found {len(movies_ready)} movies ready for removal")

        return movies_ready
