# PrunArr Test Suite

This directory contains comprehensive tests for the PrunArr CLI application.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── test_config.py           # Configuration module tests
├── test_logger.py           # Logger module tests
├── test_radarr.py          # Radarr API client tests
├── test_sonarr.py          # Sonarr API client tests
├── test_tautulli.py        # Tautulli API client tests
├── test_prunarr.py         # Core PrunArr class tests
├── test_cli.py             # CLI application tests
├── test_commands.py        # Command module tests
├── requirements.txt        # Test dependencies
└── README.md              # This file
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Run configuration tests
pytest tests/test_config.py

# Run API client tests
pytest tests/test_radarr.py tests/test_sonarr.py tests/test_tautulli.py

# Run CLI tests
pytest tests/test_cli.py tests/test_commands.py
```

### Run Tests with Coverage

```bash
pytest --cov=prunarr --cov-report=html
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only CLI tests
pytest -m cli

# Run integration tests
pytest -m integration
```

## Test Categories

### Unit Tests
- **Configuration**: YAML loading, validation, environment variable handling
- **Logger**: Message formatting, log levels, Rich console integration
- **API Clients**: Radarr, Sonarr, and Tautulli API interactions (mocked)
- **Core Logic**: PrunArr class media correlation and processing

### Integration Tests
- **CLI Commands**: Full command execution with mocked dependencies
- **Error Handling**: Configuration errors, API failures, validation errors
- **Output Formatting**: Rich table formatting and console output

### Test Fixtures

#### Configuration
- `mock_settings`: Valid Settings object for testing
- `temp_config_file`: Temporary YAML configuration file

#### API Clients
- `mock_radarr_api`: Mocked Radarr API with sample movie data
- `mock_sonarr_api`: Mocked Sonarr API with sample series data
- `mock_tautulli_api`: Mocked Tautulli API with sample watch history

#### Sample Data
- `sample_movie_data`: Complete movie objects with metadata
- `sample_series_data`: Complete series objects with seasons/episodes
- `sample_watch_history`: Watch history records for correlation

## Test Data

### Sample Movie Data
```python
{
    "id": 1,
    "title": "Test Movie",
    "year": 2023,
    "tmdbId": 12345,
    "tags": [1],
    "hasFile": True,
    "movieFile": {
        "size": 1073741824,  # 1GB
        "quality": {"quality": {"name": "Bluray-1080p"}}
    }
}
```

### Sample Series Data
```python
{
    "id": 1,
    "title": "Test Series",
    "year": 2023,
    "tvdbId": 54321,
    "tags": [1],
    "seasons": [{
        "seasonNumber": 1,
        "statistics": {
            "episodeCount": 10,
            "totalEpisodeCount": 10,
            "sizeOnDisk": 5368709120  # 5GB
        }
    }]
}
```

### Sample Watch History
```python
{
    "id": 1,
    "title": "Test Movie",
    "user_id": 123,
    "friendly_name": "testuser",
    "date": 1640995200,  # Unix timestamp
    "watched_status": 1,
    "media_type": "movie",
    "percent_complete": 100
}
```

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>`

### Using Fixtures
```python
def test_my_function(mock_settings, mock_radarr_api):
    """Test description."""
    # Use fixtures directly
    assert mock_settings.radarr_url == "http://localhost:7878"
```

### Mocking External Dependencies
```python
@patch('prunarr.module.ExternalClass')
def test_with_mock(mock_external):
    """Test with mocked external dependency."""
    mock_external.return_value.method.return_value = "expected"
    # Test implementation
```

### Testing CLI Commands
```python
def test_command(mock_settings):
    """Test CLI command."""
    runner = CliRunner()
    mock_ctx = Mock()
    mock_ctx.obj = {"settings": mock_settings, "debug": False}

    result = runner.invoke(app, ["command", "args"], obj=mock_ctx.obj)
    assert result.exit_code == 0
```

## Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Modules**: 95%+ (config, core logic)

## Continuous Integration

Tests are designed to run in CI environments with:
- No external API dependencies (all mocked)
- Deterministic behavior
- Fast execution (< 30 seconds total)
- Clear failure reporting

## Debugging Tests

### Verbose Output
```bash
pytest -v -s
```

### Debug Specific Test
```bash
pytest tests/test_config.py::TestSettings::test_valid_settings_creation -v -s
```

### Print Coverage Report
```bash
pytest --cov=prunarr --cov-report=term-missing
```

### Generate HTML Coverage Report
```bash
pytest --cov=prunarr --cov-report=html
# Open htmlcov/index.html in browser
```