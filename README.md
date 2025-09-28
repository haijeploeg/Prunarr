# PrunArr

A Python CLI tool to automatically manage and cleanup movies and TV shows in Radarr and Sonarr based on watched status from Tautulli.

## What is PrunArr?

PrunArr helps you maintain clean media libraries by automatically removing content that has been watched for a configurable period. It integrates with:

- **Radarr/Sonarr**: For managing your media library
- **Tautulli**: For tracking what content has been watched and by whom

The tool uses a user tag system to track who requested specific content and only removes media after it has been watched by the original requester.

## Installation

### Prerequisites

- Python 3.9 or higher
- Access to Radarr and/or Sonarr instances
- Access to a Tautulli instance
- API keys for all services

### Install from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd prunarr
```

2. Create a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Configuration

### Method 1: YAML Configuration File

Create a `config.yaml` file:

```yaml
radarr_api_key: "your-radarr-api-key"
radarr_url: "http://localhost:7878"
sonarr_api_key: "your-sonarr-api-key"
sonarr_url: "http://localhost:8989"
tautulli_api_key: "your-tautulli-api-key"
tautulli_url: "http://localhost:8181"
user_tag_regex: "^\\d+ - (.+)$"
```

### Method 2: Environment Variables

```bash
export RADARR_API_KEY="your-radarr-api-key"
export RADARR_URL="http://localhost:7878"
export SONARR_API_KEY="your-sonarr-api-key"
export SONARR_URL="http://localhost:8989"
export TAUTULLI_API_KEY="your-tautulli-api-key"
export TAUTULLI_URL="http://localhost:8181"
export USER_TAG_REGEX="^\\d+ - (.+)$"
```

### Required Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `radarr_api_key` | API key for Radarr | Required |
| `radarr_url` | Radarr server URL | Required |
| `sonarr_api_key` | API key for Sonarr | Required |
| `sonarr_url` | Sonarr server URL | Required |
| `tautulli_api_key` | API key for Tautulli | Required |
| `tautulli_url` | Tautulli server URL | Required |
| `user_tag_regex` | Regex pattern for user tags | `^\\d+ - (.+)$` |

## User Tag System

PrunArr uses a specific tag format in Radarr/Sonarr to track who requested content:

**Tag Format**: `"userid - username"`

Example: `"123 - john_doe"`

- Only movies/shows with tags matching this pattern are processed
- The username must match a user in Tautulli
- Content is only removed when watched by the user specified in the tag

## Usage

### Basic Commands

```bash
# Show help
prunarr --help

# Use custom config file
prunarr --config /path/to/config.yaml <command>

# Enable debug logging
prunarr --debug <command>
```

### Movie Management

```bash
# List all movies with user tags
prunarr movies list

# List movies for specific user
prunarr movies list --username john_doe

# List only watched movies
prunarr movies list --watched

# Remove watched movies (default: 60 days after being watched)
prunarr movies remove

# Remove movies watched more than 30 days ago
prunarr movies remove --days-watched 30

# Preview what would be removed (dry run)
prunarr movies remove --dry-run
```

### TV Series Management

```bash
# List all series with user tags
prunarr series list

# List series for specific user
prunarr series list --username john_doe

# Get detailed information about a series
prunarr series get "Breaking Bad"

# Remove watched series
prunarr series remove

# Remove with custom retention period
prunarr series remove --days-watched 45
```

### Watch History

```bash
# Show watch history
prunarr history list

# Filter by username
prunarr history list --username john_doe

# Show only watched items
prunarr history list --watched-only

# Get details for specific history item
prunarr history get 12345
```

### Debug Mode

For troubleshooting:

```bash
# Enable debug logging for any command
prunarr --debug movies list

# Debug with config file
prunarr --debug --config config.yaml series list
```

Debug mode provides:
- Detailed API call information
- Configuration validation details
- Processing steps and error diagnostics
- Timestamped, color-coded output

## How It Works

1. **Discovery**: PrunArr scans your Radarr/Sonarr libraries for content with user tags
2. **Matching**: Cross-references content with Tautulli's watch history
3. **Filtering**: Only content watched by the original requester (from tag) is considered
4. **Time Check**: Content is only removed after the specified days since being watched
5. **Cleanup**: Matching content is removed from your media server

## Contributing

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=prunarr --cov-report=term-missing
```

## Security Notes

- Keep your API keys secure and never commit them to version control
- The `config.yaml` file should be excluded from git
- Consider using environment variables in production environments

## Troubleshooting

### Common Issues

1. **"Configuration validation failed"**: Ensure all required API keys and URLs are provided
2. **"No movies found"**: Check that your movies have the correct user tag format
3. **API connection errors**: Verify URLs and API keys are correct

### Getting Help

Use debug mode for detailed troubleshooting:

```bash
prunarr --debug movies list
```

This will show detailed information about configuration loading, API calls, and any errors encountered.