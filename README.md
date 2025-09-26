# CleanArr

A Python CLI tool to automatically cleanup movies and TV shows in Radarr and Sonarr based on watched status from Tautulli.

## Purpose

CleanArr helps you maintain clean media libraries by automatically removing content that has been watched for a configurable period. It integrates with:

- **Radarr/Sonarr**: For managing your media library
- **Tautulli**: For tracking what content has been watched and by whom

The tool uses a user tag system to track who requested specific content and only removes media after it has been watched by the original requester for a specified number of days.

## Features

- 🎬 **Movie Management**: List and remove watched movies from Radarr
- 📺 **TV Series Management**: List and remove watched TV shows from Sonarr
- 📊 **Watch History**: View detailed watch history from Tautulli
- 👤 **User-based Tracking**: Uses tag system to track who requested what content
- ⏰ **Configurable Retention**: Set custom delay before removing watched content
- 🔧 **Flexible Configuration**: Support for YAML config files and environment variables

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
cd cleanarr
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

CleanArr supports multiple configuration methods:

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
| `tautulli_api_key` | API key for Tautulli | Required |
| `tautulli_url` | Tautulli server URL | Required |
| `days_before_removal` | Days to wait after watching before removal | 60 |

## User Tag System

CleanArr uses a specific tag format in Radarr to track who requested content:

**Tag Format**: `"userid - username"`

Example: `"123 - john_doe"`

- Only movies/shows with tags matching this pattern are processed
- The username must match a user in Tautulli
- Content is only removed when watched by the user specified in the tag

## Usage

### Basic Commands

```bash
# Show help
cleanarr --help

# Use custom config file
cleanarr --config /path/to/config.yaml <command>
```

### Movie Management

```bash
# List all requested movies
cleanarr movies list

# List movies requested by specific user(s)
cleanarr movies list --user john_doe --user jane_doe

# Remove watched movies (after configured days)
cleanarr movies remove
```

### TV Series Management

```bash
# List all requested series
cleanarr series list

# Remove watched series
cleanarr series remove
```

### Watch History

```bash
# Show watch history
cleanarr history show
```

## How It Works

1. **Discovery**: CleanArr scans your Radarr/Sonarr libraries for downloaded content with user tags
2. **Matching**: It cross-references this content with Tautulli's watch history
3. **Filtering**: Only content watched by the original requester (from tag) is considered for removal
4. **Time Check**: Content is only removed after the configured `days_before_removal` period
5. **Cleanup**: Matching content is removed from your media server

## Examples

### List Movies for Specific User
```bash
cleanarr movies list --user john_doe
```

### Remove Old Watched Content
```bash
# Remove movies watched more than 60 days ago (default)
cleanarr movies remove

# Use custom config with different retention period
cleanarr --config my-config.yaml movies remove
```

### Check Configuration
```bash
# This will validate your configuration
cleanarr movies list
```

## Development

### Running Tests
```bash
python test.py
```

### Project Structure
```
cleanarr/
├── cleanarr/
│   ├── cli.py              # Main CLI interface
│   ├── cleanarr.py         # Core logic
│   ├── config.py           # Configuration handling
│   ├── radarr.py           # Radarr API client
│   ├── tautulli.py         # Tautulli API client
│   └── commands/           # Command implementations
│       ├── movies.py
│       ├── series.py
│       └── history.py
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

For troubleshooting, you can run commands with increased verbosity or check the configuration:

```bash
# Test connection by listing content
cleanarr movies list
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request