# Configuration Guide

Complete guide to configuring PrunArr.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Step-by-Step Setup](#step-by-step-setup)
- [Finding API Keys](#finding-api-keys)
- [Configuration Options](#configuration-options)
- [Environment Variables](#environment-variables)
- [Configuration Priority](#configuration-priority)

---

## Configuration Overview

**⚠️ Configuration is required!** PrunArr needs API access to Radarr, Sonarr, and Tautulli.

Configuration is done via a YAML file that contains your API credentials and optional settings.

---

## Step-by-Step Setup

### Step 1: Create Your Config File

Download the example configuration:

```bash
curl -O https://raw.githubusercontent.com/haijeploeg/prunarr/main/config.example.yaml
mv config.example.yaml config.yaml
```

Or create `config.yaml` manually with this minimal configuration:

```yaml
# Required: API Credentials
radarr_api_key: "your-radarr-api-key"
radarr_url: "https://radarr.yourdomain.com"
sonarr_api_key: "your-sonarr-api-key"
sonarr_url: "https://sonarr.yourdomain.com"
tautulli_api_key: "your-tautulli-api-key"
tautulli_url: "https://tautulli.yourdomain.com"
```

### Step 2: Find Your API Keys

See [Finding API Keys](#finding-api-keys) section below.

### Step 3: Update Your Config

Edit `config.yaml` and replace the placeholder values with your actual API keys and URLs.

### Step 4: Test Your Configuration

```bash
# Test with a simple command
prunarr --config config.yaml movies list --limit 5
```

If you see a list of movies, you're all set! If you get errors, double-check your API keys and URLs.

---

## Finding API Keys

### Radarr/Sonarr API Keys

1. Open Radarr/Sonarr web interface
2. Go to **Settings** → **General**
3. Show **Advanced Settings**
4. Copy the **API Key** from the Security section

### Tautulli API Key

1. Open Tautulli web interface
2. Go to **Settings** → **Web Interface**
3. Copy the **API Key**

---

## Configuration Options

### Required Settings

These settings are mandatory for PrunArr to function:

```yaml
# Radarr connection
radarr_api_key: "your-radarr-api-key"
radarr_url: "https://radarr.yourdomain.com"

# Sonarr connection
sonarr_api_key: "your-sonarr-api-key"
sonarr_url: "https://sonarr.yourdomain.com"

# Tautulli connection
tautulli_api_key: "your-tautulli-api-key"
tautulli_url: "https://tautulli.yourdomain.com"
```

### Optional Settings

#### User Tag Pattern

Customize how PrunArr identifies user tags (default works with Overseerr):

```yaml
# Default pattern (matches "123 - username")
user_tag_regex: "^\\d+ - (.+)$"

# Custom patterns:
user_tag_regex: "^user:(.+)$"           # For tags like "user:john_doe"
user_tag_regex: "^\\[(.+)\\]$"          # For tags like "[john_doe]"
user_tag_regex: "^req_by_(.+)$"         # For tags like "req_by_alice"
```

#### Logging Configuration

Control log verbosity:

```yaml
# Log level: DEBUG, INFO, WARNING, ERROR
log_level: ERROR  # Default: ERROR (only shows errors)
```

You can also enable debug mode for any command:
```bash
prunarr --debug movies list
```

#### Caching Configuration

Improve performance for large libraries:

```yaml
# Enable/disable caching
cache_enabled: true

# Custom cache directory (optional)
cache_dir: ~/.prunarr/cache

# Cache size limit
cache_max_size_mb: 100

# Cache TTL (Time To Live) in seconds
cache_ttl_movies: 3600      # 1 hour
cache_ttl_series: 3600      # 1 hour
cache_ttl_history: 300      # 5 minutes
cache_ttl_tags: 86400       # 24 hours
cache_ttl_metadata: 604800  # 7 days
```

#### Streaming Provider Configuration

Enable JustWatch integration for streaming availability checks:

```yaml
streaming_enabled: false    # Set to true to enable
streaming_locale: "en_US"   # Your region (language_COUNTRY format)
streaming_providers:        # List of provider technical names
  - "netflix"
  - "amazonprime"
  - "disneyplus"
  - "hulu"
cache_ttl_streaming: 86400  # 24 hours
```

See [STREAMING.md](STREAMING.md) for more details on streaming providers.

---

## Environment Variables

You can also configure PrunArr using environment variables:

```bash
# Required API Settings
export RADARR_API_KEY="your-radarr-api-key"
export RADARR_URL="https://radarr.yourdomain.com"
export SONARR_API_KEY="your-sonarr-api-key"
export SONARR_URL="https://sonarr.yourdomain.com"
export TAUTULLI_API_KEY="your-tautulli-api-key"
export TAUTULLI_URL="https://tautulli.yourdomain.com"

# Optional Settings
export USER_TAG_REGEX="^\\d+ - (.+)$"
export LOG_LEVEL="ERROR"
export CACHE_ENABLED="true"
```

---

## Configuration Priority

PrunArr loads configuration in the following order (later sources override earlier ones):

1. **Default values** (where applicable)
2. **Environment variables**
3. **YAML configuration file** (via `--config` flag)

This means you can:
- Use environment variables for sensitive data in production
- Override specific settings with environment variables
- Keep base configuration in YAML and override as needed

---

## Complete Configuration Example

See [config.example.yaml](https://github.com/haijeploeg/prunarr/blob/main/config.example.yaml) for a complete configuration file with all options and detailed comments.

---

## Security Notes

- **Keep API keys secure**: Never commit `config.yaml` to version control
- **Use `.gitignore`**: Add `config.yaml` to your `.gitignore` file
- **Environment variables**: Consider using environment variables in production
- **File permissions**: Restrict access to your config file (`chmod 600 config.yaml`)

---

[← Back to README](../README.md) | [Next: Quick Start →](QUICK_START.md)
