"""
Pytest configuration and shared fixtures for PrunArr tests.

This module provides common test fixtures and configuration for all test modules,
including mock API clients, sample data, and test configuration objects.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from pathlib import Path
import tempfile
import yaml

from prunarr.config import Settings
from prunarr.logger import PrunArrLogger


@pytest.fixture
def mock_settings():
    """Create a mock Settings object with test configuration."""
    return Settings(
        radarr_api_key="test-radarr-key",
        radarr_url="http://localhost:7878",
        sonarr_api_key="test-sonarr-key",
        sonarr_url="http://localhost:8989",
        tautulli_api_key="test-tautulli-key",
        tautulli_url="http://localhost:8181",
        user_tag_regex=r"^\d+ - (.+)$"
    )


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    config_data = {
        "radarr_api_key": "test-radarr-key",
        "radarr_url": "http://localhost:7878",
        "sonarr_api_key": "test-sonarr-key",
        "sonarr_url": "http://localhost:8989",
        "tautulli_api_key": "test-tautulli-key",
        "tautulli_url": "http://localhost:8181",
        "user_tag_regex": r"^\d+ - (.+)$"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_radarr_api():
    """Create a mock Radarr API client."""
    mock_api = Mock()
    mock_api.get_movie.return_value = [
        {
            "id": 1,
            "title": "Test Movie",
            "year": 2023,
            "tmdbId": 12345,
            "tags": [1],
            "hasFile": True,
            "movieFile": {
                "id": 1,
                "size": 1073741824,  # 1GB
                "quality": {"quality": {"name": "Bluray-1080p"}},
                "relativePath": "Test Movie (2023)/Test Movie (2023) Bluray-1080p.mkv"
            }
        }
    ]
    mock_api.get_tag.return_value = {"id": 1, "label": "123 - testuser"}
    mock_api.delete_movie.return_value = True
    mock_api.get_movie_by_tmdb_id.return_value = mock_api.get_movie.return_value[0]
    mock_api.get_movies_by_tag.return_value = mock_api.get_movie.return_value
    return mock_api


@pytest.fixture
def mock_sonarr_api():
    """Create a mock Sonarr API client."""
    mock_api = Mock()
    mock_api.get_series.return_value = [
        {
            "id": 1,
            "title": "Test Series",
            "year": 2023,
            "tvdbId": 54321,
            "tags": [1],
            "seasons": [
                {
                    "seasonNumber": 1,
                    "statistics": {
                        "episodeCount": 10,
                        "episodeFileCount": 10,
                        "totalEpisodeCount": 10,
                        "sizeOnDisk": 5368709120  # 5GB
                    }
                }
            ],
            "statistics": {
                "episodeCount": 10,
                "episodeFileCount": 10,
                "totalEpisodeCount": 10,
                "sizeOnDisk": 5368709120
            }
        }
    ]
    mock_api.get_episodes_by_series_id.return_value = [
        {
            "id": 1,
            "seriesId": 1,
            "seasonNumber": 1,
            "episodeNumber": 1,
            "title": "Test Episode",
            "hasFile": True,
            "episodeFileId": 1
        }
    ]
    mock_api.get_episode_files.return_value = [
        {
            "id": 1,
            "seriesId": 1,
            "seasonNumber": 1,
            "episodeNumber": 1,
            "size": 536870912,  # 512MB
            "quality": {"quality": {"name": "HDTV-1080p"}},
            "relativePath": "Season 01/Test Series - S01E01 - Test Episode HDTV-1080p.mkv"
        }
    ]
    mock_api.get_tag.return_value = {"id": 1, "label": "123 - testuser"}
    mock_api.delete_series.return_value = True
    return mock_api


@pytest.fixture
def mock_tautulli_api():
    """Create a mock Tautulli API client."""
    mock_api = Mock()
    mock_api.get_watch_history.return_value = [
        {
            "id": 1,
            "title": "Test Movie",
            "rating_key": "12345",
            "user_id": 123,
            "friendly_name": "testuser",
            "date": 1640995200,  # 2022-01-01
            "watched_status": 1,
            "media_type": "movie",
            "year": 2023,
            "duration": 7200,
            "percent_complete": 100
        }
    ]
    mock_api.get_movie_completed_history.return_value = mock_api.get_watch_history.return_value
    mock_api.get_episode_completed_history.return_value = [
        {
            "title": "Test Episode",
            "rating_key": "54321",
            "parent_rating_key": "543",
            "grandparent_rating_key": "54",
            "user": "testuser",
            "watched_at": 1640995200,
            "watched_status": 1,
            "media_type": "episode",
            "season_num": 1,
            "episode_num": 1,
            "series_title": "Test Series"
        }
    ]
    mock_api.get_metadata.return_value = {
        "title": "Test Movie",
        "year": 2023,
        "rating": "8.5",
        "summary": "A test movie",
        "guids": ["imdb://tt1234567", "tvdb://12345"]
    }
    mock_api.get_imdb_id_from_rating_key.return_value = "tt1234567"
    mock_api.get_tvdb_id_from_rating_key.return_value = "12345"
    return mock_api


@pytest.fixture
def sample_movie_data():
    """Sample movie data for testing."""
    return {
        "id": 1,
        "title": "Test Movie",
        "year": 2023,
        "tmdbId": 12345,
        "tags": [1],
        "hasFile": True,
        "movieFile": {
            "id": 1,
            "size": 1073741824,
            "quality": {"quality": {"name": "Bluray-1080p"}},
            "relativePath": "Test Movie (2023)/Test Movie (2023) Bluray-1080p.mkv"
        }
    }


@pytest.fixture
def sample_series_data():
    """Sample series data for testing."""
    return {
        "id": 1,
        "title": "Test Series",
        "year": 2023,
        "tvdbId": 54321,
        "tags": [1],
        "seasons": [
            {
                "seasonNumber": 1,
                "statistics": {
                    "episodeCount": 10,
                    "episodeFileCount": 10,
                    "totalEpisodeCount": 10,
                    "sizeOnDisk": 5368709120
                }
            }
        ],
        "statistics": {
            "episodeCount": 10,
            "episodeFileCount": 10,
            "totalEpisodeCount": 10,
            "sizeOnDisk": 5368709120
        }
    }


@pytest.fixture
def sample_watch_history():
    """Sample watch history data for testing."""
    return [
        {
            "id": 1,
            "title": "Test Movie",
            "rating_key": "12345",
            "user_id": 123,
            "friendly_name": "testuser",
            "date": 1640995200,
            "watched_status": 1,
            "media_type": "movie",
            "year": 2023,
            "duration": 7200,
            "percent_complete": 100
        }
    ]


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock(spec=PrunArrLogger)


@pytest.fixture
def captured_output():
    """Fixture to capture console output during tests."""
    from io import StringIO
    import sys

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = StringIO()
    stderr_capture = StringIO()

    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    yield stdout_capture, stderr_capture

    sys.stdout = old_stdout
    sys.stderr = old_stderr