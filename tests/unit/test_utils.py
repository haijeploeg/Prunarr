"""
Unit tests for the utility functions module.

Tests formatting functions, episode key handling, and other shared utilities.
"""

from datetime import datetime

import pytest

from prunarr.utils import (
    format_completion_percentage,
    format_date,
    format_duration,
    format_episode_count,
    format_file_size,
    format_history_watch_status,
    format_movie_watch_status,
    format_series_watch_status,
    format_timestamp,
    make_episode_key,
    parse_episode_key,
)


class TestFormatFileSize:
    """Test file size formatting."""

    def test_zero_bytes(self):
        """Test formatting zero bytes."""
        assert format_file_size(0) == "0 B"

    def test_bytes(self):
        """Test formatting bytes."""
        assert format_file_size(100) == "100 B"
        assert format_file_size(512) == "512 B"

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(5120) == "5.00 KB"

    def test_megabytes(self):
        """Test formatting megabytes."""
        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 50) == "50.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_file_size(1024 * 1024 * 1024 * 2) == "2.00 GB"

    def test_terabytes(self):
        """Test formatting terabytes."""
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"

    def test_decimal_places(self):
        """Test correct decimal places based on size."""
        # < 10: 2 decimal places
        assert format_file_size(1536) == "1.50 KB"
        # >= 10 and < 100: 1 decimal place
        assert format_file_size(15360) == "15.0 KB"
        # >= 100: 0 decimal places
        assert format_file_size(153600) == "150 KB"


class TestFormatDate:
    """Test date formatting."""

    def test_valid_datetime(self):
        """Test formatting valid datetime object."""
        dt = datetime(2024, 3, 15, 10, 30)
        assert format_date(dt) == "2024-03-15"

    def test_none_date(self):
        """Test formatting None date."""
        assert format_date(None) == "N/A"

    def test_different_dates(self):
        """Test formatting various dates."""
        assert format_date(datetime(2020, 1, 1)) == "2020-01-01"
        assert format_date(datetime(2025, 12, 31)) == "2025-12-31"


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_valid_timestamp(self):
        """Test formatting valid Unix timestamp."""
        # January 1, 2024, 00:00:00 UTC
        timestamp = "1704067200"
        result = format_timestamp(timestamp)
        assert "2024-01-01" in result
        # Time will vary by timezone, just check format is HH:MM
        assert ":" in result

    def test_empty_timestamp(self):
        """Test formatting empty timestamp."""
        assert format_timestamp("") == "N/A"
        assert format_timestamp(None) == "N/A"

    def test_invalid_timestamp(self):
        """Test formatting invalid timestamp."""
        result = format_timestamp("invalid")
        assert result == "invalid"


class TestFormatDuration:
    """Test duration formatting."""

    def test_zero_duration(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "N/A"

    def test_minutes_only(self):
        """Test formatting durations under an hour."""
        assert format_duration(60) == "1m"
        assert format_duration(1800) == "30m"
        assert format_duration(3540) == "59m"

    def test_hours_and_minutes(self):
        """Test formatting durations with hours."""
        assert format_duration(3600) == "1h 0m"
        assert format_duration(3660) == "1h 1m"
        assert format_duration(7200) == "2h 0m"
        assert format_duration(9000) == "2h 30m"


class TestFormatMovieWatchStatus:
    """Test movie watch status formatting."""

    def test_watched_status(self):
        """Test formatting watched status."""
        result = format_movie_watch_status("watched")
        assert "[green]" in result
        assert "Watched" in result

    def test_unwatched_status(self):
        """Test formatting unwatched status."""
        result = format_movie_watch_status("unwatched")
        assert "[red]" in result
        assert "Unwatched" in result

    def test_watched_by_other_status(self):
        """Test formatting watched by other status."""
        result = format_movie_watch_status("watched_by_other")
        assert "[yellow]" in result
        assert "Watched" in result

    def test_unknown_status(self):
        """Test formatting unknown status."""
        result = format_movie_watch_status("unknown")
        assert "[dim]" in result
        assert "Unknown" in result


class TestFormatSeriesWatchStatus:
    """Test series watch status formatting."""

    def test_fully_watched(self):
        """Test formatting fully watched status."""
        result = format_series_watch_status("fully_watched")
        assert "[green]" in result
        assert "Fully Watched" in result

    def test_partially_watched(self):
        """Test formatting partially watched status."""
        result = format_series_watch_status("partially_watched")
        assert "[yellow]" in result
        assert "Partially Watched" in result

    def test_unwatched(self):
        """Test formatting unwatched status."""
        result = format_series_watch_status("unwatched")
        assert "[red]" in result
        assert "Unwatched" in result

    def test_no_episodes(self):
        """Test formatting no episodes status."""
        result = format_series_watch_status("no_episodes")
        assert "[dim]" in result
        assert "No Episodes" in result

    def test_unknown(self):
        """Test formatting unknown status."""
        result = format_series_watch_status("unknown")
        assert "[dim]" in result
        assert "Unknown" in result


class TestFormatHistoryWatchStatus:
    """Test history watch status formatting."""

    def test_watched_status(self):
        """Test formatting watched status (1)."""
        result = format_history_watch_status(1)
        assert "[green]" in result
        assert "Watched" in result

    def test_partial_status(self):
        """Test formatting partial status (0)."""
        result = format_history_watch_status(0)
        assert "[yellow]" in result
        assert "Partial" in result

    def test_stopped_status(self):
        """Test formatting stopped status (other values)."""
        result = format_history_watch_status(2)
        assert "[red]" in result
        assert "Stopped" in result


class TestFormatCompletionPercentage:
    """Test completion percentage formatting."""

    def test_zero_percent(self):
        """Test formatting 0%."""
        result = format_completion_percentage(0)
        assert "[dim]" in result
        assert "0%" in result

    def test_low_percentage(self):
        """Test formatting low percentage (< 50%)."""
        result = format_completion_percentage(25)
        assert "[red]" in result
        assert "25%" in result

    def test_medium_percentage(self):
        """Test formatting medium percentage (50-99%)."""
        result = format_completion_percentage(75)
        assert "[yellow]" in result
        assert "75%" in result

    def test_full_percentage(self):
        """Test formatting 100%."""
        result = format_completion_percentage(100)
        assert "[green]" in result
        assert "100%" in result


class TestFormatEpisodeCount:
    """Test episode count formatting."""

    def test_zero_episodes(self):
        """Test formatting zero episodes."""
        result = format_episode_count(0, 0)
        assert "[dim]" in result
        assert "0/0" in result

    def test_all_watched(self):
        """Test formatting all episodes watched."""
        result = format_episode_count(10, 10)
        assert "[green]" in result
        assert "10/10" in result

    def test_some_watched(self):
        """Test formatting some episodes watched."""
        result = format_episode_count(5, 10)
        assert "[yellow]" in result
        assert "5/10" in result

    def test_none_watched(self):
        """Test formatting no episodes watched."""
        result = format_episode_count(0, 10)
        assert "[red]" in result
        assert "0/10" in result


class TestMakeEpisodeKey:
    """Test episode key creation."""

    def test_standard_episode(self):
        """Test creating standard episode key."""
        assert make_episode_key(1, 5) == "s1e5"

    def test_double_digit_season(self):
        """Test creating key with double digit season."""
        assert make_episode_key(12, 3) == "s12e3"

    def test_double_digit_episode(self):
        """Test creating key with double digit episode."""
        assert make_episode_key(3, 24) == "s3e24"

    def test_season_zero(self):
        """Test creating key for season 0 (specials)."""
        assert make_episode_key(0, 1) == "s0e1"

    def test_triple_digits(self):
        """Test creating key with triple digit numbers."""
        assert make_episode_key(100, 999) == "s100e999"


class TestParseEpisodeKey:
    """Test episode key parsing."""

    def test_standard_episode_key(self):
        """Test parsing standard episode key."""
        result = parse_episode_key("s1e5")
        assert result == (1, 5)

    def test_double_digit_season(self):
        """Test parsing double digit season."""
        result = parse_episode_key("s12e3")
        assert result == (12, 3)

    def test_double_digit_episode(self):
        """Test parsing double digit episode."""
        result = parse_episode_key("s3e24")
        assert result == (3, 24)

    def test_season_zero(self):
        """Test parsing season 0."""
        result = parse_episode_key("s0e1")
        assert result == (0, 1)

    def test_uppercase(self):
        """Test parsing uppercase key."""
        result = parse_episode_key("S1E5")
        assert result == (1, 5)

    def test_mixed_case(self):
        """Test parsing mixed case key."""
        result = parse_episode_key("S1e5")
        assert result == (1, 5)

    def test_invalid_format(self):
        """Test parsing invalid format."""
        assert parse_episode_key("invalid") is None
        assert parse_episode_key("s1") is None
        assert parse_episode_key("e5") is None

    def test_non_numeric(self):
        """Test parsing non-numeric values."""
        assert parse_episode_key("sxey") is None
        assert parse_episode_key("s1ex") is None

    def test_empty_string(self):
        """Test parsing empty string."""
        assert parse_episode_key("") is None

    def test_none_input(self):
        """Test parsing None input."""
        assert parse_episode_key(None) is None


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_episode_key_roundtrip(self):
        """Test creating and parsing episode keys roundtrip."""
        season, episode = 5, 12
        key = make_episode_key(season, episode)
        parsed = parse_episode_key(key)
        assert parsed == (season, episode)

    def test_formatting_consistency(self):
        """Test that formatting functions handle edge cases consistently."""
        # All status formatters should handle unknown values
        movie_status = format_movie_watch_status("unknown_status")
        assert "[dim]" in movie_status

        series_status = format_series_watch_status("unknown_status")
        assert "[dim]" in series_status

    def test_size_formatting_consistency(self):
        """Test file size formatting consistency."""
        sizes = [0, 1024, 1024**2, 1024**3, 1024**4]
        for size in sizes:
            result = format_file_size(size)
            assert isinstance(result, str)
            assert len(result) > 0
