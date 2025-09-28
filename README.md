# PrunArr

A Python CLI tool to automatically prune movies and TV shows in Radarr and Sonarr based on watched status from Tautulli.

## Purpose

PrunArr helps you maintain clean media libraries by automatically removing content that has been watched for a configurable period. It integrates with:

- **Radarr/Sonarr**: For managing your media library
- **Tautulli**: For tracking what content has been watched and by whom

The tool uses a user tag system to track who requested specific content and only removes media after it has been watched by the original requester for a specified number of days.

## Features

- 🎬 **Movie Management**: List and remove watched movies from Radarr with file size tracking
- 📺 **TV Series Management**: List and remove watched TV shows from Sonarr with episode-level details
- 📊 **Watch History**: View detailed watch history from Tautulli with comprehensive filtering
- 👤 **User-based Tracking**: Uses tag system to track who requested what content
- ⏰ **Configurable Retention**: Set custom delay before removing watched content
- 🔧 **Flexible Configuration**: Support for YAML config files and environment variables
- 📏 **File Size Tracking**: Display file sizes for individual episodes, seasons, and entire series
- 📈 **Progress Tracking**: Show completion percentages and detailed episode statistics
- 🎯 **Advanced Filtering**: Filter by user, series title, season, watch status, and more
- 🔍 **Debug Logging**: Comprehensive logging system with timestamps and styled output
- 🚀 **Professional Architecture**: Fully documented codebase with type hints and robust error handling

## Installation

### Prerequisites

- Python 3.9 or higher
- Access to Radarr and/or Sonarr instances
- Access to a Tautulli instance
- API keys for both services

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

PrunArr supports multiple configuration methods:

### 1. YAML Configuration File

Create a `config.yaml` file:

```yaml
radarr_api_key: "your-radarr-api-key"
radarr_url: "http://localhost:7878"
tautulli_api_key: "your-tautulli-api-key"
tautulli_url: "http://localhost:8181"
days_before_removal: 60
```

### 2. Environment Variables

```bash
export RADARR_API_KEY="your-radarr-api-key"
export RADARR_URL="http://localhost:7878"
export TAUTULLI_API_KEY="your-tautulli-api-key"
export TAUTULLI_URL="http://localhost:8181"
export DAYS_BEFORE_REMOVAL=60
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
| `user_tag_regex` | Regex pattern for user tags | `^\d+ - (.+)$` |

## User Tag System

PrunArr uses a specific tag format in Radarr to track who requested content:

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
```

### Movie Management

```bash
# List all requested movies with file sizes
prunarr movies list

# List movies requested by specific user(s)
prunarr movies list --user john_doe --user jane_doe

# List only watched movies
prunarr movies list --watched

# Remove watched movies (after configured days)
prunarr movies remove
```

### TV Series Management

```bash
# List all requested series with episode counts and file sizes
prunarr series list

# List series for specific user
prunarr series list --username john_doe

# List fully watched series only
prunarr series list --watched

# List partially watched series
prunarr series list --partially-watched

# Filter by series title and season
prunarr series list --series "Breaking Bad" --season 1

# Get detailed series information with episode breakdown
prunarr series get 123

# Remove watched series
prunarr series remove
```

### Watch History

```bash
# Show watch history with filtering options
prunarr history show

# Filter by username
prunarr history show --username john_doe

# Filter by media type
prunarr history show --media-type movie

# Show only watched items
prunarr history show --watched-only

# Limit results
prunarr history show --limit 50
```

### Debug Mode

For troubleshooting and detailed information:

```bash
# Enable debug logging for any command
prunarr --debug series list

# Debug with config file
prunarr --debug --config config.yaml movies list
```

## How It Works

1. **Discovery**: PrunArr scans your Radarr/Sonarr libraries for downloaded content with user tags
2. **Matching**: It cross-references this content with Tautulli's watch history
3. **Filtering**: Only content watched by the original requester (from tag) is considered for removal
4. **Time Check**: Content is only removed after the configured `days_before_removal` period
5. **Cleanup**: Matching content is removed from your media server

## Examples

### List Movies for Specific User
```bash
prunarr movies list --user john_doe
```

### Remove Old Watched Content
```bash
# Remove movies watched more than 60 days ago (default)
prunarr movies remove

# Use custom config with different retention period
prunarr --config my-config.yaml movies remove
```

### Check Configuration
```bash
# This will validate your configuration
prunarr movies list
```

## Development

### Running Tests
```bash
python test.py
```

### Project Structure
```
prunarr/
├── prunarr/
│   ├── cli.py              # Main CLI interface with Typer
│   ├── main.py             # Application entry point
│   ├── prunarr.py          # Core logic and orchestration
│   ├── config.py           # Configuration handling with Pydantic
│   ├── logger.py           # Rich-styled logging system
│   ├── radarr.py           # Enhanced Radarr API client
│   ├── sonarr.py           # Enhanced Sonarr API client
│   ├── tautulli.py         # Advanced Tautulli API client
│   └── commands/           # Command implementations
│       ├── movies.py       # Movie management with file sizes
│       ├── series.py       # Series management with episode tracking
│       └── history.py      # Watch history analysis
├── pyproject.toml          # Project configuration
└── README.md
```

## Security Notes

- Keep your API keys secure and never commit them to version control
- The `config.yaml` file is excluded from git by default
- Consider using environment variables in production environments

## Troubleshooting

### Common Issues

1. **"No requested movies found"**: Check that your movies have the correct user tag format
2. **API connection errors**: Verify your URLs and API keys are correct
3. **Configuration errors**: Ensure all required settings are provided and valid

### Debug Mode

PrunArr includes comprehensive logging with timestamped, color-coded output:

```bash
# Enable debug logging for detailed troubleshooting
prunarr --debug movies list

# Debug output includes:
# - API call details
# - Configuration validation
# - Data processing steps
# - Error diagnostics
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request