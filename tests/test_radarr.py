"""
Unit tests for the Radarr API client module.

Tests the RadarrAPI class functionality including movie retrieval,
tag management, deletion operations, and error handling.
"""

from unittest.mock import Mock, patch

from prunarr.radarr import RadarrAPI


class TestRadarrAPI:
    """Test the RadarrAPI class functionality."""

    def test_initialization(self):
        """Test RadarrAPI initialization."""
        api = RadarrAPI("http://localhost:7878", "test-api-key")

        assert api.base_url == "http://localhost:7878"
        assert api.api_key == "test-api-key"

    def test_initialization_url_normalization(self):
        """Test that URLs are normalized during initialization."""
        api = RadarrAPI("http://localhost:7878/", "test-api-key")
        assert api.base_url == "http://localhost:7878"

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_all(self, mock_pyarr):
        """Test getting all movies."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie 1"},
            {"id": 2, "title": "Movie 2"}
        ]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie()

        mock_instance.get_movie.assert_called_once_with()
        assert len(result) == 2
        assert result[0]["title"] == "Movie 1"

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_by_id(self, mock_pyarr):
        """Test getting a specific movie by ID."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = {"id": 1, "title": "Specific Movie"}

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie(movie_id=1)

        mock_instance.get_movie.assert_called_once_with(1)
        assert result["title"] == "Specific Movie"

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_with_kwargs(self, mock_pyarr):
        """Test getting movies with additional parameters."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [{"id": 1, "title": "Monitored Movie"}]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie(monitored=True)

        mock_instance.get_movie.assert_called_once_with(monitored=True)
        assert len(result) == 1

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_tag(self, mock_pyarr):
        """Test getting tag information."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_tag.return_value = {"id": 5, "label": "123 - testuser"}

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_tag(5)

        mock_instance.get_tag.assert_called_once_with(5)
        assert result["label"] == "123 - testuser"

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_delete_movie_success(self, mock_pyarr):
        """Test successful movie deletion."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.del_movie.return_value = True

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.delete_movie(123)

        mock_instance.del_movie.assert_called_once_with(
            123, delete_files=True, add_exclusion=False
        )
        assert result is True

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_delete_movie_with_options(self, mock_pyarr):
        """Test movie deletion with custom options."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.del_movie.return_value = True

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.delete_movie(123, delete_files=False, add_exclusion=True)

        mock_instance.del_movie.assert_called_once_with(
            123, delete_files=False, add_exclusion=True
        )
        assert result is True

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_delete_movie_failure(self, mock_pyarr):
        """Test movie deletion failure handling."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.del_movie.side_effect = Exception("API error")

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.delete_movie(123)

        mock_instance.del_movie.assert_called_once()
        assert result is False

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_by_tmdb_id_found(self, mock_pyarr):
        """Test finding a movie by TMDB ID."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tmdbId": 12345},
            {"id": 2, "title": "Movie 2", "tmdbId": 67890}
        ]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_by_tmdb_id(12345)

        assert result is not None
        assert result["title"] == "Movie 1"
        assert result["tmdbId"] == 12345

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_by_tmdb_id_not_found(self, mock_pyarr):
        """Test searching for a non-existent TMDB ID."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tmdbId": 12345}
        ]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_by_tmdb_id(99999)

        assert result is None

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_by_tmdb_id_exception(self, mock_pyarr):
        """Test TMDB ID search with API exception."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.side_effect = Exception("API error")

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_by_tmdb_id(12345)

        assert result is None

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movies_by_tag(self, mock_pyarr):
        """Test getting movies filtered by tag."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tags": [1, 2]},
            {"id": 2, "title": "Movie 2", "tags": [2, 3]},
            {"id": 3, "title": "Movie 3", "tags": [1]}
        ]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movies_by_tag(1)

        assert len(result) == 2
        assert result[0]["title"] == "Movie 1"
        assert result[1]["title"] == "Movie 3"

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movies_by_tag_no_matches(self, mock_pyarr):
        """Test getting movies by tag with no matches."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie 1", "tags": [2, 3]}
        ]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movies_by_tag(1)

        assert len(result) == 0

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movies_by_tag_exception(self, mock_pyarr):
        """Test getting movies by tag with API exception."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.side_effect = Exception("API error")

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movies_by_tag(1)

        assert result == []

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_file_info_with_file(self, mock_pyarr):
        """Test getting movie file info when file exists."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [{
            "id": 1,
            "movieFile": {
                "id": 123,
                "size": 1073741824,
                "quality": {"quality": {"name": "Bluray-1080p"}},
                "relativePath": "Movie/Movie.mkv"
            }
        }]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_file_info(1)

        assert result is not None
        assert result["size"] == 1073741824
        assert result["quality"]["quality"]["name"] == "Bluray-1080p"

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_file_info_no_file(self, mock_pyarr):
        """Test getting movie file info when no file exists."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [{"id": 1}]  # No movieFile

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_file_info(1)

        assert result is None

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_file_info_empty_response(self, mock_pyarr):
        """Test getting movie file info with empty API response."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = []

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_file_info(1)

        assert result is None

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_get_movie_file_info_exception(self, mock_pyarr):
        """Test getting movie file info with API exception."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.side_effect = Exception("API error")

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movie_file_info(1)

        assert result is None

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_movies_without_tags(self, mock_pyarr):
        """Test handling movies without tags field."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie without tags"},
            {"id": 2, "title": "Movie with tags", "tags": [1]}
        ]

        api = RadarrAPI("http://localhost:7878", "test-api-key")
        result = api.get_movies_by_tag(1)

        # Should only return the movie that has the tag
        assert len(result) == 1
        assert result[0]["title"] == "Movie with tags"


class TestRadarrAPIIntegration:
    """Integration tests for RadarrAPI error handling and edge cases."""

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_pyarr_api_initialization(self, mock_pyarr):
        """Test that PyarrRadarrAPI is initialized correctly."""
        RadarrAPI("http://localhost:7878", "test-key")

        mock_pyarr.assert_called_once_with("http://localhost:7878", "test-key")

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_method_call_forwarding(self, mock_pyarr):
        """Test that method calls are forwarded to PyarrRadarrAPI correctly."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance

        api = RadarrAPI("http://localhost:7878", "test-key")

        # Test different method calls
        api.get_movie()
        api.get_movie(123, monitored=True)
        api.get_tag(5)

        # Verify calls were forwarded correctly
        mock_instance.get_movie.assert_any_call()
        mock_instance.get_movie.assert_any_call(123, monitored=True)
        mock_instance.get_tag.assert_called_once_with(5)

    def test_real_initialization_attributes(self):
        """Test that real initialization sets attributes correctly."""
        api = RadarrAPI("http://test:7878/", "my-key")

        assert api.base_url == "http://test:7878"
        assert api.api_key == "my-key"
        assert hasattr(api, '_api')

    @patch('prunarr.radarr.PyarrRadarrAPI')
    def test_complex_movie_filtering(self, mock_pyarr):
        """Test complex movie filtering scenarios."""
        mock_instance = Mock()
        mock_pyarr.return_value = mock_instance

        # Complex movie data with various tag combinations
        mock_instance.get_movie.return_value = [
            {"id": 1, "title": "Movie A", "tags": [1, 2, 3]},
            {"id": 2, "title": "Movie B", "tags": [2, 4]},
            {"id": 3, "title": "Movie C", "tags": []},
            {"id": 4, "title": "Movie D"},  # No tags field
            {"id": 5, "title": "Movie E", "tags": [1, 5]}
        ]

        api = RadarrAPI("http://localhost:7878", "test-key")

        # Test filtering by different tags
        result_tag_1 = api.get_movies_by_tag(1)
        result_tag_2 = api.get_movies_by_tag(2)
        result_tag_999 = api.get_movies_by_tag(999)

        assert len(result_tag_1) == 2  # Movie A and Movie E
        assert len(result_tag_2) == 2  # Movie A and Movie B
        assert len(result_tag_999) == 0  # No movies with tag 999