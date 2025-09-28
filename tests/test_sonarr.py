"""
Unit tests for the Sonarr API client module.

Tests the SonarrAPI class functionality including series retrieval,
episode management, file tracking, and comprehensive error handling.
"""

from unittest.mock import Mock, patch

import pytest

from prunarr.sonarr import SonarrAPI


class TestSonarrAPI:
    """Test the SonarrAPI class functionality."""

    def test_initialization(self):
        """Test SonarrAPI initialization."""
        api = SonarrAPI("http://localhost:8989", "test-api-key")

        assert api._base_url == "http://localhost:8989"
        assert api._api_key == "test-api-key"

    def test_initialization_url_normalization(self):
        """Test that URLs are normalized during initialization."""
        api = SonarrAPI("http://localhost:8989/", "test-api-key")
        assert api._base_url == "http://localhost:8989"

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_series_all(self, mock_pyarr):
        """Test getting all series."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_series.return_value = [
            {"id": 1, "title": "Series 1"},
            {"id": 2, "title": "Series 2"},
        ]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_series()

        mock_instance.get_series.assert_called_once_with()
        assert len(result) == 2
        assert result[0]["title"] == "Series 1"

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_series_by_id(self, mock_pyarr):
        """Test getting a specific series by ID."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_series.return_value = {"id": 1, "title": "Specific Series"}

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_series(series_id=1)

        mock_instance.get_series.assert_called_once_with(1)
        assert result["title"] == "Specific Series"

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_series_by_id_method(self, mock_pyarr):
        """Test get_series_by_id method."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_series.return_value = {"id": 1, "title": "Test Series"}

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_series_by_id(1)

        mock_instance.get_series.assert_called_once_with(1)
        assert result["title"] == "Test Series"

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episode_all(self, mock_pyarr):
        """Test getting all episodes."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.return_value = [
            {"id": 1, "title": "Episode 1"},
            {"id": 2, "title": "Episode 2"},
        ]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode()

        mock_instance.get_episode.assert_called_once_with()
        assert len(result) == 2

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episode_by_series_id(self, mock_pyarr):
        """Test getting episodes for a specific series."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.return_value = [{"id": 1, "title": "Episode 1"}]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode(series_id=123)

        mock_instance.get_episode.assert_called_once_with(series=123)
        assert len(result) == 1

    @patch("requests.get")
    def test_get_episodes_by_series_id_direct_api(self, mock_get):
        """Test get_episodes_by_series_id using direct HTTP call."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id": 1, "seriesId": 123, "title": "Episode 1"},
            {"id": 2, "seriesId": 123, "title": "Episode 2"},
        ]
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        mock_get.assert_called_once_with(
            "http://localhost:8989/api/v3/episode",
            params={"seriesId": 123, "includeImages": "false", "apikey": "test-api-key"},
            timeout=30,
        )
        assert len(result) == 2
        assert result[0]["title"] == "Episode 1"

    @patch("requests.get")
    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_by_series_id_fallback(self, mock_pyarr, mock_get):
        """Test get_episodes_by_series_id fallback to pyarr."""
        # Mock direct HTTP call failure
        mock_get.side_effect = Exception("HTTP error")

        # Mock pyarr fallback success
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.return_value = [{"id": 1, "title": "Episode 1"}]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        # Should fall back to pyarr
        mock_instance.get_episode.assert_called_with(seriesId=123)
        assert len(result) == 1
        assert result[0]["title"] == "Episode 1"

    @patch("requests.get")
    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_by_series_id_all_fallbacks_fail(self, mock_pyarr, mock_get):
        """Test get_episodes_by_series_id when all methods fail."""
        # Mock all methods failing
        mock_get.side_effect = Exception("HTTP error")
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.side_effect = Exception("Pyarr error")

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        # Should return empty list
        assert result == []

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_tag(self, mock_pyarr):
        """Test getting tag information."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_tag.return_value = {"id": 5, "label": "123 - testuser"}

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_tag(5)

        mock_instance.get_tag.assert_called_once_with(5)
        assert result["label"] == "123 - testuser"

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_delete_series_success(self, mock_pyarr):
        """Test successful series deletion."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.del_series.return_value = True

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.delete_series(123)

        mock_instance.del_series.assert_called_once_with(
            123, delete_files=True, add_exclusion=False
        )
        assert result is True

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_delete_series_with_options(self, mock_pyarr):
        """Test series deletion with custom options."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.del_series.return_value = True

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.delete_series(123, delete_files=False, add_exclusion=True)

        mock_instance.del_series.assert_called_once_with(
            123, delete_files=False, add_exclusion=True
        )
        assert result is True

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_delete_series_failure(self, mock_pyarr):
        """Test series deletion failure handling."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.del_series.side_effect = Exception("API error")

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.delete_series(123)

        assert result is False

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_season_info(self, mock_pyarr):
        """Test getting season information."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_series.return_value = {
            "id": 1,
            "seasons": [
                {"seasonNumber": 1, "statistics": {"episodeCount": 10}},
                {"seasonNumber": 2, "statistics": {"episodeCount": 12}},
            ],
        }

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_season_info(1)

        assert len(result) == 2
        assert result[0]["seasonNumber"] == 1
        assert result[1]["statistics"]["episodeCount"] == 12

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_season_info_exception(self, mock_pyarr):
        """Test get_season_info with API exception."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_series.side_effect = Exception("API error")

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_season_info(1)

        assert result == []

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_with_files(self, mock_pyarr):
        """Test getting episodes with file information."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.return_value = [
            {
                "id": 1,
                "seriesId": 123,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "Episode 1",
                "hasFile": True,
                "episodeFileId": 456,
            }
        ]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_with_files()

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["has_file"] is True
        assert result[0]["episode_file_id"] == 456

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_with_files_by_series(self, mock_pyarr):
        """Test getting episodes with files for specific series."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.return_value = [{"id": 1, "seriesId": 123, "hasFile": True}]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_with_files(series_id=123)

        mock_instance.get_episode.assert_called_once_with(series=123)
        assert len(result) == 1

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_with_files_exception(self, mock_pyarr):
        """Test get_episodes_with_files with API exception."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_episode.side_effect = Exception("API error")

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_with_files()

        assert result == []

    @patch("requests.get")
    def test_get_episode_files(self, mock_get):
        """Test getting episode file information."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {
                "id": 1,
                "seriesId": 123,
                "size": 1073741824,
                "quality": {"quality": {"name": "HDTV-1080p"}},
                "relativePath": "Season 01/Episode.mkv",
            }
        ]
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode_files()

        mock_get.assert_called_once_with(
            "http://localhost:8989/api/v3/episodefile",
            params={"apikey": "test-api-key"},
            timeout=30,
        )
        assert len(result) == 1
        assert result[0]["size"] == 1073741824

    @patch("requests.get")
    def test_get_episode_files_by_series(self, mock_get):
        """Test getting episode files for specific series."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": 1, "seriesId": 123}]
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode_files(series_id=123)

        mock_get.assert_called_once_with(
            "http://localhost:8989/api/v3/episodefile",
            params={"seriesId": 123, "apikey": "test-api-key"},
            timeout=30,
        )
        assert len(result) == 1

    @patch("requests.get")
    def test_get_episode_files_exception(self, mock_get):
        """Test get_episode_files with HTTP exception."""
        mock_get.side_effect = Exception("HTTP error")

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode_files()

        assert result == []

    @patch("pyarr.SonarrAPI.get_episode")
    def test_get_episodes_by_series_id_dict_response(self, mock_get):
        """Test get_episodes_by_series_id with dict response."""
        # Mock returning a single episode as dict instead of list
        mock_get.return_value = {"id": 1, "title": "Episode 1"}

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("pyarr.SonarrAPI.get_episode")
    def test_get_episodes_by_series_id_other_response(self, mock_get):
        """Test get_episodes_by_series_id with unexpected response type."""
        # Mock returning something unexpected (string)
        mock_get.return_value = "unexpected"

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert result == []

    @patch("pyarr.SonarrAPI.get_episode")
    def test_get_episodes_by_series_id_fallback_dict_response(self, mock_get):
        """Test get_episodes_by_series_id fallback with dict response."""
        # First call fails, second call returns dict
        mock_get.side_effect = [Exception("First failed"), {"id": 1, "title": "Episode 1"}]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("pyarr.SonarrAPI.get_episode")
    def test_get_episodes_by_series_id_fallback_other_response(self, mock_get):
        """Test get_episodes_by_series_id fallback with unexpected response."""
        # First call fails, second call returns unexpected type
        mock_get.side_effect = [Exception("First failed"), "unexpected"]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert result == []

    @patch("requests.get")
    def test_get_episode_files_dict_response(self, mock_get):
        """Test get_episode_files with dict response."""
        # Mock returning a single file as dict instead of list
        mock_response = Mock()
        mock_response.json.return_value = {"id": 1, "path": "/path/to/file"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode_files()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("pyarr.SonarrAPI.get_episode")
    def test_get_episodes_by_series_id_fallback_list_response(self, mock_get):
        """Test get_episodes_by_series_id fallback returns list."""
        # First call fails, second call returns list
        mock_get.side_effect = [Exception("First failed"), [{"id": 1, "title": "Episode 1"}]]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch("requests.get")
    def test_get_episode_files_other_response(self, mock_get):
        """Test get_episode_files with unexpected response type."""
        # Mock returning something unexpected
        mock_response = Mock()
        mock_response.json.return_value = "unexpected"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episode_files()

        assert result == []

    def test_get_series_episodes_summary_success(self):
        """Test get_series_episodes_summary successful execution."""
        api = SonarrAPI("http://localhost:8989", "test-api-key")

        with patch.object(api, "get_episodes_with_files") as mock_episodes:
            mock_episodes.return_value = [
                {"season_number": 1, "has_file": True},
                {"season_number": 1, "has_file": False},
                {"season_number": 2, "has_file": True},
                {"season_number": 2, "has_file": True},
            ]

            result = api.get_series_episodes_summary(123)

            assert result["series_id"] == 123
            assert result["total_seasons"] == 2
            assert result["total_episodes"] == 4
            assert result["downloaded_episodes"] == 3

            # Check season breakdown
            seasons = result["seasons"]
            season_1 = next(s for s in seasons if s["season_number"] == 1)
            season_2 = next(s for s in seasons if s["season_number"] == 2)

            assert season_1["total_episodes"] == 2
            assert season_1["downloaded_episodes"] == 1
            assert season_2["total_episodes"] == 2
            assert season_2["downloaded_episodes"] == 2

    def test_get_series_episodes_summary_exception(self):
        """Test get_series_episodes_summary with exception."""
        api = SonarrAPI("http://localhost:8989", "test-api-key")

        with patch.object(api, "get_episodes_with_files") as mock_episodes:
            mock_episodes.side_effect = Exception("API error")

            result = api.get_series_episodes_summary(123)

            assert result["series_id"] == 123
            assert result["total_seasons"] == 0
            assert result["total_episodes"] == 0
            assert result["downloaded_episodes"] == 0
            assert result["seasons"] == []


class TestSonarrAPIDataHandling:
    """Test data handling and edge cases in SonarrAPI."""

    @patch("requests.get")
    def test_get_episodes_by_series_id_single_episode_response(self, mock_get):
        """Test handling single episode response as dict instead of list."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 1, "title": "Single Episode"}
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert len(result) == 1
        assert result[0]["title"] == "Single Episode"

    @patch("requests.get")
    def test_get_episodes_by_series_id_unexpected_response(self, mock_get):
        """Test handling unexpected response type."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = "unexpected string response"
        mock_get.return_value = mock_response

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_by_series_id(123)

        assert result == []

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_with_files_data_transformation(self, mock_pyarr):
        """Test that episode data is properly transformed."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance

        # Test with complete episode data
        mock_instance.get_episode.return_value = [
            {
                "id": 1,
                "seriesId": 123,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "Pilot",
                "hasFile": True,
                "episodeFileId": 456,
                "airDate": "2023-01-01",
                "overview": "The first episode",
                "runtime": 42,
                "monitored": True,
            }
        ]

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_with_files()

        episode = result[0]
        assert episode["id"] == 1
        assert episode["series_id"] == 123
        assert episode["season_number"] == 1
        assert episode["episode_number"] == 1
        assert episode["title"] == "Pilot"
        assert episode["has_file"] is True
        assert episode["downloaded"] is True
        assert episode["episode_file_id"] == 456
        assert episode["air_date"] == "2023-01-01"
        assert episode["overview"] == "The first episode"
        assert episode["runtime"] == 42
        assert episode["monitored"] is True

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_with_files_missing_fields(self, mock_pyarr):
        """Test handling episodes with missing fields."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance

        # Episode with minimal data
        mock_instance.get_episode.return_value = [{"id": 1}]  # Only ID field

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_with_files()

        episode = result[0]
        assert episode["id"] == 1
        assert episode["series_id"] is None
        assert episode["has_file"] is False
        assert episode["downloaded"] is False
        assert episode["overview"] == ""
        assert episode["runtime"] == 0
        assert episode["monitored"] is False

    @patch("prunarr.sonarr.PyarrSonarrAPI")
    def test_get_episodes_with_files_non_list_response(self, mock_pyarr):
        """Test handling non-list response from get_episode."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance

        # Single episode returned as dict
        mock_instance.get_episode.return_value = {"id": 1, "title": "Single Episode"}

        api = SonarrAPI("http://localhost:8989", "test-api-key")
        result = api.get_episodes_with_files()

        assert len(result) == 1
        assert result[0]["id"] == 1

        # None response
        mock_instance.get_episode.return_value = None
        result = api.get_episodes_with_files()
        assert result == []
