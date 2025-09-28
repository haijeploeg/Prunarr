"""
Unit tests for the core PrunArr class.

Tests the main PrunArr orchestration class functionality including
media correlation, user tag extraction, and cleanup operations.
"""

from unittest.mock import Mock, patch

from prunarr.prunarr import PrunArr
from prunarr.config import Settings


class TestPrunArr:
    """Test the PrunArr core class functionality."""

    def test_initialization(self, mock_settings):
        """Test PrunArr initialization."""
        prunarr = PrunArr(mock_settings)

        assert prunarr.settings == mock_settings
        assert hasattr(prunarr, 'radarr')
        assert hasattr(prunarr, 'sonarr')
        assert hasattr(prunarr, 'tautulli')

    @patch('prunarr.prunarr.RadarrAPI')
    @patch('prunarr.prunarr.SonarrAPI')
    @patch('prunarr.prunarr.TautulliAPI')
    def test_api_initialization(self, mock_tautulli, mock_sonarr, mock_radarr, mock_settings):
        """Test that API clients are initialized correctly."""
        prunarr = PrunArr(mock_settings)

        mock_radarr.assert_called_once_with(
            mock_settings.radarr_url,
            mock_settings.radarr_api_key
        )
        mock_sonarr.assert_called_once_with(
            mock_settings.sonarr_url,
            mock_settings.sonarr_api_key
        )
        mock_tautulli.assert_called_once_with(
            mock_settings.tautulli_url,
            mock_settings.tautulli_api_key
        )

    def test_extract_username_from_tag_valid(self, mock_settings):
        """Test extracting username from valid tag labels."""
        prunarr = PrunArr(mock_settings)

        test_cases = [
            ("123 - john_doe", "john_doe"),
            ("456 - jane.smith", "jane.smith"),
            ("789 - user@email.com", "user@email.com"),
            ("1 - a", "a"),
            ("999999 - very_long_username_here", "very_long_username_here")
        ]

        for tag_label, expected_username in test_cases:
            result = prunarr._extract_username_from_tag(tag_label)
            assert result == expected_username

    def test_extract_username_from_tag_invalid(self, mock_settings):
        """Test extracting username from invalid tag labels."""
        prunarr = PrunArr(mock_settings)

        invalid_cases = [
            "invalid_tag",
            "123-john_doe",  # No spaces
            "- john_doe",  # No ID
            "123 -",  # No username
            "",  # Empty string
            "123 john_doe",  # Missing dash
            "abc - john_doe"  # Non-numeric ID
        ]

        for tag_label in invalid_cases:
            result = prunarr._extract_username_from_tag(tag_label)
            assert result is None

    def test_extract_username_from_tag_custom_regex(self):
        """Test extracting username with custom regex pattern."""
        custom_settings = Settings(
            radarr_api_key="key",
            radarr_url="http://localhost:7878",
            sonarr_api_key="key",
            sonarr_url="http://localhost:8989",
            tautulli_api_key="key",
            tautulli_url="http://localhost:8181",
            user_tag_regex=r"^user:(.+)$"
        )

        prunarr = PrunArr(custom_settings)

        assert prunarr._extract_username_from_tag("user:john_doe") == "john_doe"
        assert prunarr._extract_username_from_tag("123 - john_doe") is None

    def test_get_movies_list_with_tags(self, mock_settings, mock_radarr_api):
        """Test getting movies list with tag information."""
        mock_radarr_api.get_movie.return_value = [
            {
                "id": 1,
                "title": "Movie 1",
                "tags": [1, 2],
                "hasFile": True,
                "movieFile": {"size": 1073741824}
            },
            {
                "id": 2,
                "title": "Movie 2",
                "tags": [3],
                "hasFile": False
            }
        ]

        mock_radarr_api.get_tag.side_effect = [
            {"id": 1, "label": "123 - testuser"},
            {"id": 2, "label": "456 - otheruser"},
            {"id": 3, "label": "invalid_tag"}
        ]

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_list_with_tags()

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["user_tags"] == ["123 - testuser", "456 - otheruser"]
            assert result[1]["id"] == 2
            assert result[1]["user_tags"] == ["invalid_tag"]

    def test_get_movies_list_with_tags_api_exception(self, mock_settings, mock_radarr_api):
        """Test get_movies_list_with_tags with API exception."""
        mock_radarr_api.get_movie.side_effect = Exception("API error")

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_list_with_tags()

            assert result == []

    def test_get_series_list_with_tags(self, mock_settings, mock_sonarr_api):
        """Test getting series list with tag information."""
        mock_sonarr_api.get_series.return_value = [
            {
                "id": 1,
                "title": "Series 1",
                "tags": [1],
                "statistics": {"episodeCount": 10, "totalEpisodeCount": 10}
            },
            {
                "id": 2,
                "title": "Series 2",
                "tags": [2],
                "statistics": {"episodeCount": 5, "totalEpisodeCount": 20}
            }
        ]

        mock_sonarr_api.get_tag.side_effect = [
            {"id": 1, "label": "123 - testuser"},
            {"id": 2, "label": "456 - otheruser"}
        ]

        with patch('prunarr.prunarr.SonarrAPI', return_value=mock_sonarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_series_list_with_tags()

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["user_tags"] == ["123 - testuser"]
            assert result[0]["statistics"]["episodeCount"] == 10
            assert result[1]["statistics"]["totalEpisodeCount"] == 20

    def test_get_series_list_with_tags_no_statistics(self, mock_settings, mock_sonarr_api):
        """Test series list handling when statistics are missing."""
        mock_sonarr_api.get_series.return_value = [
            {
                "id": 1,
                "title": "Series 1",
                "tags": [1]
                # No statistics field
            }
        ]

        mock_sonarr_api.get_tag.return_value = {"id": 1, "label": "123 - testuser"}

        with patch('prunarr.prunarr.SonarrAPI', return_value=mock_sonarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_series_list_with_tags()

            assert len(result) == 1
            assert result[0]["statistics"] == {}

    def test_get_movies_for_user(self, mock_settings, mock_radarr_api):
        """Test getting movies for a specific user."""
        mock_radarr_api.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tags": [1]},
            {"id": 2, "title": "Movie 2", "tags": [2]},
            {"id": 3, "title": "Movie 3", "tags": [1, 3]}
        ]

        mock_radarr_api.get_tag.side_effect = [
            {"id": 1, "label": "123 - testuser"},
            {"id": 2, "label": "456 - otheruser"},
            {"id": 3, "label": "invalid_tag"}
        ]

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_for_user("testuser")

            # Should only return movies with tags for testuser
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 3
            for movie in result:
                assert any("testuser" in tag for tag in movie["user_tags"])

    def test_get_movies_for_user_not_found(self, mock_settings, mock_radarr_api):
        """Test getting movies for user with no matches."""
        mock_radarr_api.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tags": [1]}
        ]

        mock_radarr_api.get_tag.return_value = {"id": 1, "label": "123 - otheruser"}

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_for_user("testuser")

            assert len(result) == 0

    def test_get_series_for_user(self, mock_settings, mock_sonarr_api):
        """Test getting series for a specific user."""
        mock_sonarr_api.get_series.return_value = [
            {"id": 1, "title": "Series 1", "tags": [1], "statistics": {}},
            {"id": 2, "title": "Series 2", "tags": [2], "statistics": {}},
            {"id": 3, "title": "Series 3", "tags": [1, 3], "statistics": {}}
        ]

        mock_sonarr_api.get_tag.side_effect = [
            {"id": 1, "label": "123 - testuser"},
            {"id": 2, "label": "456 - otheruser"},
            {"id": 3, "label": "invalid_tag"}
        ]

        with patch('prunarr.prunarr.SonarrAPI', return_value=mock_sonarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_series_for_user("testuser")

            # Should only return series with tags for testuser
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 3

    def test_correlate_movie_with_watch_history(self, mock_settings):
        """Test correlating movie with watch history."""
        movie = {
            "id": 1,
            "title": "Test Movie",
            "year": 2023,
            "tmdbId": 12345,
            "user_tags": ["123 - testuser"]
        }

        watch_history = [
            {
                "title": "Test Movie",
                "user": "testuser",
                "watched_at": 1640995200,
                "media_type": "movie"
            },
            {
                "title": "Other Movie",
                "user": "testuser",
                "watched_at": 1640995200,
                "media_type": "movie"
            }
        ]

        prunarr = PrunArr(mock_settings)
        result = prunarr._correlate_movie_with_watch_history(movie, watch_history)

        assert result["watched"] is True
        assert result["last_watched"] == 1640995200
        assert result["watched_by"] == ["testuser"]

    def test_correlate_movie_with_watch_history_no_match(self, mock_settings):
        """Test movie correlation with no matching watch history."""
        movie = {
            "id": 1,
            "title": "Test Movie",
            "year": 2023,
            "tmdbId": 12345,
            "user_tags": ["123 - testuser"]
        }

        watch_history = [
            {
                "title": "Other Movie",
                "user": "testuser",
                "watched_at": 1640995200,
                "media_type": "movie"
            }
        ]

        prunarr = PrunArr(mock_settings)
        result = prunarr._correlate_movie_with_watch_history(movie, watch_history)

        assert result["watched"] is False
        assert result["last_watched"] is None
        assert result["watched_by"] == []

    def test_correlate_movie_different_users(self, mock_settings):
        """Test movie correlation with different users."""
        movie = {
            "id": 1,
            "title": "Test Movie",
            "year": 2023,
            "tmdbId": 12345,
            "user_tags": ["123 - user1", "456 - user2"]
        }

        watch_history = [
            {
                "title": "Test Movie",
                "user": "user1",
                "watched_at": 1640995200,
                "media_type": "movie"
            },
            {
                "title": "Test Movie",
                "user": "user3",  # Different user, shouldn't match
                "watched_at": 1640995300,
                "media_type": "movie"
            }
        ]

        prunarr = PrunArr(mock_settings)
        result = prunarr._correlate_movie_with_watch_history(movie, watch_history)

        assert result["watched"] is True
        assert result["watched_by"] == ["user1"]

    def test_correlate_series_with_watch_history(self, mock_settings):
        """Test correlating series with episode watch history."""
        series = {
            "id": 1,
            "title": "Test Series",
            "year": 2023,
            "tvdbId": 12345,
            "user_tags": ["123 - testuser"],
            "statistics": {"episodeCount": 10, "totalEpisodeCount": 10}
        }

        episode_history = [
            {
                "series_title": "Test Series",
                "user": "testuser",
                "watched_at": 1640995200,
                "season_num": 1,
                "episode_num": 1
            },
            {
                "series_title": "Test Series",
                "user": "testuser",
                "watched_at": 1640995300,
                "season_num": 1,
                "episode_num": 2
            }
        ]

        prunarr = PrunArr(mock_settings)
        result = prunarr._correlate_series_with_watch_history(series, episode_history)

        assert result["watched_episodes"] == 2
        assert result["total_episodes"] == 10
        assert result["completion_percentage"] == 20.0
        assert result["last_watched"] == 1640995300
        assert result["watched_by"] == ["testuser"]

    def test_correlate_series_fully_watched(self, mock_settings):
        """Test series correlation when fully watched."""
        series = {
            "id": 1,
            "title": "Test Series",
            "user_tags": ["123 - testuser"],
            "statistics": {"episodeCount": 2, "totalEpisodeCount": 2}
        }

        episode_history = [
            {"series_title": "Test Series", "user": "testuser", "watched_at": 1640995200},
            {"series_title": "Test Series", "user": "testuser", "watched_at": 1640995300}
        ]

        prunarr = PrunArr(mock_settings)
        result = prunarr._correlate_series_with_watch_history(series, episode_history)

        assert result["watched_episodes"] == 2
        assert result["total_episodes"] == 2
        assert result["completion_percentage"] == 100.0
        assert result["watch_status"] == "fully_watched"

    def test_correlate_series_no_episodes(self, mock_settings):
        """Test series correlation with no downloaded episodes."""
        series = {
            "id": 1,
            "title": "Test Series",
            "user_tags": ["123 - testuser"],
            "statistics": {"episodeCount": 0, "totalEpisodeCount": 10}
        }

        episode_history = []

        prunarr = PrunArr(mock_settings)
        result = prunarr._correlate_series_with_watch_history(series, episode_history)

        assert result["watch_status"] == "no_episodes"
        assert result["completion_percentage"] == 0.0

    def test_get_watch_status_for_movies(self, mock_settings, mock_tautulli_api):
        """Test getting watch status for movies."""
        movies = [
            {"id": 1, "title": "Movie 1", "user_tags": ["123 - testuser"]},
            {"id": 2, "title": "Movie 2", "user_tags": ["456 - otheruser"]}
        ]

        mock_tautulli_api.get_movie_completed_history.return_value = [
            {"title": "Movie 1", "user": "testuser", "watched_at": 1640995200}
        ]

        with patch('prunarr.prunarr.TautulliAPI', return_value=mock_tautulli_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_watch_status_for_movies(movies)

            assert len(result) == 2
            assert result[0]["watched"] is True
            assert result[1]["watched"] is False

    def test_get_watch_status_for_series(self, mock_settings, mock_tautulli_api):
        """Test getting watch status for series."""
        series_list = [
            {
                "id": 1,
                "title": "Series 1",
                "user_tags": ["123 - testuser"],
                "statistics": {"episodeCount": 5, "totalEpisodeCount": 10}
            }
        ]

        mock_tautulli_api.get_episode_completed_history.return_value = [
            {"series_title": "Series 1", "user": "testuser", "watched_at": 1640995200},
            {"series_title": "Series 1", "user": "testuser", "watched_at": 1640995300}
        ]

        with patch('prunarr.prunarr.TautulliAPI', return_value=mock_tautulli_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_watch_status_for_series(series_list)

            assert len(result) == 1
            assert result[0]["watched_episodes"] == 2
            assert result[0]["completion_percentage"] == 20.0

    def test_get_movies_for_users_multiple(self, mock_settings, mock_radarr_api):
        """Test getting movies for multiple users."""
        mock_radarr_api.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tags": [1]},
            {"id": 2, "title": "Movie 2", "tags": [2]},
            {"id": 3, "title": "Movie 3", "tags": [1, 2]}
        ]

        mock_radarr_api.get_tag.side_effect = [
            {"id": 1, "label": "123 - user1"},
            {"id": 2, "label": "456 - user2"}
        ]

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_for_users(["user1", "user2"])

            assert len(result) == 3
            # All movies should be included as they have tags for requested users


class TestPrunArrErrorHandling:
    """Test error handling in PrunArr class."""

    def test_tag_api_exception(self, mock_settings, mock_radarr_api):
        """Test handling tag API exceptions."""
        mock_radarr_api.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tags": [1]}
        ]

        mock_radarr_api.get_tag.side_effect = Exception("Tag API error")

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_list_with_tags()

            # Should handle the exception gracefully
            assert len(result) == 1
            assert result[0]["user_tags"] == []

    def test_empty_movie_list(self, mock_settings, mock_radarr_api):
        """Test handling empty movie list."""
        mock_radarr_api.get_movie.return_value = []

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_list_with_tags()

            assert result == []

    def test_movies_without_tags(self, mock_settings, mock_radarr_api):
        """Test handling movies without tags."""
        mock_radarr_api.get_movie.return_value = [
            {"id": 1, "title": "Movie 1"},  # No tags field
            {"id": 2, "title": "Movie 2", "tags": []}  # Empty tags
        ]

        with patch('prunarr.prunarr.RadarrAPI', return_value=mock_radarr_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_movies_list_with_tags()

            assert len(result) == 2
            assert result[0]["user_tags"] == []
            assert result[1]["user_tags"] == []

    def test_tautulli_api_exception(self, mock_settings, mock_tautulli_api):
        """Test handling Tautulli API exceptions."""
        movies = [{"id": 1, "title": "Movie 1", "user_tags": ["123 - testuser"]}]

        mock_tautulli_api.get_movie_completed_history.side_effect = Exception("Tautulli error")

        with patch('prunarr.prunarr.TautulliAPI', return_value=mock_tautulli_api):
            prunarr = PrunArr(mock_settings)
            result = prunarr.get_watch_status_for_movies(movies)

            # Should handle exception and return original movies with no watch data
            assert len(result) == 1
            assert "watched" not in result[0] or result[0]["watched"] is False


class TestPrunArrHelperMethods:
    """Test helper methods in PrunArr class."""

    def test_normalize_title_basic(self, mock_settings):
        """Test basic title normalization."""
        prunarr = PrunArr(mock_settings)

        test_cases = [
            ("The Movie", "movie"),
            ("A Series", "series"),
            ("An Episode", "episode"),
            ("Movie Title", "movie title"),
            ("THE MOVIE", "movie"),  # Case insensitive
            ("  Spaced  ", "spaced"),  # Trim whitespace
        ]

        for input_title, expected in test_cases:
            result = prunarr._normalize_title(input_title)
            assert result == expected

    def test_normalize_title_special_characters(self, mock_settings):
        """Test title normalization with special characters."""
        prunarr = PrunArr(mock_settings)

        test_cases = [
            ("Movie: The Sequel", "movie the sequel"),
            ("Series (2023)", "series 2023"),
            ("Movie & Series", "movie series"),
            ("Title-With-Dashes", "title with dashes"),
        ]

        for input_title, expected in test_cases:
            result = prunarr._normalize_title(input_title)
            assert result == expected

    def test_year_matching_tolerance(self, mock_settings):
        """Test year matching with tolerance."""
        prunarr = PrunArr(mock_settings)

        # Test cases: (movie_year, history_year, should_match)
        test_cases = [
            (2023, 2023, True),   # Exact match
            (2023, 2022, True),   # Within tolerance
            (2023, 2024, True),   # Within tolerance
            (2023, 2021, False),  # Outside tolerance
            (2023, 2025, False),  # Outside tolerance
            (None, 2023, True),   # No movie year
            (2023, None, True),   # No history year
        ]

        for movie_year, history_year, should_match in test_cases:
            result = prunarr._years_match(movie_year, history_year)
            assert result == should_match

    def test_extract_usernames_from_tags(self, mock_settings):
        """Test extracting usernames from tag lists."""
        prunarr = PrunArr(mock_settings)

        user_tags = [
            "123 - user1",
            "456 - user2",
            "invalid_tag",
            "789 - user3"
        ]

        result = prunarr._extract_usernames_from_tags(user_tags)
        assert set(result) == {"user1", "user2", "user3"}

    def test_calculate_watch_statistics(self, mock_settings):
        """Test watch statistics calculation."""
        prunarr = PrunArr(mock_settings)

        # Test various episode counts
        test_cases = [
            (10, 10, 100.0, "fully_watched"),
            (5, 10, 50.0, "partially_watched"),
            (0, 10, 0.0, "unwatched"),
            (0, 0, 0.0, "no_episodes"),
            (3, 10, 30.0, "partially_watched")
        ]

        for watched, total, expected_pct, expected_status in test_cases:
            pct, status = prunarr._calculate_watch_statistics(watched, total)
            assert pct == expected_pct
            assert status == expected_status