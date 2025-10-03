"""
Media matcher service for correlating watch history with media libraries.

This service handles the complex logic of matching Tautulli watch history
records with Radarr/Sonarr media items using IMDB/TVDB identifiers.
"""

from typing import Any, Dict, List

from prunarr.utils.parsers import make_episode_key


class MediaMatcher:
    """
    Service for matching watch history with media library items.

    This service encapsulates the logic for correlating Tautulli watch
    history with Radarr movies and Sonarr series/episodes using external
    identifiers (IMDB, TVDB).
    """

    @staticmethod
    def build_movie_watch_lookup(
        tautulli_history: List[Dict[str, Any]], tautulli_client
    ) -> Dict[str, Dict]:
        """
        Build lookup dictionary for movie watch history by IMDB ID.

        Args:
            tautulli_history: List of watch history records from Tautulli
            tautulli_client: TautulliAPI client instance for IMDB ID lookups

        Returns:
            Dictionary mapping imdb_id -> {
                watchers: {user -> {watched_at, watched_status}},
                most_recent_watch: timestamp
            }
        """
        watch_lookup = {}

        for record in tautulli_history:
            rating_key = record.get("rating_key")
            if not rating_key:
                continue

            imdb_id = tautulli_client.get_imdb_id_from_rating_key(str(rating_key))
            if not imdb_id or not record.get("watched_at"):
                continue

            user = record.get("user")
            watched_at = record.get("watched_at")

            if imdb_id not in watch_lookup:
                watch_lookup[imdb_id] = {
                    "watchers": {},
                    "most_recent_watch": watched_at,
                }

            # Track each user's most recent watch of this movie
            if user not in watch_lookup[imdb_id]["watchers"] or int(watched_at) > int(
                watch_lookup[imdb_id]["watchers"][user]["watched_at"]
            ):
                watch_lookup[imdb_id]["watchers"][user] = {
                    "watched_at": watched_at,
                    "watched_status": "watched",
                }

            # Update overall most recent watch time
            if int(watched_at) > int(watch_lookup[imdb_id]["most_recent_watch"]):
                watch_lookup[imdb_id]["most_recent_watch"] = watched_at

        return watch_lookup

    @staticmethod
    def build_episode_watch_lookup(
        tautulli_history: List[Dict[str, Any]], series_tvdb_cache: Dict[str, str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Build watch lookup dictionary for episodes.

        Args:
            tautulli_history: List of episode watch history records from Tautulli
            series_tvdb_cache: Mapping of rating_key -> tvdb_id

        Returns:
            Dictionary mapping tvdb_id -> episode_key -> user -> watch_data
            Example: {"12345": {"s1e1": {"john": {"watched_at": "123456", ...}}}}
        """
        watch_lookup = {}

        for record in tautulli_history:
            grandparent_key = record.get("grandparent_rating_key")
            if not grandparent_key:
                continue

            tvdb_id = series_tvdb_cache.get(str(grandparent_key))
            if not tvdb_id:
                continue

            season_num = record.get("season_num")
            episode_num = record.get("episode_num")
            user = record.get("user")
            watched_at = record.get("watched_at")

            if not all([season_num, episode_num, user, watched_at]):
                continue

            series_key = str(tvdb_id)
            episode_key = make_episode_key(season_num, episode_num)

            if series_key not in watch_lookup:
                watch_lookup[series_key] = {}
            if episode_key not in watch_lookup[series_key]:
                watch_lookup[series_key][episode_key] = {}

            # Track each user's most recent watch of this episode
            if user not in watch_lookup[series_key][episode_key] or int(watched_at) > int(
                watch_lookup[series_key][episode_key][user]["watched_at"]
            ):
                watch_lookup[series_key][episode_key][user] = {
                    "watched_at": watched_at,
                    "season_num": season_num,
                    "episode_num": episode_num,
                }

        return watch_lookup

    @staticmethod
    def match_movie_with_watch_data(
        movie: Dict[str, Any], watch_lookup: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Match a movie with its watch data from lookup.

        Args:
            movie: Movie dictionary from Radarr
            watch_lookup: Watch lookup dictionary from build_movie_watch_lookup

        Returns:
            Dictionary containing watchers info and most recent watch timestamp
        """
        imdb_id = movie.get("imdb_id")
        if not imdb_id or imdb_id not in watch_lookup:
            return {"watchers": {}, "most_recent_watch": None}

        return watch_lookup[imdb_id]

    @staticmethod
    def match_series_with_watch_data(
        series: Dict[str, Any], watch_lookup: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Match a series with its episode watch data from lookup.

        Args:
            series: Series dictionary from Sonarr
            watch_lookup: Episode watch lookup dictionary from build_episode_watch_lookup

        Returns:
            Dictionary mapping episode_key -> user -> watch_data for this series
        """
        tvdb_id = str(series.get("tvdb_id", ""))
        if not tvdb_id or tvdb_id not in watch_lookup:
            return {}

        return watch_lookup[tvdb_id]
