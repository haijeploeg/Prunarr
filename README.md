# PrunArr

**Automatically clean up your Radarr and Sonarr libraries based on what you've actually watched in Plex/Jellyfin (via Tautulli).**

Stop manually managing your media library. PrunArr removes watched content after a configurable period, checks streaming availability, and gives you complete control over what stays and what goes.

[![PyPI version](https://badge.fury.io/py/prunarr.svg)](https://pypi.org/project/prunarr/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

---

## Quick Start

```bash
# 1. Install
pip install prunarr

# 2. Configure (create config.yaml with your API keys)
curl -O https://raw.githubusercontent.com/haijeploeg/prunarr/main/config.example.yaml
mv config.example.yaml config.yaml
# Edit config.yaml with your API keys

# 3. Preview what would be removed
prunarr --config config.yaml movies remove --dry-run

# 4. Remove watched content (60+ days old by default)
prunarr --config config.yaml movies remove
prunarr --config config.yaml series remove
```

📖 **[Full Quick Start Guide →](docs/QUICK_START.md)**

---

## Why PrunArr?

**The Problem:**
- Your media library keeps growing
- You're running out of storage space
- Manually tracking what's been watched is tedious
- You don't know what's safe to remove
- There are Movies and Shows in your library that are also availble on streaming providers

**The Solution:**
PrunArr automates media cleanup by:
- ✅ Checking Tautulli to see what's been watched
- ✅ Removing content after your specified retention period
- ✅ Checking if content is available on streaming services
- ✅ Supporting user-based tracking for multi-user setups
- ✅ Providing safety features (dry-run, confirmations, previews)

**Perfect for:**
- People with limited storage space
- Multi-user Plex/Jellyfin servers
- Users of Overseerr request management
- Anyone tired of manual library cleanup
- Users who want to prioritize unique content over streamable content

---

## Key Features

### 🎯 User-Based Tracking
Integrates with **Overseerr** to automatically track who requested what. Content is only removed when watched by the original requester.

```bash
prunarr movies remove --username "alice" --days-watched 30
```

📖 **[Tag System Guide →](docs/TAG_SYSTEM.md)**

### ⏰ Flexible Retention Periods
Control exactly how long to keep watched content:

```bash
prunarr movies remove --days-watched 60   # Remove after 60 days
prunarr series remove --days-watched 90   # Keep series longer
```

### 📦 Size-Based Filtering
Target large files to free up space quickly:

```bash
prunarr movies list --min-filesize "5GB" --sort-by filesize --desc
prunarr movies remove --min-filesize "5GB" --days-watched 60
```

### 🏷️ Tag-Based Organization
Filter content by quality, genre, or any custom tags:

```bash
prunarr movies list --tag "4K" --tag "HDR"
prunarr movies remove --tag "Kids" --days-watched 14
prunarr movies remove --exclude-tag "Favorites"
```

### 🎬 Streaming Provider Integration
Check if content is available on your streaming services via JustWatch:

```bash
# Remove watched movies available on streaming
prunarr movies remove --on-streaming --days-watched 30

# Keep unique content longer (not on streaming)
prunarr movies remove --not-on-streaming --days-watched 180
```

📖 **[Streaming Integration Guide →](docs/STREAMING.md)**

### 🛡️ Safety-First Design
Multiple layers of protection:
- **Dry-run mode** - Preview changes before committing
- **Confirmation prompts** - Review what will be removed
- **User verification** - Only remove content watched by the requester
- **Detailed logging** - Track all operations with `--debug`

### 📊 Rich Console Output
Beautiful, informative tables with:
- 🟢 Color-coded status (Watched, Partial, Unwatched)
- 📏 Human-readable file sizes (MB, GB, TB)
- 📅 Last watched dates and days ago
- 🔄 JSON output option for automation

### ⚡ Performance & Automation
- **Intelligent caching** - Minimize API calls
- **JSON output** - Machine-readable for scripts
- **Cron-ready** - Perfect for scheduled automation
- **Exit codes** - Proper status codes for monitoring

---

## Documentation

### Getting Started
- **[Installation Guide](docs/INSTALLATION.md)** - Install PrunArr via pip or from source
- **[Configuration Guide](docs/CONFIGURATION.md)** - Set up API keys and options
- **[Quick Start Guide](docs/QUICK_START.md)** - Get productive in minutes
- **[Command Reference](docs/COMMANDS.md)** - Complete command documentation

### Core Concepts
- **[Tag System](docs/TAG_SYSTEM.md)** - User tracking and content organization
- **[Streaming Integration](docs/STREAMING.md)** - JustWatch provider integration
- **[Advanced Features](docs/ADVANCED.md)** - Automation, scripting, and optimization
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## Common Use Cases

### Weekly Cleanup Routine
```bash
# Preview and remove watched content
prunarr movies remove --days-watched 60 --dry-run
prunarr movies remove --days-watched 60
prunarr series remove --days-watched 90
```

### Free Up Space Quickly
```bash
# Target large files first
prunarr movies list --min-filesize "10GB" --sort-by filesize --desc
prunarr movies remove --min-filesize "5GB" --days-watched 30
```

### Smart Streaming-Based Cleanup
```bash
# Remove watched movies you can re-stream
prunarr movies remove --on-streaming --days-watched 30

# Keep unique content longer
prunarr movies remove --not-on-streaming --days-watched 180
```

### Multi-User Management
```bash
# List content by user
prunarr movies list --username "alice"

# User-specific cleanup
prunarr movies remove --username "bob" --days-watched 45
```

### Kids Content Fast Rotation
```bash
# Quick cleanup of kids content
prunarr movies remove --tag "Kids" --days-watched 14
prunarr series remove --tag "Kids" --days-watched 14
```

📖 **[More Examples →](docs/QUICK_START.md#common-workflows)**

---

## Requirements

- **Python 3.9 or higher**
- **Radarr** (for movies) and/or **Sonarr** (for TV shows)
- **Tautulli** (for watch history tracking)
- **API keys** for all three services
- **Optional: Overseerr** (for automatic user tag management)

---

## Installation

### From PyPI (Recommended)
```bash
pip install prunarr
```

### From Source
```bash
git clone https://github.com/haijeploeg/prunarr
cd prunarr
pip install -e .
```

📖 **[Full Installation Guide →](docs/INSTALLATION.md)**

---

## Configuration

1. **Create config file:**
   ```bash
   curl -O https://raw.githubusercontent.com/haijeploeg/prunarr/main/config.example.yaml
   mv config.example.yaml config.yaml
   ```

2. **Add your API keys:**
   ```yaml
   radarr_api_key: "your-radarr-api-key"
   radarr_url: "https://radarr.yourdomain.com"
   sonarr_api_key: "your-sonarr-api-key"
   sonarr_url: "https://sonarr.yourdomain.com"
   tautulli_api_key: "your-tautulli-api-key"
   tautulli_url: "https://tautulli.yourdomain.com"
   ```

3. **Test your config:**
   ```bash
   prunarr --config config.yaml movies list --limit 5
   ```

📖 **[Full Configuration Guide →](docs/CONFIGURATION.md)**

---

## Overseerr Integration

PrunArr works seamlessly with Overseerr's "Tag Requests" feature:

1. In Overseerr, go to **Settings** → **Radarr/Sonarr**
2. Enable **"Tag Requests"**
3. That's it! PrunArr will automatically track who requested what

When users request content through Overseerr:
- Tags are automatically created (e.g., `"123 - john_doe"`)
- PrunArr matches usernames with Tautulli
- Content is only removed when watched by the original requester

📖 **[Tag System Guide →](docs/TAG_SYSTEM.md#automatic-tags-with-overseerr-recommended)**

---

## Command Overview

**Movies:**
```bash
prunarr movies list                      # List all movies
prunarr movies remove --dry-run          # Preview removal
prunarr movies remove --days-watched 60  # Remove watched movies
```

**Series:**
```bash
prunarr series list                      # List all series
prunarr series get "Breaking Bad"        # Get detailed info
prunarr series remove --days-watched 90  # Remove watched series
```

**History:**
```bash
prunarr history list --limit 20          # View watch history
```

**Streaming:**
```bash
prunarr providers list                   # List streaming providers
prunarr providers check "The Matrix"     # Check availability
```

**Cache:**
```bash
prunarr cache init                       # Initialize cache
prunarr cache status                     # View cache stats
```

📖 **[Complete Command Reference →](docs/COMMANDS.md)**

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Format code (`make format`)
6. Commit (`git commit -m 'feat: add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/haijeploeg/prunarr
cd prunarr
python -m venv env
source env/bin/activate
pip install -e ".[dev]"

# Run tests
make test

# Format code
make format

# Run linting
make lint
```

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/haijeploeg/prunarr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/haijeploeg/prunarr/discussions)

---

## License

Apache-2.0 License - See [LICENSE](LICENSE) file for details.

---

## Links

- **GitHub**: https://github.com/haijeploeg/prunarr
- **PyPI**: https://pypi.org/project/prunarr/
- **Issues**: https://github.com/haijeploeg/prunarr/issues

---

**Made with ❤️ for the Plex/Jellyfin community**

*PrunArr is not affiliated with Radarr, Sonarr, Tautulli, Overseerr, Plex, or Jellyfin.*
