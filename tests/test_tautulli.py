"""
Unit tests for the Tautulli API client module.

Tests the TautulliAPI class functionality including watch history retrieval,
metadata extraction, ID extraction, and pagination handling.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from prunarr.tautulli import TautulliAPI, IMDB_ID_PATTERN, TVDB_ID_PATTERN


class TestTautulliAPI:
    """Test the TautulliAPI class functionality."""

    def test_initialization(self):
        """Test TautulliAPI initialization."""
        api = TautulliAPI("http://localhost:8181", "test-api-key")

        assert api.base_url == "http://localhost:8181"
        assert api.api_key == "test-api-key"

    def test_initialization_url_normalization(self):
        """Test that URLs are normalized during initialization."""
        api = TautulliAPI("http://localhost:8181/", "test-api-key")
        assert api.base_url == "http://localhost:8181"

    @patch('requests.get')
    def test_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {"data": {"key": "value"}}
        }
        mock_get.return_value = mock_response

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api._request("test_command", {"param": "value"})

        mock_get.assert_called_once_with(
            "http://localhost:8181/api/v2",
            params={
                "apikey": "test-api-key",
                "cmd": "test_command",
                "param": "value"
            },
            timeout=15
        )
        assert result == {"data": {"key": "value"}}

    @patch('requests.get')
    def test_request_with_no_params(self, mock_get):
        """Test API request without additional parameters."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"success": True}}
        mock_get.return_value = mock_response

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api._request("simple_command")

        mock_get.assert_called_once_with(
            "http://localhost:8181/api/v2",
            params={
                "apikey": "test-api-key",
                "cmd": "simple_command"
            },
            timeout=15
        )
        assert result == {"success": True}

    @patch('requests.get')
    def test_request_http_error(self, mock_get):
        """Test API request with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP 404")
        mock_get.return_value = mock_response

        api = TautulliAPI("http://localhost:8181", "test-api-key")

        with pytest.raises(requests.HTTPError):
            api._request("test_command")

    @patch('requests.get')
    def test_request_timeout(self, mock_get):
        """Test API request timeout."""
        mock_get.side_effect = requests.Timeout("Request timeout")

        api = TautulliAPI("http://localhost:8181", "test-api-key")

        with pytest.raises(requests.Timeout):
            api._request("test_command")

    @patch.object(TautulliAPI, '_request')
    def test_get_watch_history_basic(self, mock_request):
        """Test basic watch history retrieval."""
        mock_request.return_value = {
            "data": {
                "data": [
                    {"id": 1, "title": "Movie 1"},
                    {"id": 2, "title": "Movie 2"}
                ]
            }
        }

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_watch_history(limit=2)

        mock_request.assert_called_once_with(
            "get_history",
            params={
                "length": 2,
                "start": 0,
                "order_column": "date",
                "order_dir": "desc"
            }
        )
        assert len(result) == 2
        assert result[0]["title"] == "Movie 1"

    @patch.object(TautulliAPI, '_request')
    def test_get_watch_history_pagination(self, mock_request):
        """Test watch history pagination."""
        # First page
        mock_request.side_effect = [
            {
                "data": {
                    "data": [
                        {"id": 1, "title": "Movie 1"},
                        {"id": 2, "title": "Movie 2"}
                    ]
                }
            },
            {
                "data": {
                    "data": [
                        {"id": 3, "title": "Movie 3"}
                    ]
                }
            },
            {
                "data": {
                    "data": []  # Empty page indicates end
                }
            }
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_watch_history(page_size=2)

        assert len(result) == 3
        assert mock_request.call_count == 2  # Should stop after second call

    @patch.object(TautulliAPI, '_request')
    def test_get_watch_history_with_limit(self, mock_request):
        """Test watch history with limit enforcement."""
        mock_request.side_effect = [
            {
                "data": {
                    "data": [
                        {"id": 1, "title": "Movie 1"},
                        {"id": 2, "title": "Movie 2"}
                    ]
                }
            },
            {
                "data": {
                    "data": [
                        {"id": 3, "title": "Movie 3"}
                    ]
                }
            }
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_watch_history(page_size=2, limit=3)

        assert len(result) == 3
        assert result[2]["title"] == "Movie 3"

    @patch.object(TautulliAPI, '_request')
    def test_get_watch_history_custom_sorting(self, mock_request):
        """Test watch history with custom sorting."""
        mock_request.return_value = {
            "data": {
                "data": [{"id": 1, "title": "Movie 1"}]
            }
        }

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        api.get_watch_history(order_column="friendly_name", order_dir="asc")

        mock_request.assert_called_once_with(
            "get_history",
            params={
                "length": 100,  # default page_size
                "start": 0,
                "order_column": "friendly_name",
                "order_dir": "asc"
            }
        )

    @patch.object(TautulliAPI, 'get_watch_history')
    def test_get_movie_completed_history(self, mock_get_history):
        """Test getting completed movie history."""
        mock_get_history.return_value = [
            {
                "title": "Movie 1",
                "rating_key": "123",
                "friendly_name": "user1",
                "date": 1640995200,
                "watched_status": 1,
                "media_type": "movie"
            },
            {
                "title": "Episode 1",
                "rating_key": "456",
                "friendly_name": "user1",
                "date": 1640995200,
                "watched_status": 1,
                "media_type": "episode"
            },
            {
                "title": "Movie 2",
                "rating_key": "789",
                "friendly_name": "user1",
                "date": 1640995200,
                "watched_status": 0,
                "media_type": "movie"
            }
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_movie_completed_history()

        # Should only return completed movies
        assert len(result) == 1
        assert result[0]["title"] == "Movie 1"
        assert result[0]["media_type"] == "movie"
        assert result[0]["watched_status"] == 1

    @patch.object(TautulliAPI, 'get_watch_history')
    def test_get_filtered_history(self, mock_get_history):
        """Test getting filtered history."""
        mock_get_history.return_value = [
            {
                "id": 1,
                "title": "Movie 1",
                "user_id": 123,
                "friendly_name": "testuser",
                "watched_status": 1,
                "media_type": "movie",
                "date": 1640995200
            },
            {
                "id": 2,
                "title": "Movie 2",
                "user_id": 456,
                "friendly_name": "otheruser",
                "watched_status": 0,
                "media_type": "movie",
                "date": 1640995200
            }
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_filtered_history(
            watched_only=True,
            username="testuser",
            media_type="movie"
        )

        # Should only return the matching record
        assert len(result) == 1
        assert result[0]["title"] == "Movie 1"
        assert result[0]["user"] == "testuser"

    @patch.object(TautulliAPI, 'get_watch_history')
    def test_get_filtered_history_with_limit(self, mock_get_history):
        """Test filtered history with result limit."""
        # Mock more data than the limit
        mock_data = []
        for i in range(10):
            mock_data.append({
                "id": i,
                "title": f"Movie {i}",
                "user_id": 123,
                "friendly_name": "testuser",
                "watched_status": 1,
                "media_type": "movie",
                "date": 1640995200
            })

        mock_get_history.return_value = mock_data

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_filtered_history(limit=5)

        assert len(result) == 5

    @patch.object(TautulliAPI, 'get_watch_history')
    def test_get_history_item_details(self, mock_get_history):
        """Test getting details for a specific history item."""
        mock_get_history.return_value = [
            {"id": 1, "title": "Movie 1", "rating_key": "123"},
            {"id": 2, "title": "Movie 2", "rating_key": "456"}
        ]

        with patch.object(TautulliAPI, 'get_metadata') as mock_get_metadata:
            mock_get_metadata.return_value = {
                "summary": "A great movie",
                "rating": "8.5"
            }

            with patch.object(TautulliAPI, 'get_imdb_id_from_rating_key') as mock_get_imdb:
                mock_get_imdb.return_value = "tt1234567"

                api = TautulliAPI("http://localhost:8181", "test-api-key")
                result = api.get_history_item_details(1)

                assert result["history_id"] == 1
                assert result["title"] == "Movie 1"
                assert result["imdb_id"] == "tt1234567"
                assert result["summary"] == "A great movie"
                assert result["rating"] == "8.5"

    @patch.object(TautulliAPI, 'get_watch_history')
    def test_get_history_item_details_not_found(self, mock_get_history):
        """Test getting details for non-existent history item."""
        mock_get_history.return_value = [
            {"id": 1, "title": "Movie 1"}
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_history_item_details(999)

        assert result == {}

    @patch.object(TautulliAPI, '_request')
    def test_get_metadata(self, mock_request):
        """Test getting metadata for a rating key."""
        mock_request.return_value = {
            "data": {
                "title": "Test Movie",
                "year": 2023,
                "summary": "A test movie"
            }
        }

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_metadata("12345")

        mock_request.assert_called_once_with(
            "get_metadata",
            params={"rating_key": "12345"}
        )
        assert result["title"] == "Test Movie"

    @patch.object(TautulliAPI, 'get_metadata')
    def test_get_imdb_id_from_rating_key(self, mock_get_metadata):
        """Test extracting IMDb ID from metadata."""
        mock_get_metadata.return_value = {
            "guids": [
                "plex://movie/5d7768294ced9d001e61dc83",
                "imdb://tt1234567",
                "tvdb://123456"
            ]
        }

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_imdb_id_from_rating_key("12345")

        assert result == "tt1234567"

    @patch.object(TautulliAPI, 'get_metadata')
    def test_get_imdb_id_from_rating_key_not_found(self, mock_get_metadata):
        """Test IMDb ID extraction when not found."""
        mock_get_metadata.return_value = {
            "guids": [
                "plex://movie/5d7768294ced9d001e61dc83",
                "tvdb://123456"
            ]
        }

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_imdb_id_from_rating_key("12345")

        assert result is None

    @patch.object(TautulliAPI, 'get_metadata')
    def test_get_imdb_id_no_guids(self, mock_get_metadata):
        """Test IMDb ID extraction with no guids."""
        mock_get_metadata.return_value = {}

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_imdb_id_from_rating_key("12345")

        assert result is None

    @patch.object(TautulliAPI, 'get_watch_history')
    def test_get_episode_completed_history(self, mock_get_history):
        """Test getting completed episode history."""
        mock_get_history.return_value = [
            {
                "title": "Episode 1",
                "rating_key": "123",
                "parent_rating_key": "12",
                "grandparent_rating_key": "1",
                "friendly_name": "user1",
                "date": 1640995200,
                "watched_status": 1,
                "media_type": "episode",
                "parent_media_index": 1,
                "media_index": 1,
                "grandparent_title": "Test Series"
            },
            {
                "title": "Movie 1",
                "watched_status": 1,
                "media_type": "movie"
            }
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_episode_completed_history()

        # Should only return completed episodes
        assert len(result) == 1
        assert result[0]["title"] == "Episode 1"
        assert result[0]["media_type"] == "episode"
        assert result[0]["season_num"] == 1
        assert result[0]["episode_num"] == 1
        assert result[0]["series_title"] == "Test Series"

    @patch.object(TautulliAPI, 'get_metadata')
    def test_get_tvdb_id_from_rating_key(self, mock_get_metadata):
        """Test extracting TVDB ID from metadata."""
        mock_get_metadata.return_value = {
            "guids": [
                "tvdb://123456",
                "imdb://tt1234567"
            ]
        }

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_tvdb_id_from_rating_key("12345")

        assert result == "123456"

    @patch.object(TautulliAPI, 'get_metadata')
    def test_build_series_metadata_cache(self, mock_get_metadata):
        """Test building series metadata cache."""
        episode_history = [
            {"grandparent_rating_key": "100"},
            {"grandparent_rating_key": "200"},
            {"grandparent_rating_key": "100"},  # Duplicate
            {"grandparent_rating_key": "300"}
        ]

        # Mock metadata responses
        metadata_responses = {
            "100": {"guids": ["tvdb://111"]},
            "200": {"guids": ["tvdb://222"]},
            "300": {"guids": ["imdb://tt333"]}  # No TVDB ID
        }

        def metadata_side_effect(rating_key):
            return metadata_responses.get(rating_key, {})

        mock_get_metadata.side_effect = metadata_side_effect

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.build_series_metadata_cache(episode_history)

        assert result == {"100": "111", "200": "222"}
        # Should not include series without TVDB ID
        assert "300" not in result

    @patch.object(TautulliAPI, 'get_metadata')
    def test_build_series_metadata_cache_with_exceptions(self, mock_get_metadata):
        """Test building series cache with API exceptions."""
        episode_history = [
            {"grandparent_rating_key": "100"},
            {"grandparent_rating_key": "200"}
        ]

        def metadata_side_effect(rating_key):
            if rating_key == "100":
                return {"guids": ["tvdb://111"]}
            else:
                raise Exception("API error")

        mock_get_metadata.side_effect = metadata_side_effect

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.build_series_metadata_cache(episode_history)

        # Should continue processing despite exception
        assert result == {"100": "111"}
        assert "200" not in result


class TestTautulliRegexPatterns:
    """Test the regex patterns used for ID extraction."""

    def test_imdb_id_pattern_valid(self):
        """Test valid IMDb ID patterns."""
        test_cases = [
            ("imdb://tt1234567", "tt1234567"),
            ("imdb://tt0123456", "tt0123456"),
            ("imdb://tt9876543", "tt9876543")
        ]

        for guid, expected in test_cases:
            match = IMDB_ID_PATTERN.match(guid)
            assert match is not None
            assert match.group(1) == expected

    def test_imdb_id_pattern_invalid(self):
        """Test invalid IMDb ID patterns."""
        invalid_cases = [
            "tvdb://123456",
            "imdb://1234567",  # Missing 'tt'
            "tt1234567",  # Missing protocol
            "imdb://tt",  # No numbers
            "imdb://abc123"  # Invalid format
        ]

        for guid in invalid_cases:
            match = IMDB_ID_PATTERN.match(guid)
            assert match is None

    def test_tvdb_id_pattern_valid(self):
        """Test valid TVDB ID patterns."""
        test_cases = [
            ("tvdb://123456", "123456"),
            ("tvdb://1", "1"),
            ("tvdb://999999999", "999999999")
        ]

        for guid, expected in test_cases:
            match = TVDB_ID_PATTERN.match(guid)
            assert match is not None
            assert match.group(1) == expected

    def test_tvdb_id_pattern_invalid(self):
        """Test invalid TVDB ID patterns."""
        invalid_cases = [
            "imdb://tt123456",
            "tvdb://abc123",  # Non-numeric
            "tvdb://",  # No ID
            "123456",  # Missing protocol
            "tvdb://12.34"  # Decimal numbers
        ]

        for guid in invalid_cases:
            match = TVDB_ID_PATTERN.match(guid)
            assert match is None


class TestTautulliAPIIntegration:
    """Integration tests for TautulliAPI functionality."""

    @patch.object(TautulliAPI, '_request')
    def test_complex_filtering_scenario(self, mock_request):
        """Test complex filtering with multiple criteria."""
        # Mock paginated response
        mock_request.side_effect = [
            {
                "data": {
                    "data": [
                        {
                            "id": 1,
                            "title": "Movie 1",
                            "user_id": 123,
                            "friendly_name": "testuser",
                            "watched_status": 1,
                            "media_type": "movie",
                            "date": 1640995200
                        },
                        {
                            "id": 2,
                            "title": "Episode 1",
                            "user_id": 123,
                            "friendly_name": "testuser",
                            "watched_status": 1,
                            "media_type": "episode",
                            "date": 1640995200
                        }
                    ]
                }
            },
            {
                "data": {
                    "data": []  # End of data
                }
            }
        ]

        api = TautulliAPI("http://localhost:8181", "test-api-key")
        result = api.get_filtered_history(
            watched_only=True,
            username="testuser",
            media_type="movie"
        )

        # Should only return the movie, not the episode
        assert len(result) == 1
        assert result[0]["title"] == "Movie 1"
        assert result[0]["media_type"] == "movie"

    def test_real_initialization_attributes(self):
        """Test that real initialization sets attributes correctly."""
        api = TautulliAPI("http://test:8181/", "my-key")

        assert api.base_url == "http://test:8181"
        assert api.api_key == "my-key"