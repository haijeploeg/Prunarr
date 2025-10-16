# PrunArr Command Reference

Complete reference for all PrunArr commands with examples and options.

## Table of Contents

- [Movies Commands](#movies-commands)
- [Series Commands](#series-commands)
- [History Commands](#history-commands)
- [Streaming Provider Commands](#streaming-provider-commands)
- [Cache Commands](#cache-commands)
- [Global Options](#global-options)

---

## Movies Commands

### `prunarr movies list`

List all movies with watch status and filtering.

**Usage:**
```bash
prunarr movies list [OPTIONS]
```

**Examples:**

```bash
# Basic listing
prunarr movies list

# Filter by watch status
prunarr movies list --watched               # Only watched movies
prunarr movies list --unwatched             # Only unwatched movies
prunarr movies list --watched-by-other      # Watched by someone else

# Filter by user
prunarr movies list --username "alice"

# Filter by size
prunarr movies list --min-filesize "2GB"

# Filter by time
prunarr movies list --days-watched 30       # Watched 30+ days ago

# Filter by tags
prunarr movies list --tag "4K"              # Has 4K tag
prunarr movies list --exclude-tag "Kids"    # Exclude kids content

# Streaming filters
prunarr movies list --on-streaming          # Available on streaming
prunarr movies list --not-on-streaming      # NOT available on streaming

# Sorting and limiting
prunarr movies list --sort-by filesize --desc --limit 20
prunarr movies list --sort-by days_watched --limit 10

# JSON output
prunarr movies list --output json
```

**Options:**
- `--watched` / `-w` - Show only watched movies
- `--unwatched` - Show only unwatched movies
- `--watched-by-other` - Show movies watched by someone other than requester
- `--username` / `-u` - Filter by specific username
- `--days-watched` / `-d` - Show movies watched N+ days ago
- `--min-filesize` - Minimum file size (e.g., "2GB", "500MB")
- `--tag` - Include only movies with this tag (can use multiple times)
- `--exclude-tag` - Exclude movies with this tag (can use multiple times)
- `--tag-match-all` - Require ALL specified tags instead of ANY
- `--on-streaming` - Show only movies available on streaming
- `--not-on-streaming` - Show only movies NOT available on streaming
- `--sort-by` / `-s` - Sort by: title, date, filesize, watched_date, days_watched
- `--desc` - Sort in descending order
- `--limit` / `-l` - Limit number of results
- `--output` / `-o` - Output format: table or json

---

### `prunarr movies remove`

Remove watched movies with safety features.

**Usage:**
```bash
prunarr movies remove [OPTIONS]
```

**Examples:**

```bash
# ALWAYS test with dry-run first!
prunarr movies remove --dry-run

# Basic removal (60+ days old by default)
prunarr movies remove

# Custom retention period
prunarr movies remove --days-watched 90

# All the list filters work here too
prunarr movies remove --username "john" --days-watched 30
prunarr movies remove --min-filesize "5GB" --days-watched 60
prunarr movies remove --tag "Kids" --days-watched 14
prunarr movies remove --on-streaming --days-watched 30

# Skip confirmations (for automation - use carefully!)
prunarr movies remove --force
```

**Options:**
- `--dry-run` - Preview what would be removed without deleting
- `--days-watched` / `-d` - Remove movies watched N+ days ago (default: 60)
- `--force` / `-f` - Skip confirmation prompts
- All filtering options from `movies list` command

---

## Series Commands

### `prunarr series list`

List TV series with watch progress.

**Usage:**
```bash
prunarr series list [OPTIONS]
```

**Examples:**

```bash
# Basic listing
prunarr series list

# Filter by watch status
prunarr series list --watched               # Fully watched series
prunarr series list --partially-watched     # Partially watched
prunarr series list --unwatched             # Unwatched series

# Filter by user
prunarr series list --username "bob"

# Filter by series name
prunarr series list --series "Breaking Bad"

# Filter by season
prunarr series list --season 2

# Filter by tags
prunarr series list --tag "Drama"
prunarr series list --exclude-tag "Reality"

# Limit results
prunarr series list --limit 20

# JSON output
prunarr series list --output json
```

**Options:**
- `--watched` / `-w` - Show only fully watched series
- `--partially-watched` / `-p` - Show only partially watched series
- `--unwatched` - Show only unwatched series
- `--username` / `-u` - Filter by specific username
- `--series` / `-s` - Filter by series title (partial matching)
- `--season` - Filter by specific season number
- `--tag` - Include only series with this tag (can use multiple times)
- `--exclude-tag` - Exclude series with this tag (can use multiple times)
- `--tag-match-all` - Require ALL specified tags instead of ANY
- `--include-untagged` - Include series without user tags
- `--limit` / `-l` - Limit number of results
- `--output` / `-o` - Output format: table or json

---

### `prunarr series get`

Get detailed information about a specific series.

**Usage:**
```bash
prunarr series get <identifier> [OPTIONS]
```

**Examples:**

```bash
# By title (fuzzy matching)
prunarr series get "Breaking Bad"

# By Sonarr ID
prunarr series get 123

# Filter to specific season
prunarr series get "The Office" --season 2

# Show only watched episodes
prunarr series get "Stranger Things" --watched-only

# Show only unwatched episodes
prunarr series get "Game of Thrones" --unwatched-only

# Show watch info for all users
prunarr series get "Westworld" --all-watchers

# JSON output
prunarr series get "Breaking Bad" --output json
```

**Options:**
- `--season` / `-s` - Show only specific season
- `--watched-only` / `-w` - Show only watched episodes
- `--unwatched-only` / `-u` - Show only unwatched episodes
- `--all-watchers` / `-a` - Show watch info for all users
- `--output` / `-o` - Output format: table or json

---

### `prunarr series remove`

Remove fully watched series.

**Usage:**
```bash
prunarr series remove [OPTIONS]
```

**Examples:**

```bash
# ALWAYS test with dry-run first!
prunarr series remove --dry-run

# Basic removal (60+ days old by default)
prunarr series remove

# Custom retention period
prunarr series remove --days-watched 90

# User-specific removal
prunarr series remove --username "alice"

# Filter by series name
prunarr series remove --series "completed show"

# Filter by tags
prunarr series remove --tag "Kids" --days-watched 14

# Skip confirmations
prunarr series remove --yes
```

**Options:**
- `--dry-run` - Preview what would be removed without deleting
- `--days-watched` / `-d` - Remove series watched N+ days ago (default: 60)
- `--yes` / `-y` - Skip confirmation prompts
- All filtering options from `series list` command

---

## History Commands

### `prunarr history list`

View Tautulli watch history.

**Usage:**
```bash
prunarr history list [OPTIONS]
```

**Examples:**

```bash
# Recent history (default: 100 items)
prunarr history list

# Filter by user
prunarr history list --username "alice"

# Filter by media type
prunarr history list --media-type movie
prunarr history list --media-type episode

# Show only fully watched
prunarr history list --watched

# Custom limits
prunarr history list --limit 50
prunarr history list --all                  # Get all records

# JSON output
prunarr history list --output json
```

**Options:**
- `--watched` / `-w` - Show only fully watched items
- `--username` / `-u` - Filter by specific username
- `--media-type` / `-m` - Filter by media type: movie, show, episode
- `--limit` / `-l` - Limit number of results (default: 100)
- `--all` / `-a` - Fetch all available records
- `--output` / `-o` - Output format: table or json

---

### `prunarr history get`

Get detailed information about a specific history record.

**Usage:**
```bash
prunarr history get <history_id> [OPTIONS]
```

**Examples:**

```bash
# By history ID (from list command)
prunarr history get 2792

# JSON output
prunarr history get 2792 --output json
```

**Options:**
- `--output` / `-o` - Output format: table or json

---

## Streaming Provider Commands

### `prunarr providers list`

List available streaming providers for your region.

**Usage:**
```bash
prunarr providers list [OPTIONS]
```

**Examples:**

```bash
# List providers for your configured locale
prunarr providers list

# List for specific locale
prunarr providers list --locale en_GB
prunarr providers list --locale de_DE

# JSON output
prunarr providers list --output json

# Find specific provider
prunarr providers list | grep -i netflix
```

**Options:**
- `--locale` / `-l` - Override locale (e.g., en_US, en_GB, de_DE)
- `--output` / `-o` - Output format: table or json

---

### `prunarr providers check`

Check if specific content is available on streaming.

**Usage:**
```bash
prunarr providers check <title> [OPTIONS]
```

**Examples:**

```bash
# Check a movie
prunarr providers check "The Matrix"

# Check with year for better matching
prunarr providers check "The Matrix" --year 1999

# Check TV series
prunarr providers check "Breaking Bad" --type series

# Different locale
prunarr providers check "Dark" --type series --locale de_DE

# JSON output
prunarr providers check "Inception" --output json
```

**Options:**
- `--type` / `-t` - Media type: movie or series (default: movie)
- `--year` / `-y` - Release year for better matching
- `--locale` / `-l` - Override locale (e.g., en_US, en_GB)
- `--output` / `-o` - Output format: table or json

---

## Cache Commands

### `prunarr cache init`

Initialize cache for better performance.

**Usage:**
```bash
prunarr cache init [OPTIONS]
```

**Examples:**

```bash
# Quick init (recommended)
prunarr cache init

# Full init (pre-cache everything - slower)
prunarr cache init --full
```

**Options:**
- `--full` / `-f` - Complete initialization with all episodes pre-cached

---

### `prunarr cache status`

View cache statistics.

**Usage:**
```bash
prunarr cache status [OPTIONS]
```

**Examples:**

```bash
# Show cache status
prunarr cache status

# JSON output
prunarr cache status --output json
```

**Options:**
- `--output` / `-o` - Output format: table or json

---

### `prunarr cache clear`

Clear cached data.

**Usage:**
```bash
prunarr cache clear [OPTIONS]
```

**Examples:**

```bash
# Clear specific cache type
prunarr cache clear --type movies
prunarr cache clear --type series
prunarr cache clear --type history

# Clear all cache
prunarr cache clear --type all

# Clear only expired entries
prunarr cache clear --expired

# Skip confirmation
prunarr cache clear --force
```

**Options:**
- `--type` / `-t` - Cache type: movies, series, history, tags, metadata, all
- `--expired` - Clear only expired entries
- `--force` / `-f` - Skip confirmation prompt

---

### `prunarr cache refresh`

Refresh cached data (clear and refetch).

**Usage:**
```bash
prunarr cache refresh [OPTIONS]
```

**Examples:**

```bash
# Refresh history cache
prunarr cache refresh --type history

# Refresh all cache
prunarr cache refresh --type all
```

**Options:**
- `--type` / `-t` - Cache type to refresh: history, all

---

## Global Options

These options work with any command:

```bash
# Use custom config file (required unless using environment variable)
prunarr --config /path/to/config.yaml movies list

# Enable debug logging
prunarr --debug movies list

# Combine both
prunarr --config config.yaml --debug movies remove --dry-run
```

**Global Options:**
- `--config` / `-c` - Path to YAML configuration file
- `--debug` / `-d` - Enable debug logging for detailed output

---

## Quick Reference

### Most Common Commands

```bash
# List movies
prunarr movies list

# Preview movie removal
prunarr movies remove --dry-run

# Remove movies (60+ days)
prunarr movies remove

# List series
prunarr series list

# Get series details
prunarr series get "Breaking Bad"

# Remove series (90+ days)
prunarr series remove --days-watched 90

# Check watch history
prunarr history list --limit 20

# Initialize cache
prunarr cache init
```

### Filter Combinations

```bash
# Large watched movies from specific user
prunarr movies list --username "alice" --watched --min-filesize "5GB"

# Partially watched drama series (not kids or reality)
prunarr series list --partially-watched --tag "Drama" --exclude-tag "Kids" --exclude-tag "Reality"

# Watched movies available on streaming (can be removed safely)
prunarr movies remove --on-streaming --days-watched 30 --dry-run

# Kids content cleanup (fast rotation)
prunarr movies remove --tag "Kids" --days-watched 14
prunarr series remove --tag "Kids" --days-watched 14
```

---

## Need Help?

- **Main Documentation**: See [README](../README.md) for overview
- **Configuration**: See [CONFIGURATION.md](CONFIGURATION.md) for setup
- **Tag System**: Learn about user tags in [TAG_SYSTEM.md](TAG_SYSTEM.md)
- **Streaming Integration**: See [STREAMING.md](STREAMING.md)
- **Troubleshooting**: Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Issues**: Report bugs at https://github.com/haijeploeg/prunarr/issues

---

[← Back to README](../README.md)
