"""
Unit tests for CLI command modules.

Tests the individual command implementations including movies, series,
and history commands with their various options and functionality.
"""

from unittest.mock import Mock, patch
from typer.testing import CliRunner

from prunarr.commands import movies, series, history


class TestMoviesCommands:
    """Test the movies command module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_movies_list_command(self, mock_settings):
        """Test movies list command."""
        # Mock context with settings
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance

            # Mock movie data
            mock_instance.get_movies_list_with_tags.return_value = [
                {
                    "id": 1,
                    "title": "Test Movie",
                    "year": 2023,
                    "user_tags": ["123 - testuser"],
                    "hasFile": True,
                    "movieFile": {"size": 1073741824}
                }
            ]

            mock_instance.get_watch_status_for_movies.return_value = [
                {
                    "id": 1,
                    "title": "Test Movie",
                    "year": 2023,
                    "watched": True,
                    "last_watched": 1640995200,
                    "file_size": 1073741824
                }
            ]

            result = self.runner.invoke(movies.app, ["list"], obj=mock_ctx.obj)

            assert result.exit_code == 0
            mock_instance.get_movies_list_with_tags.assert_called_once()
            mock_instance.get_watch_status_for_movies.assert_called_once()

    def test_movies_list_with_user_filter(self, mock_settings):
        """Test movies list command with user filter."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_movies_for_users.return_value = []
            mock_instance.get_watch_status_for_movies.return_value = []

            result = self.runner.invoke(
                movies.app,
                ["list", "--user", "testuser"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            mock_instance.get_movies_for_users.assert_called_once_with(["testuser"])

    def test_movies_list_multiple_users(self, mock_settings):
        """Test movies list command with multiple users."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_movies_for_users.return_value = []
            mock_instance.get_watch_status_for_movies.return_value = []

            result = self.runner.invoke(
                movies.app,
                ["list", "--user", "user1", "--user", "user2"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            mock_instance.get_movies_for_users.assert_called_once_with(["user1", "user2"])

    def test_movies_list_watched_filter(self, mock_settings):
        """Test movies list command with watched filter."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_movies_list_with_tags.return_value = []

            # Mock watch status with both watched and unwatched movies
            mock_instance.get_watch_status_for_movies.return_value = [
                {"id": 1, "title": "Watched Movie", "watched": True},
                {"id": 2, "title": "Unwatched Movie", "watched": False}
            ]

            result = self.runner.invoke(
                movies.app,
                ["list", "--watched"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            # Should filter to only watched movies

    def test_movies_remove_command(self, mock_settings):
        """Test movies remove command."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_movies_list_with_tags.return_value = []
            mock_instance.get_watch_status_for_movies.return_value = []

            with patch('rich.prompt.Confirm.ask', return_value=False):
                result = self.runner.invoke(movies.app, ["remove"], obj=mock_ctx.obj)

            assert result.exit_code == 0

    def test_movies_format_file_size(self):
        """Test file size formatting function."""
        from prunarr.commands.movies import format_file_size

        test_cases = [
            (0, "0 B"),
            (1024, "1.0 KB"),
            (1048576, "1.0 MB"),
            (1073741824, "1.0 GB"),
            (1099511627776, "1.0 TB"),
            (1536, "1.5 KB"),
            (1536000, "1.5 MB")
        ]

        for size_bytes, expected in test_cases:
            result = format_file_size(size_bytes)
            assert result == expected

    def test_movies_sort_function(self):
        """Test movie sorting function."""
        from prunarr.commands.movies import sort_movies

        movies_data = [
            {"title": "B Movie", "year": 2022, "last_watched": 100, "file_size": 2000},
            {"title": "A Movie", "year": 2023, "last_watched": 200, "file_size": 1000},
            {"title": "C Movie", "year": 2021, "last_watched": 300, "file_size": 3000}
        ]

        # Test sorting by title
        result = sort_movies(movies_data, "title")
        assert result[0]["title"] == "A Movie"

        # Test sorting by year descending
        result = sort_movies(movies_data, "year", desc=True)
        assert result[0]["year"] == 2023

        # Test sorting by file size
        result = sort_movies(movies_data, "file_size")
        assert result[0]["file_size"] == 1000


class TestSeriesCommands:
    """Test the series command module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_series_list_command(self, mock_settings):
        """Test series list command."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance

            mock_instance.get_series_list_with_tags.return_value = [
                {
                    "id": 1,
                    "title": "Test Series",
                    "year": 2023,
                    "user_tags": ["123 - testuser"],
                    "statistics": {"episodeCount": 10, "totalEpisodeCount": 10}
                }
            ]

            mock_instance.get_watch_status_for_series.return_value = [
                {
                    "id": 1,
                    "title": "Test Series",
                    "watched_episodes": 5,
                    "total_episodes": 10,
                    "completion_percentage": 50.0,
                    "watch_status": "partially_watched"
                }
            ]

            result = self.runner.invoke(series.app, ["list"], obj=mock_ctx.obj)

            assert result.exit_code == 0
            mock_instance.get_series_list_with_tags.assert_called_once()
            mock_instance.get_watch_status_for_series.assert_called_once()

    def test_series_list_with_filters(self, mock_settings):
        """Test series list command with various filters."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_series_for_user.return_value = []
            mock_instance.get_watch_status_for_series.return_value = []

            # Test username filter
            result = self.runner.invoke(
                series.app,
                ["list", "--username", "testuser"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            mock_instance.get_series_for_user.assert_called_once_with("testuser")

    def test_series_list_watch_status_filters(self, mock_settings):
        """Test series list with watch status filters."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_series_list_with_tags.return_value = []

            # Mock series with different watch statuses
            mock_instance.get_watch_status_for_series.return_value = [
                {"id": 1, "watch_status": "fully_watched", "completion_percentage": 100.0},
                {"id": 2, "watch_status": "partially_watched", "completion_percentage": 50.0},
                {"id": 3, "watch_status": "unwatched", "completion_percentage": 0.0}
            ]

            # Test watched filter
            result = self.runner.invoke(
                series.app,
                ["list", "--watched"],
                obj=mock_ctx.obj
            )
            assert result.exit_code == 0

            # Test partially watched filter
            result = self.runner.invoke(
                series.app,
                ["list", "--partially-watched"],
                obj=mock_ctx.obj
            )
            assert result.exit_code == 0

    def test_series_get_command(self, mock_settings):
        """Test series get command for detailed view."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance

            # Mock series data
            mock_series = {
                "id": 1,
                "title": "Test Series",
                "year": 2023,
                "user_tags": ["123 - testuser"]
            }

            # Mock Sonarr API
            mock_sonarr = Mock()
            mock_instance.sonarr = mock_sonarr
            mock_sonarr.get_series_by_id.return_value = mock_series
            mock_sonarr.get_episodes_by_series_id.return_value = [
                {"seasonNumber": 1, "episodeNumber": 1, "title": "Episode 1", "hasFile": True}
            ]
            mock_sonarr.get_episode_files.return_value = [
                {"seasonNumber": 1, "size": 1073741824}
            ]

            result = self.runner.invoke(
                series.app,
                ["get", "1"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            mock_sonarr.get_series_by_id.assert_called_once_with(1)

    def test_series_format_functions(self):
        """Test series formatting helper functions."""
        from prunarr.commands.series import (
            format_watch_status,
            format_completion_percentage,
            format_file_size
        )

        # Test watch status formatting
        assert "✓ Fully Watched" in format_watch_status("fully_watched")
        assert "📺 Partially Watched" in format_watch_status("partially_watched")
        assert "✗ Unwatched" in format_watch_status("unwatched")

        # Test completion percentage formatting
        assert "100%" in format_completion_percentage(100.0)
        assert "50%" in format_completion_percentage(50.0)
        assert "0%" in format_completion_percentage(0.0)

        # Test file size formatting
        assert format_file_size(1073741824) == "1.0 GB"

    def test_series_remove_command(self, mock_settings):
        """Test series remove command."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_series_list_with_tags.return_value = []
            mock_instance.get_watch_status_for_series.return_value = []

            with patch('rich.prompt.Confirm.ask', return_value=False):
                result = self.runner.invoke(series.app, ["remove"], obj=mock_ctx.obj)

            assert result.exit_code == 0


class TestHistoryCommands:
    """Test the history command module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_history_show_command(self, mock_settings):
        """Test history show command."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.history.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance

            mock_instance.tautulli.get_filtered_history.return_value = [
                {
                    "history_id": 1,
                    "title": "Test Movie",
                    "user": "testuser",
                    "watched_at": 1640995200,
                    "media_type": "movie",
                    "duration": 7200,
                    "percent_complete": 100
                }
            ]

            result = self.runner.invoke(history.app, ["show"], obj=mock_ctx.obj)

            assert result.exit_code == 0
            mock_instance.tautulli.get_filtered_history.assert_called_once()

    def test_history_show_with_filters(self, mock_settings):
        """Test history show command with filters."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.history.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.tautulli.get_filtered_history.return_value = []

            # Test with username filter
            result = self.runner.invoke(
                history.app,
                ["show", "--username", "testuser"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            mock_instance.tautulli.get_filtered_history.assert_called_with(
                watched_only=False,
                username="testuser",
                media_type=None,
                limit=None
            )

            # Test with media type filter
            result = self.runner.invoke(
                history.app,
                ["show", "--media-type", "movie"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0

            # Test with watched only filter
            result = self.runner.invoke(
                history.app,
                ["show", "--watched-only"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0

            # Test with limit
            result = self.runner.invoke(
                history.app,
                ["show", "--limit", "50"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0

    def test_history_format_functions(self):
        """Test history formatting helper functions."""
        from prunarr.commands.history import format_duration, format_timestamp

        # Test duration formatting
        assert format_duration(7200) == "2h 0m"
        assert format_duration(3661) == "1h 1m"
        assert format_duration(90) == "1m 30s"
        assert format_duration(45) == "45s"

        # Test timestamp formatting
        timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
        result = format_timestamp(timestamp)
        assert "2022" in result

    def test_history_get_command(self, mock_settings):
        """Test history get command for detailed view."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.history.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance

            mock_instance.tautulli.get_history_item_details.return_value = {
                "history_id": 1,
                "title": "Test Movie",
                "user": "testuser",
                "watched_at": 1640995200,
                "media_type": "movie",
                "summary": "A test movie",
                "rating": "8.5",
                "duration": 7200
            }

            result = self.runner.invoke(
                history.app,
                ["get", "1"],
                obj=mock_ctx.obj
            )

            assert result.exit_code == 0
            mock_instance.tautulli.get_history_item_details.assert_called_once_with(1)


class TestCommandErrorHandling:
    """Test error handling in command modules."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_movies_command_with_api_error(self, mock_settings):
        """Test movies command handling API errors."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_movies_list_with_tags.side_effect = Exception("API Error")

            with patch('prunarr.commands.movies.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                result = self.runner.invoke(movies.app, ["list"], obj=mock_ctx.obj)

                # Should handle error gracefully
                mock_logger.error.assert_called()

    def test_series_command_with_api_error(self, mock_settings):
        """Test series command handling API errors."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_series_list_with_tags.side_effect = Exception("API Error")

            with patch('prunarr.commands.series.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                result = self.runner.invoke(series.app, ["list"], obj=mock_ctx.obj)

                mock_logger.error.assert_called()

    def test_history_command_with_api_error(self, mock_settings):
        """Test history command handling API errors."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.history.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.tautulli.get_filtered_history.side_effect = Exception("API Error")

            with patch('prunarr.commands.history.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                result = self.runner.invoke(history.app, ["show"], obj=mock_ctx.obj)

                mock_logger.error.assert_called()

    def test_command_context_validation(self, mock_settings):
        """Test that commands validate context properly."""
        # Test with missing context
        result = self.runner.invoke(movies.app, ["list"])
        # Should handle missing context gracefully

        # Test with invalid context
        invalid_ctx = {"invalid": "context"}
        result = self.runner.invoke(movies.app, ["list"], obj=invalid_ctx)
        # Should handle invalid context gracefully


class TestCommandOutputFormatting:
    """Test command output formatting and Rich integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_movies_table_output(self, mock_settings):
        """Test that movies command produces table output."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.movies.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_movies_list_with_tags.return_value = [
                {
                    "id": 1,
                    "title": "Test Movie",
                    "year": 2023,
                    "user_tags": ["123 - testuser"],
                    "hasFile": True
                }
            ]
            mock_instance.get_watch_status_for_movies.return_value = [
                {
                    "id": 1,
                    "title": "Test Movie",
                    "watched": True,
                    "last_watched": 1640995200,
                    "file_size": 1073741824
                }
            ]

            result = self.runner.invoke(movies.app, ["list"], obj=mock_ctx.obj)

            assert result.exit_code == 0
            # Output should contain table formatting (Rich markup)

    def test_series_table_output(self, mock_settings):
        """Test that series command produces table output."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.series.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.get_series_list_with_tags.return_value = [
                {
                    "id": 1,
                    "title": "Test Series",
                    "year": 2023,
                    "user_tags": ["123 - testuser"],
                    "statistics": {"episodeCount": 10}
                }
            ]
            mock_instance.get_watch_status_for_series.return_value = [
                {
                    "id": 1,
                    "title": "Test Series",
                    "watched_episodes": 5,
                    "total_episodes": 10,
                    "completion_percentage": 50.0
                }
            ]

            result = self.runner.invoke(series.app, ["list"], obj=mock_ctx.obj)

            assert result.exit_code == 0

    def test_history_table_output(self, mock_settings):
        """Test that history command produces table output."""
        mock_ctx = Mock()
        mock_ctx.obj = {"settings": mock_settings, "debug": False}

        with patch('prunarr.commands.history.PrunArr') as mock_prunarr:
            mock_instance = Mock()
            mock_prunarr.return_value = mock_instance
            mock_instance.tautulli.get_filtered_history.return_value = [
                {
                    "history_id": 1,
                    "title": "Test Movie",
                    "user": "testuser",
                    "watched_at": 1640995200,
                    "media_type": "movie",
                    "duration": 7200
                }
            ]

            result = self.runner.invoke(history.app, ["show"], obj=mock_ctx.obj)

            assert result.exit_code == 0