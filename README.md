# PrunArr

A sophisticated Python CLI tool that automates intelligent cleanup of movies and TV shows in Radarr and Sonarr based on watched status from Tautulli. PrunArr provides advanced filtering, comprehensive filesize tracking, and user-based management with safety-first design.

## What is PrunArr?

PrunArr helps you maintain clean, organized media libraries by automatically removing content that has been watched for a configurable period. It provides deep integration with your media stack:

- **Radarr/Sonarr**: Advanced media library management with tag-based user tracking
- **Tautulli**: Comprehensive watch history analysis and user correlation
- **Rich CLI Interface**: Beautiful tables, progress indicators, and detailed feedback

**Key Features:**
- 🎯 **User-based Content Management**: Associates media with specific users through intelligent tag parsing
- 📊 **Advanced Watch Status Analysis**: Cross-references watch history across multiple platforms
- 💾 **Comprehensive Filesize Tracking**: Byte-accurate monitoring from individual episodes to entire series
- 🔍 **Multi-dimensional Filtering**: Filter by user, status, date, size, and custom criteria
- 🛡️ **Safety-first Design**: Multiple confirmation steps, dry-run modes, and detailed previews
- 🎨 **Rich Console Interface**: Color-coded tables, progress bars, and intuitive navigation
- ⚡ **Performance Caching**: Intelligent caching system minimizes API calls and improves response times
- 📝 **Configurable Logging**: Priority-based log levels (DEBUG, INFO, WARNING, ERROR) with detailed tracing
- 🔄 **JSON Output Support**: Machine-readable output for automation and scripting alongside human-friendly tables

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

PrunArr supports flexible configuration through YAML files or environment variables with comprehensive validation and detailed error reporting.

### Method 1: YAML Configuration File (Recommended)

Create a `config.yaml` file with your API credentials:

```yaml
# Required API Credentials
radarr_api_key: "your-radarr-api-key"
radarr_url: "https://radarr.yourdomain.com"
sonarr_api_key: "your-sonarr-api-key"
sonarr_url: "https://sonarr.yourdomain.com"
tautulli_api_key: "your-tautulli-api-key"
tautulli_url: "https://tautulli.yourdomain.com"

# Optional: Customize user tag pattern (default works for most setups)
user_tag_regex: "^\\d+ - (.+)$"

# Logging Configuration
log_level: ERROR  # DEBUG, INFO, WARNING, ERROR (default: ERROR)

# Cache Configuration (optional - improves performance)
cache_enabled: true
cache_dir: ~/.prunarr/cache
cache_max_size_mb: 100
cache_ttl_movies: 3600      # 1 hour
cache_ttl_series: 3600      # 1 hour
cache_ttl_history: 300      # 5 minutes

# Streaming Provider Configuration (optional - JustWatch integration)
streaming_enabled: false    # Set to true to enable streaming provider checks
streaming_locale: "en_US"   # Locale for JustWatch (language_COUNTRY format)
streaming_providers:        # List of provider technical names
  - "nfx"                   # Netflix
  - "amp"                   # Amazon Prime Video
  - "dnp"                   # Disney+
  - "hlu"                   # Hulu
cache_ttl_streaming: 86400  # 24 hours
```

### Method 2: Environment Variables

```bash
# Required API Settings
export RADARR_API_KEY="your-radarr-api-key"
export RADARR_URL="https://radarr.yourdomain.com"
export SONARR_API_KEY="your-sonarr-api-key"
export SONARR_URL="https://sonarr.yourdomain.com"
export TAUTULLI_API_KEY="your-tautulli-api-key"
export TAUTULLI_URL="https://tautulli.yourdomain.com"

# Optional: Custom user tag pattern
export USER_TAG_REGEX="^\\d+ - (.+)$"
```

### Configuration Settings

| Setting | Description | Example | Default |
|---------|-------------|---------|---------|
| `radarr_api_key` | API key from Radarr Settings → General | `6dbfa503ff6f45d2...` | Required |
| `radarr_url` | Radarr server URL (with protocol) | `https://radarr.example.com` | Required |
| `sonarr_api_key` | API key from Sonarr Settings → General | `bb54fb4decab4503...` | Required |
| `sonarr_url` | Sonarr server URL (with protocol) | `https://sonarr.example.com` | Required |
| `tautulli_api_key` | API key from Tautulli Settings → Web Interface | `a5aa5211c0a04e21...` | Required |
| `tautulli_url` | Tautulli server URL (with protocol) | `https://tautulli.example.com` | Required |
| `user_tag_regex` | Regex for extracting usernames from tags | `^\\d+ - (.+)$` | `^\\d+ - (.+)$` |
| `log_level` | Minimum log level to display | `INFO` | `ERROR` |
| `cache_enabled` | Enable performance caching | `true` | `true` |
| `cache_dir` | Cache storage directory | `~/.prunarr/cache` | `~/.prunarr/cache` |
| `cache_max_size_mb` | Maximum cache size in MB | `100` | `100` |
| `streaming_enabled` | Enable JustWatch streaming provider checks | `true` | `false` |
| `streaming_locale` | Locale for streaming availability (language_COUNTRY) | `en_US` | `en_US` |
| `streaming_providers` | List of provider technical names | `["nfx", "amp"]` | `[]` |
| `cache_ttl_streaming` | Streaming data cache TTL (seconds) | `86400` | `86400` |

### Configuration Priority

PrunArr loads configuration in the following order (later sources override earlier ones):
1. **Default values** (where applicable)
2. **Environment variables**
3. **YAML configuration file** (via `--config` flag)

### Finding Your API Keys

#### Radarr/Sonarr API Keys
1. Open your Radarr/Sonarr web interface
2. Go to **Settings** → **General**
3. Show **Advanced Settings**
4. Copy the **API Key** from the Security section

#### Tautulli API Key
1. Open your Tautulli web interface
2. Go to **Settings** → **Web Interface**
3. Copy the **API Key** from the API section

## Tag System

PrunArr uses tags in Radarr/Sonarr for both user tracking and organizational filtering:

### User Tags

**Tag Format**: `"userid - username"`

Example: `"123 - john_doe"`

- Only movies/shows with tags matching this pattern are processed for removal
- The username must match a user in Tautulli
- Content is only removed when watched by the user specified in the tag

### Organizational Tags

PrunArr also displays and filters by non-user tags (tags that don't match the user tag pattern):

**Examples**: `"4K"`, `"Action"`, `"Kids"`, `"HDR"`, `"Documentary"`

- **Display**: Non-user tags appear in the Tags column of list commands (max 3 shown, "+N more" for additional)
- **Filtering**: Use `--tag` to include only items with specific tags, or `--exclude-tag` to exclude items
- **Case-Insensitive**: Tag matching is case-insensitive ("4k" matches "4K")
- **Multiple Tags**: Specify `--tag` or `--exclude-tag` multiple times
- **Match Modes**: Use `--tag-match-all` to require ALL specified tags instead of ANY

## Streaming Provider Integration (JustWatch)

PrunArr integrates with JustWatch to check streaming availability across your configured providers. This allows you to filter and manage content based on whether it's available on your streaming services.

### Configuration

Enable streaming provider checks in your `config.yaml`:

```yaml
streaming_enabled: true
streaming_locale: "en_US"  # Your region (language_COUNTRY)
streaming_providers:
  - "nfx"                  # Netflix
  - "amp"                  # Amazon Prime Video
  - "dnp"                  # Disney+
  - "hlu"                  # Hulu
```

**Common Provider Technical Names:**
- `nfx` - Netflix
- `amp` - Amazon Prime Video (Amazon)
- `dnp` - Disney+
- `hlu` - Hulu
- `hbm` - HBO Max
- `atp` - Apple TV+
- `pmp` - Paramount+
- `sho` - Showtime

**Note:** Use `prunarr providers list` to see all available provider technical names for your locale.

### Filtering Options

**`--on-streaming`**: Show/remove ONLY content available on your configured providers
- Use case: Find movies you're storing that you can already stream

**`--not-on-streaming`**: Show/remove ONLY content NOT available on streaming
- Use case: Focus on your unique collection not available elsewhere

### Example Use Cases

```bash
# Find large files you're storing that are available on streaming
prunarr movies list --on-streaming --min-filesize 5GB

# Clean up watched movies available on streaming (you can stream them)
prunarr movies remove --on-streaming --days-watched 30

# Keep unique content longer (not on streaming)
prunarr movies remove --not-on-streaming --days-watched 180

# See what unique content you have
prunarr movies list --not-on-streaming
```

### Caching

Streaming availability data is cached for 24 hours by default to minimize API calls. Cache TTL can be configured with `cache_ttl_streaming` in seconds.

## Usage

PrunArr provides three main command categories with extensive filtering and management capabilities.

### Global Options

```bash
# Show comprehensive help
prunarr --help

# Use custom configuration file
prunarr --config /path/to/config.yaml <command>

# Enable detailed debug logging (overrides log_level)
prunarr --debug <command>

# Get JSON output for automation
prunarr movies list --output json
prunarr series get "Breaking Bad" --output json
prunarr cache status --output json
```

### 🎬 Movie Management (`prunarr movies`)

#### List Movies with Advanced Filtering

```bash
# List all movies with watch status and file sizes
prunarr movies list

# Filter by specific user
prunarr movies list --username "john_doe"

# Show only watched movies
prunarr movies list --watched

# Show only unwatched movies
prunarr movies list --unwatched

# Find movies watched by someone other than the requester
prunarr movies list --watched-by-other

# Find movies ready for cleanup (watched 30+ days ago)
prunarr movies list --days-watched 30

# Filter by minimum file size
prunarr movies list --min-filesize "2GB"

# Exclude movies without user tags
prunarr movies list --exclude-untagged

# Filter by organizational tags
prunarr movies list --tag "4K"                          # Show only 4K movies
prunarr movies list --tag "Action" --tag "Sci-Fi"      # Show Action OR Sci-Fi movies
prunarr movies list --tag "4K" --tag "HDR" --tag-match-all  # Show movies with BOTH 4K AND HDR
prunarr movies list --exclude-tag "Kids"               # Exclude kids movies
prunarr movies list --tag "Action" --exclude-tag "Kids" # Action movies, but not kids content

# Sort by different criteria
prunarr movies list --sort-by filesize --desc
prunarr movies list --sort-by watched_date --limit 20
prunarr movies list --sort-by days_watched

# Combine multiple filters
prunarr movies list --username "alice" --watched --min-filesize "1GB" --days-watched 60

# Streaming provider filtering (requires streaming_enabled=true in config)
prunarr movies list --on-streaming                    # Show ONLY movies on your streaming services
prunarr movies list --not-on-streaming                # Show ONLY movies NOT on streaming
prunarr movies list --on-streaming --min-filesize 5GB # Find large streamable files

# Get JSON output for scripts/automation
prunarr movies list --output json
prunarr movies list --username "alice" --output json > movies.json
```

#### Remove Movies Safely

```bash
# Preview what would be removed (ALWAYS start with this)
prunarr movies remove --dry-run

# Remove movies watched 60+ days ago (default behavior)
prunarr movies remove

# Custom retention period
prunarr movies remove --days-watched 90

# Remove for specific user
prunarr movies remove --username "john_doe" --days-watched 30

# Remove large files first (sorted by size)
prunarr movies remove --sort-by filesize --limit 10

# Skip confirmation prompts (for automation)
prunarr movies remove --force

# Advanced filtering in removal
prunarr movies remove --min-filesize "5GB" --days-watched 180 --dry-run

# Streaming provider-based removal (requires streaming_enabled=true in config)
prunarr movies remove --on-streaming --days-watched 30      # Remove watched movies you can stream
prunarr movies remove --not-on-streaming --days-watched 180 # Keep unique content longer

# Tag-based removal targeting
prunarr movies remove --tag "Kids" --days-watched 14        # Cleanup kids movies after 2 weeks
prunarr movies remove --exclude-tag "Favorites" --days-watched 30  # Keep favorites longer
prunarr movies remove --tag "4K" --min-filesize "10GB"     # Target large 4K files
```

### 📺 TV Series Management (`prunarr series`)

#### List Series with Comprehensive Details

```bash
# List all series with watch progress
prunarr series list

# Filter by user and watch status
prunarr series list --username "alice" --watched
prunarr series list --partially-watched
prunarr series list --unwatched

# Filter by series name (partial matching)
prunarr series list --series "breaking bad"

# Focus on specific season
prunarr series list --series "the office" --season 2

# Filter by organizational tags
prunarr series list --tag "4K"                          # Show only 4K series
prunarr series list --tag "Drama" --tag "Sci-Fi"       # Show Drama OR Sci-Fi series
prunarr series list --tag "4K" --tag "HDR" --tag-match-all  # Show series with BOTH 4K AND HDR
prunarr series list --exclude-tag "Kids"               # Exclude kids series
prunarr series list --tag "Drama" --exclude-tag "Reality" # Drama series, but not reality TV

# Limit results for quick overview
prunarr series list --limit 10

# Get JSON output for automation
prunarr series list --output json
prunarr series list --watched --output json > watched-series.json
```

#### Get Detailed Series Information

```bash
# Get comprehensive episode details by title
prunarr series get "Breaking Bad"

# Get details by Sonarr ID
prunarr series get 123

# Focus on specific season
prunarr series get "The Office" --season 2

# Show only unwatched episodes
prunarr series get "Stranger Things" --unwatched-only

# Show only watched episodes
prunarr series get "Game of Thrones" --watched-only

# Show watch info for all users (not just requester)
prunarr series get "Westworld" --all-watchers

# Get JSON output with complete episode data
prunarr series get "Breaking Bad" --output json
prunarr series get 123 --output json > series-details.json
```

#### Remove Series with Safety Controls

```bash
# Preview series removal (dry run)
prunarr series remove --dry-run

# Remove fully watched series (default: 60 days)
prunarr series remove

# Custom retention period
prunarr series remove --days-watched 45

# Remove for specific user
prunarr series remove --username "john_doe"

# Filter by specific series
prunarr series remove --series "completed show name"

# Skip confirmation prompts
prunarr series remove --yes

# Tag-based removal targeting
prunarr series remove --tag "Kids" --days-watched 14        # Cleanup kids shows after 2 weeks
prunarr series remove --exclude-tag "Favorites" --days-watched 60  # Keep favorites longer
prunarr series remove --tag "Reality" --days-watched 30     # Quick cleanup of reality TV

# Planned: Season-level removal
prunarr series remove --mode season --days-watched 90
```

### 📊 Watch History Analysis (`prunarr history`)

#### List Watch History with Filtering

```bash
# Show recent watch history (default: 100 items)
prunarr history list

# Show only fully watched items
prunarr history list --watched

# Filter by specific user
prunarr history list --username "alice"

# Filter by media type
prunarr history list --media-type movie
prunarr history list --media-type episode

# Combine filters
prunarr history list --username "john" --media-type movie --watched

# Custom result limits
prunarr history list --limit 50

# Get all available history records
prunarr history list --all

# JSON output for analysis
prunarr history list --output json
prunarr history list --username "alice" --output json > user-history.json
```

#### Get Detailed History Information

```bash
# Get comprehensive details for specific history record
prunarr history get 2792

# Use history ID from the list command output
prunarr history list --limit 5
prunarr history get 12345

# JSON output with all metadata
prunarr history get 2792 --output json
```

### 🎬 Streaming Provider Management (`prunarr providers`)

#### List Available Providers

```bash
# List all FLATRATE providers for your locale
prunarr providers list

# List providers for specific locale
prunarr providers list --locale en_GB
prunarr providers list --locale de_DE

# Get JSON output for scripting
prunarr providers list --output json
prunarr providers list --output json | jq '.[] | select(.technical_name == "nfx")'

# Find specific provider technical name
prunarr providers list | grep -i netflix
prunarr providers list | grep -i disney
```

#### Check Content Availability

```bash
# Check if a movie is available on streaming
prunarr providers check "The Matrix"

# Check with specific year for better matching
prunarr providers check "The Matrix" --year 1999

# Check TV series availability
prunarr providers check "Breaking Bad" --type series
prunarr providers check "Stranger Things" --type show

# Check in different locale
prunarr providers check "Dark" --type series --locale de_DE

# Get JSON output with complete availability data
prunarr providers check "Inception" --output json
prunarr providers check "The Office" --type series --output json > availability.json
```

### 💾 Cache Management (`prunarr cache`)

#### Initialize and Manage Cache

```bash
# Initialize cache for improved performance
prunarr cache init

# Full initialization (includes all episodes - slower but complete)
prunarr cache init --full

# Check cache status and statistics
prunarr cache status

# Get cache stats as JSON
prunarr cache status --output json

# Clear specific cache types
prunarr cache clear --type movies
prunarr cache clear --type series
prunarr cache clear --type history

# Clear all cache
prunarr cache clear --type all

# Refresh cache (clear and refetch)
prunarr cache refresh --type history
prunarr cache refresh --type all
```

### 🔧 Advanced Usage Patterns

#### Maintenance Workflows

```bash
# Weekly cleanup workflow
prunarr movies remove --days-watched 60 --dry-run
prunarr movies remove --days-watched 60

prunarr series remove --days-watched 90 --dry-run
prunarr series remove --days-watched 90

# User-specific cleanup
prunarr movies list --username "departed_user" --watched
prunarr movies remove --username "departed_user" --days-watched 7 --force

# Large file cleanup
prunarr movies list --min-filesize "10GB" --sort-by filesize --desc
prunarr movies remove --min-filesize "5GB" --days-watched 30
```

#### Debug and Troubleshooting

```bash
# Enable debug mode for detailed logging
prunarr --debug movies list --limit 5
prunarr --debug series get "problematic series"
prunarr --debug history list --username "user"

# Configuration testing
prunarr --debug --config test-config.yaml movies list --limit 1

# Check cache operations
prunarr --debug cache init
prunarr --debug cache status

# Set log level in config for persistent logging
# In config.yaml: log_level: INFO
prunarr movies list  # Will show INFO level logs
```

#### Automation-friendly Commands

```bash
# Automated cleanup (use with cron/systemd timers)
prunarr --config /etc/prunarr/config.yaml movies remove --days-watched 90 --force
prunarr --config /etc/prunarr/config.yaml series remove --days-watched 120 --yes

# Safe automated preview (for monitoring)
prunarr movies remove --dry-run > /tmp/prunarr-preview.log

# JSON output for integration with other tools
prunarr --config /etc/prunarr/config.yaml movies list --output json | jq '.[] | select(.days_since_watched > 90)'
prunarr series list --watched --output json | process-data.py

# Initialize cache before automated runs
prunarr --config /etc/prunarr/config.yaml cache init
```

### 🎨 Rich Console Features

PrunArr provides beautiful, informative output:

- **Color-coded Status**: 🟢 Watched, 🟡 Partial, 🔴 Unwatched
- **File Size Display**: Human-readable sizes (MB, GB, TB)
- **Progress Indicators**: Real-time operation feedback
- **Detailed Tables**: Comprehensive information at a glance
- **Smart Formatting**: Consistent, easy-to-read output
- **Dual Output Modes**: Human-friendly tables or machine-readable JSON
- **Configurable Logging**: Control verbosity with log levels (ERROR, WARNING, INFO, DEBUG)

### 🔍 Filter Combinations

PrunArr supports powerful filter combinations:

```bash
# Complex movie filtering
prunarr movies list \
  --username "power_user" \
  --watched \
  --days-watched 30 \
  --min-filesize "2GB" \
  --sort-by days_watched \
  --desc \
  --limit 20

# Advanced series analysis
prunarr series list \
  --partially-watched \
  --username "binge_watcher" \
  --limit 10

# Tag-based filtering combinations
prunarr movies list \
  --tag "4K" \
  --tag "HDR" \
  --tag-match-all \
  --min-filesize "10GB" \
  --watched \
  --days-watched 90

prunarr series list \
  --tag "Drama" \
  --exclude-tag "Reality" \
  --exclude-tag "Kids" \
  --watched

# Targeted cleanup operations
prunarr movies remove \
  --days-watched 180 \
  --min-filesize "8GB" \
  --sort-by filesize \
  --limit 5 \
  --dry-run
```

## How It Works

PrunArr uses a sophisticated multi-step process to safely and intelligently manage your media library:

### 🔍 Discovery & Analysis
1. **Media Library Scanning**: Connects to Radarr/Sonarr APIs to discover all movies and TV series
2. **User Tag Parsing**: Extracts usernames from tags using configurable regex patterns
3. **Watch History Correlation**: Cross-references media with Tautulli watch history using TVDB/IMDB IDs
4. **File Size Aggregation**: Calculates comprehensive file size data from individual episodes to series totals

### 🎯 Intelligent Filtering
1. **User Verification**: Ensures only the original requester can trigger content removal
2. **Watch Status Analysis**: Determines completion status (fully watched, partially watched, unwatched)
3. **Time-based Logic**: Applies configurable retention periods based on last watch date
4. **Multi-dimensional Filtering**: Supports complex filtering by user, status, size, date, and custom criteria

### 🛡️ Safety & Confirmation
1. **Preview Mode**: Dry-run capabilities show exactly what would be affected
2. **Progressive Confirmation**: Multiple confirmation steps with detailed summaries
3. **Filter Transparency**: Clear indication of all applied filters and criteria
4. **Graceful Error Handling**: Continues processing when individual items fail

### 🎬 Smart Media Management
- **Episode-level Tracking**: Individual episode watch status and file sizes
- **Season Aggregation**: Season-level statistics and management capabilities
- **Series Intelligence**: Understands series completion and partial watching patterns
- **Cross-platform Correlation**: Links media across Radarr, Sonarr, and Tautulli seamlessly

## ✨ Key Features

### 🎯 Advanced Filtering System
- **User-based Filtering**: Filter content by specific requesting users
- **Watch Status Types**: Watched, unwatched, partially watched, watched by others
- **Time-based Criteria**: Days since watched, addition date, custom time ranges
- **File Size Filtering**: Minimum/maximum file size requirements with flexible units
- **Tag-based Filtering**: Include/exclude content by organizational tags with ANY or ALL matching modes
- **Multi-dimensional Combinations**: Combine any filters for precise control

### 📊 Comprehensive Data Analysis
- **Rich Watch Statistics**: Episode counts, completion percentages, last watch dates
- **File Size Tracking**: Individual episode sizes up to series/movie totals
- **User Activity Correlation**: Cross-reference requesting users with actual viewers
- **Historical Analysis**: Deep dive into watch history with detailed metadata

### 🎨 Beautiful Console Interface
- **Color-coded Status Indicators**: Instant visual feedback on media status
- **Rich Tables**: Properly formatted tables with comprehensive information
- **Progress Tracking**: Real-time feedback during operations
- **Smart Formatting**: Human-readable file sizes, dates, and durations

### 🛡️ Safety-first Design
- **Dry Run Modes**: Preview all operations before making changes
- **Multiple Confirmation Steps**: Progressive confirmations for destructive operations
- **User Tag Validation**: Only process content with proper user associations
- **Detailed Operation Logs**: Comprehensive logging with debug capabilities

### 🔧 Advanced Management Capabilities
- **Flexible Sorting**: Sort by title, date, file size, watch date, or days watched
- **Smart Pagination**: Limit results for manageable output
- **Series Detail Views**: Episode-level information with season aggregation
- **History Analysis**: Deep dive into Tautulli watch records

### 🚀 Automation Ready
- **Configuration File Support**: YAML configuration for repeatable setups
- **Environment Variable Support**: Flexible deployment options
- **Force Modes**: Skip confirmations for automated workflows
- **Exit Codes**: Proper exit codes for scripting and monitoring
- **JSON Output**: Machine-readable output for all list/get/status commands
- **Scriptable**: Easy integration with automation tools and workflows

### ⚡ Performance & Caching
- **Intelligent Caching**: Disk-based cache minimizes API calls
- **Configurable TTLs**: Separate TTL settings per data type
- **Cache Management**: Init, status, clear, and refresh operations
- **Size Limits**: Automatic cleanup when cache exceeds size limits
- **Cache Statistics**: Hit/miss tracking and performance metrics

### 📝 Logging & Debugging
- **Configurable Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Debug Mode**: `--debug` flag for comprehensive troubleshooting
- **API Call Tracing**: Detailed logging of all API interactions
- **Cache Operation Logging**: Visibility into cache hits and misses
- **Rich Formatting**: Color-coded, timestamped log messages

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