"""
Unit tests for PrunArr helper methods.

Tests the new refactored helper methods that were extracted during code refactoring.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from prunarr.config import Settings
from prunarr.prunarr import PrunArr


class TestMovieHelpers:
    """Test movie-related helper methods."""

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_build_movie_watch_lookup(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test building movie watch lookup from Tautulli history."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock Tautulli to return IMDB ID
        prunarr.tautulli.get_imdb_id_from_rating_key = Mock(return_value="tt1234567")

        tautulli_history = [
            {"rating_key": "123", "user": "alice", "watched_at": "1000"},
            {"rating_key": "456", "user": "bob", "watched_at": "2000"},
            {"rating_key": "123", "user": "alice", "watched_at": "3000"},  # More recent watch
        ]

        lookup = prunarr._build_movie_watch_lookup(tautulli_history)

        # Should have one IMDB ID with watchers
        assert "tt1234567" in lookup
        assert "alice" in lookup["tt1234567"]["watchers"]
        # Most recent watch should be 3000
        assert lookup["tt1234567"]["most_recent_watch"] == "3000"
        # Alice's most recent watch should be 3000
        assert lookup["tt1234567"]["watchers"]["alice"]["watched_at"] == "3000"

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_determine_movie_watch_status(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test determining movie watch status."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Movie not watched
        status, display = prunarr._determine_movie_watch_status("alice", [])
        assert status == "unwatched"
        assert display is None

        # Movie watched by requester
        status, display = prunarr._determine_movie_watch_status("alice", ["alice"])
        assert status == "watched"
        assert "alice" in display

        # Movie watched by others
        status, display = prunarr._determine_movie_watch_status("alice", ["bob", "charlie"])
        assert status == "watched_by_other"
        assert "bob" in display
        assert "charlie" in display

        # Untagged movie watched
        status, display = prunarr._determine_movie_watch_status(None, ["alice"])
        assert status == "watched"
        assert "alice" in display


class TestEpisodeHelpers:
    """Test episode-related helper methods."""

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_build_episode_watch_lookup(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test building episode watch lookup from Tautulli history."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        tautulli_history = [
            {
                "grandparent_rating_key": "100",
                "season_num": 1,
                "episode_num": 5,
                "user": "alice",
                "watched_at": "1000",
            },
            {
                "grandparent_rating_key": "100",
                "season_num": 1,
                "episode_num": 6,
                "user": "bob",
                "watched_at": "2000",
            },
        ]
        series_tvdb_cache = {"100": "12345"}

        lookup = prunarr._build_episode_watch_lookup(tautulli_history, series_tvdb_cache)

        # Should have series with episodes
        assert "12345" in lookup
        assert "s1e5" in lookup["12345"]
        assert "s1e6" in lookup["12345"]
        assert "alice" in lookup["12345"]["s1e5"]
        assert "bob" in lookup["12345"]["s1e6"]

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_count_watched_episodes(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test counting watched episodes."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        series_watch_info = {
            "s1e1": {"alice": {}, "bob": {}},
            "s1e2": {"alice": {}},
            "s2e1": {"bob": {}},
            "s0e1": {"alice": {}},  # Special
        }

        # Count all episodes watched by alice (excluding specials)
        count = prunarr._count_watched_episodes(series_watch_info, "alice")
        assert count == 2  # s1e1, s1e2 (s0e1 skipped)

        # Count only season 1
        count = prunarr._count_watched_episodes(series_watch_info, "alice", season_filter=1)
        assert count == 2  # s1e1, s1e2

        # Count season 2
        count = prunarr._count_watched_episodes(series_watch_info, "alice", season_filter=2)
        assert count == 0

        # Count bob's watches
        count = prunarr._count_watched_episodes(series_watch_info, "bob")
        assert count == 2  # s1e1, s2e1

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_calculate_most_recent_watch(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test calculating most recent watch."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # No watches
        most_recent, days_since = prunarr._calculate_most_recent_watch({})
        assert most_recent is None
        assert days_since is None

        # With watches
        series_watch_info = {
            "s1e1": {"alice": {"watched_at": "1000"}},
            "s1e2": {"bob": {"watched_at": "2000"}},
            "s1e3": {"alice": {"watched_at": "3000"}},
        }

        most_recent, days_since = prunarr._calculate_most_recent_watch(series_watch_info)
        assert most_recent == datetime.fromtimestamp(3000)
        assert isinstance(days_since, int)
        assert days_since >= 0

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_determine_series_watch_status(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test determining series watch status."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # No episodes
        assert prunarr._determine_series_watch_status(0, 0) == "no_episodes"

        # Unwatched
        assert prunarr._determine_series_watch_status(0, 10) == "unwatched"

        # Fully watched
        assert prunarr._determine_series_watch_status(10, 10) == "fully_watched"

        # Partially watched
        assert prunarr._determine_series_watch_status(5, 10) == "partially_watched"

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_build_episode_metadata_lookup(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test building episode metadata lookup."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        seasons_metadata = [
            {
                "seasonNumber": 1,
                "totalEpisodeCount": 10,
                "statistics": {"episodeFileCount": 5},
                "monitored": True,
            },
            {
                "seasonNumber": 2,
                "episodeCount": 8,
                "statistics": {"episodeFileCount": 8},
                "monitored": False,
            },
        ]

        lookup = prunarr._build_episode_metadata_lookup(seasons_metadata)

        # Should have all episodes
        assert "s1e1" in lookup
        assert "s1e10" in lookup
        assert "s2e1" in lookup
        assert "s2e8" in lookup

        # Check metadata
        assert lookup["s1e1"]["season_number"] == 1
        assert lookup["s1e1"]["episode_number"] == 1
        assert lookup["s1e1"]["monitored"] is True
        assert lookup["s1e1"]["has_file"] is True  # First 5 episodes

        assert lookup["s1e10"]["has_file"] is False  # Beyond first 5

        assert lookup["s2e1"]["monitored"] is False


class TestPrunArrIntegration:
    """Integration tests for PrunArr helper methods working together."""

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_get_movies_ready_for_removal(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test getting movies ready for removal uses correct filtering."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock the MovieService method since that's what's actually called
        prunarr.movie_service.get_movies_with_watch_status = Mock(
            return_value=[
                {"watch_status": "watched", "days_since_watched": 70, "title": "Movie 1"},
                {"watch_status": "watched", "days_since_watched": 50, "title": "Movie 2"},
                {"watch_status": "unwatched", "days_since_watched": None, "title": "Movie 3"},
                {"watch_status": "watched", "days_since_watched": 100, "title": "Movie 4"},
            ]
        )

        # Get movies ready for removal (60+ days)
        movies = prunarr.get_movies_ready_for_removal(days_watched=60)

        # Should only return Movie 1 and Movie 4
        assert len(movies) == 2
        titles = [m["title"] for m in movies]
        assert "Movie 1" in titles
        assert "Movie 4" in titles

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_get_user_tags(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test getting user from tags."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
            user_tag_regex=r"^\d+ - (.+)$",
        )
        prunarr = PrunArr(settings)

        # Mock the radarr API
        mock_radarr_instance = mock_radarr.return_value
        mock_radarr_instance.get_tag.return_value = {"id": 1, "label": "123 - alice"}

        result = prunarr.get_user_tags([1], api_client=prunarr.radarr)
        assert result == "alice"

        # Test with multiple tags (only first match returned)
        mock_radarr_instance.get_tag.side_effect = [
            {"id": 1, "label": "invalid"},
            {"id": 2, "label": "456 - bob"},
        ]
        result = prunarr.get_user_tags([1, 2], api_client=prunarr.radarr)
        assert result == "bob"

        # Test with no matching tags
        mock_radarr_instance.get_tag.side_effect = [{"id": 1, "label": "invalid"}]
        result = prunarr.get_user_tags([1], api_client=prunarr.radarr)
        assert result is None

        # Test with exception
        mock_radarr_instance.get_tag.side_effect = Exception("API Error")
        result = prunarr.get_user_tags([1], api_client=prunarr.radarr)
        assert result is None

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_get_all_radarr_movies(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test getting all Radarr movies with enhanced information."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock radarr API
        mock_radarr_instance = mock_radarr.return_value
        mock_radarr_instance.get_movie.return_value = [
            {
                "id": 1,
                "title": "Movie 1",
                "year": 2020,
                "imdbId": "tt1234567",
                "tags": [1],
                "hasFile": True,
                "movieFile": {"size": 1024 * 1024 * 1024, "path": "/path/to/movie1.mkv"},
                "added": "2024-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "title": "Movie 2",
                "year": 2021,
                "imdbId": "tt7654321",
                "tags": [],
                "hasFile": True,
                "movieFile": {"size": 512 * 1024 * 1024, "path": "/path/to/movie2.mkv"},
                "added": "2024-02-01T00:00:00Z",
            },
        ]
        mock_radarr_instance.get_tag.return_value = {"id": 1, "label": "123 - alice"}

        # Test with untagged included
        movies = prunarr.get_all_radarr_movies(include_untagged=True)
        assert len(movies) == 2
        assert movies[0]["user"] == "alice"
        assert movies[0]["file_size"] == 1024 * 1024 * 1024
        assert movies[1]["user"] is None

        # Test without untagged
        movies = prunarr.get_all_radarr_movies(include_untagged=False)
        assert len(movies) == 1
        assert movies[0]["user"] == "alice"

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_get_all_sonarr_series(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test getting all Sonarr series with enhanced information."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock sonarr API
        mock_sonarr_instance = mock_sonarr.return_value
        mock_sonarr_instance.get_series.return_value = [
            {
                "id": 1,
                "title": "Series 1",
                "year": 2020,
                "tvdbId": 12345,
                "tags": [1],
                "status": "continuing",
                "seasons": [{"seasonNumber": 1}],
            },
            {
                "id": 2,
                "title": "Series 2",
                "year": 2021,
                "tvdbId": 67890,
                "tags": [],
                "status": "ended",
                "seasons": [{"seasonNumber": 1}, {"seasonNumber": 2}],
            },
        ]
        mock_sonarr_instance.get_tag.return_value = {"id": 1, "label": "123 - bob"}

        # Test with untagged included
        series = prunarr.get_all_sonarr_series(include_untagged=True)
        assert len(series) == 2
        assert series[0]["user"] == "bob"
        assert series[1]["user"] is None

        # Test without untagged
        series = prunarr.get_all_sonarr_series(include_untagged=False)
        assert len(series) == 1
        assert series[0]["user"] == "bob"

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_find_series_by_identifier_numeric(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test finding series by numeric ID."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        prunarr.series_service.get_all_series = Mock(
            return_value=[
                {"id": 123, "title": "Series 1"},
                {"id": 456, "title": "Series 2"},
            ]
        )

        result = prunarr.find_series_by_identifier("123")
        assert len(result) == 1
        assert result[0]["title"] == "Series 1"

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_find_series_by_identifier_title(self, mock_tautulli, mock_sonarr, mock_radarr):
        """Test finding series by title."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        prunarr.series_service.get_all_series = Mock(
            return_value=[
                {"id": 1, "title": "Breaking Bad"},
                {"id": 2, "title": "Better Call Saul"},
                {"id": 3, "title": "Breaking Benjamin"},
            ]
        )

        # Exact match
        result = prunarr.find_series_by_identifier("breaking bad")
        assert len(result) == 1
        assert result[0]["title"] == "Breaking Bad"

        # Partial match
        result = prunarr.find_series_by_identifier("breaking")
        assert len(result) == 2  # Breaking Bad and Breaking Benjamin

        # No match
        result = prunarr.find_series_by_identifier("nonexistent")
        assert len(result) == 0


class TestCriticalMovieLogic:
    """Critical business logic tests for movie watch status and removal decisions."""

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_get_movies_with_watch_status_integration(
        self, mock_tautulli, mock_sonarr, mock_radarr
    ):
        """CRITICAL: Test complete movie watch status workflow."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock Radarr movies
        mock_radarr_instance = mock_radarr.return_value
        mock_radarr_instance.get_movie.return_value = [
            {
                "id": 1,
                "title": "Movie A",
                "imdbId": "tt1111111",
                "tags": [1],
                "hasFile": True,
                "movieFile": {"size": 1024 * 1024 * 1024},
            },
            {
                "id": 2,
                "title": "Movie B",
                "imdbId": "tt2222222",
                "tags": [2],
                "hasFile": True,
                "movieFile": {"size": 512 * 1024 * 1024},
            },
        ]

        # Mock get_tag to return appropriate response based on tag_id
        def mock_get_tag(tag_id):
            tag_map = {
                1: {"id": 1, "label": "1 - alice"},
                2: {"id": 2, "label": "2 - bob"},
            }
            return tag_map.get(tag_id, {"id": tag_id, "label": f"Tag {tag_id}"})

        mock_radarr_instance.get_tag.side_effect = mock_get_tag

        # Mock Tautulli watch history
        mock_tautulli_instance = mock_tautulli.return_value
        mock_tautulli_instance.get_movie_completed_history.return_value = [
            {
                "rating_key": "100",
                "user": "alice",
                "watched_at": "1704067200",  # 60 days ago
                "watched_status": 1,
                "media_type": "movie",
            },
            {
                "rating_key": "200",
                "user": "charlie",  # Different user
                "watched_at": "1706745600",
                "watched_status": 1,
                "media_type": "movie",
            },
        ]
        mock_tautulli_instance.get_imdb_id_from_rating_key.side_effect = [
            "tt1111111",  # Movie A
            "tt2222222",  # Movie B
        ]

        # Execute
        movies = prunarr.get_movies_with_watch_status(include_untagged=False, username_filter=None)

        # Verify critical results
        assert len(movies) == 2

        # Movie A: Watched by requester (alice)
        movie_a = next(m for m in movies if m["title"] == "Movie A")
        assert movie_a["watch_status"] == "watched"
        assert movie_a["user"] == "alice"
        assert movie_a["days_since_watched"] is not None

        # Movie B: Watched by someone else (charlie, not bob)
        movie_b = next(m for m in movies if m["title"] == "Movie B")
        assert movie_b["watch_status"] == "watched_by_other"
        assert movie_b["user"] == "bob"
        assert "charlie" in movie_b["watched_by"]

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_movie_removal_safety_filters(self, mock_tautulli, mock_sonarr, mock_radarr):
        """CRITICAL: Test that removal filters prevent accidental deletion."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock the MovieService method since that's what's actually called
        prunarr.movie_service.get_movies_with_watch_status = Mock(
            return_value=[
                # Should be removed (watched by requester, 70 days ago)
                {"id": 1, "watch_status": "watched", "days_since_watched": 70, "user": "alice"},
                # Should NOT be removed (watched by others)
                {
                    "id": 2,
                    "watch_status": "watched_by_other",
                    "days_since_watched": 70,
                    "user": "alice",
                },
                # Should NOT be removed (not watched yet)
                {"id": 3, "watch_status": "unwatched", "days_since_watched": None, "user": "alice"},
                # Should NOT be removed (watched too recently - 30 days)
                {"id": 4, "watch_status": "watched", "days_since_watched": 30, "user": "alice"},
                # Should be removed (watched by requester, 100 days ago)
                {"id": 5, "watch_status": "watched", "days_since_watched": 100, "user": "alice"},
            ]
        )

        # Execute with 60-day threshold
        movies_to_remove = prunarr.get_movies_ready_for_removal(days_watched=60)

        # CRITICAL SAFETY CHECK: Only movies 1 and 5 should be eligible
        assert len(movies_to_remove) == 2
        removed_ids = [m["id"] for m in movies_to_remove]
        assert 1 in removed_ids
        assert 5 in removed_ids
        # Verify dangerous ones are NOT included
        assert 2 not in removed_ids  # watched by others
        assert 3 not in removed_ids  # unwatched
        assert 4 not in removed_ids  # too recent


class TestCriticalSeriesLogic:
    """Critical business logic tests for series watch status."""

    @patch("prunarr.prunarr.RadarrAPI")
    @patch("prunarr.prunarr.SonarrAPI")
    @patch("prunarr.prunarr.TautulliAPI")
    def test_series_watch_status_calculation(self, mock_tautulli, mock_sonarr, mock_radarr):
        """CRITICAL: Test series watch status determination."""
        settings = Settings(
            radarr_api_key="test",
            radarr_url="http://test",
            sonarr_api_key="test",
            sonarr_url="http://test",
            tautulli_api_key="test",
            tautulli_url="http://test",
        )
        prunarr = PrunArr(settings)

        # Mock Sonarr series
        mock_sonarr_instance = mock_sonarr.return_value
        mock_sonarr_instance.get_series.return_value = [
            {
                "id": 1,
                "title": "Series A",
                "tvdbId": 111111,
                "tags": [1],
                "statistics": {"episodeCount": 10, "episodeFileCount": 10},
                "seasons": [],
            }
        ]
        mock_sonarr_instance.get_tag.return_value = {"id": 1, "label": "1 - alice"}
        mock_sonarr_instance.get_season_info.return_value = []

        # Mock Tautulli history - 5 out of 10 episodes watched
        mock_tautulli_instance = mock_tautulli.return_value
        mock_tautulli_instance.get_episode_completed_history.return_value = [
            {
                "grandparent_rating_key": "1000",
                "season_num": 1,
                "episode_num": i,
                "user": "alice",
                "watched_at": f"170406720{i}",
                "watched_status": 1,
            }
            for i in range(1, 6)  # Episodes 1-5
        ]
        mock_tautulli_instance.build_series_metadata_cache.return_value = {"1000": "111111"}

        # Execute
        series = prunarr.get_series_with_watch_status(include_untagged=False)

        # CRITICAL: Verify partial watch status
        assert len(series) == 1
        assert series[0]["watch_status"] == "partially_watched"
        assert series[0]["watched_episodes"] == 5
        assert series[0]["total_episodes"] == 10
        assert series[0]["completion_percentage"] == 50.0


class TestCriticalErrorHandling:
    """Test critical error handling paths in tautulli."""

    @patch("requests.get")
    def test_tautulli_invalid_api_key(self, mock_get):
        """CRITICAL: Test handling of invalid API key."""
        from prunarr.tautulli import TautulliAPI

        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        api = TautulliAPI("http://localhost:8181", "invalid-key")

        with pytest.raises(ValueError, match="Invalid Tautulli API key"):
            api._request("test")

    @patch("requests.get")
    def test_tautulli_server_not_accessible(self, mock_get):
        """CRITICAL: Test handling of inaccessible server."""
        from prunarr.tautulli import TautulliAPI

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers.get.return_value = "application/json"
        mock_get.return_value = mock_response

        api = TautulliAPI("http://localhost:8181", "test-key")

        with pytest.raises(ValueError, match="Tautulli server not accessible"):
            api._request("test")

    @patch("requests.get")
    def test_tautulli_connection_error(self, mock_get):
        """CRITICAL: Test handling of connection errors."""
        import requests

        from prunarr.tautulli import TautulliAPI

        mock_get.side_effect = requests.exceptions.ConnectionError("Cannot connect")

        api = TautulliAPI("http://localhost:8181", "test-key")

        with pytest.raises(ValueError, match="Cannot connect to Tautulli"):
            api._request("test")

    @patch("requests.get")
    def test_tautulli_invalid_json_response(self, mock_get):
        """CRITICAL: Test handling of non-JSON responses."""
        from prunarr.tautulli import TautulliAPI

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = "text/html"
        mock_get.return_value = mock_response

        api = TautulliAPI("http://localhost:8181", "test-key")

        with pytest.raises(ValueError, match="Invalid response from Tautulli"):
            api._request("test")
