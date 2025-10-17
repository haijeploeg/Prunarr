# Docker Deployment Guide

This guide covers running PrunArr using Docker and Docker Compose.

## Quick Start

### Pull from GitHub Container Registry

PrunArr images are automatically built and published to GitHub Container Registry (GHCR):

```bash
# Pull latest version
docker pull ghcr.io/hploeg/prunarr:latest

# Pull specific version
docker pull ghcr.io/hploeg/prunarr:1.0.0

# Pull by major version (automatically gets latest minor/patch)
docker pull ghcr.io/hploeg/prunarr:1
```

**Available Tags:**
- `latest` - Latest stable release from main branch
- `1.0.0` - Full version (e.g., v1.0.0 → 1.0.0)
- `1.0` - Major.minor version (e.g., v1.0.0 → 1.0)
- `1` - Major version only (e.g., v1.0.0 → 1)

**Supported Architectures:**
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit, including Apple Silicon)

### Build Locally

```bash
# Clone the repository
git clone https://github.com/hploeg/prunarr.git
cd prunarr

# Build the image
docker build -t prunarr:latest .

# Build for multiple architectures (requires buildx)
docker buildx build --platform linux/amd64,linux/arm64 -t prunarr:latest .
```

## Running with Docker

### Basic Usage

Run a one-time command:

```bash
docker run --rm \
  -e RADARR_API_KEY="your-api-key" \
  -e RADARR_URL="https://radarr.example.com" \
  -e SONARR_API_KEY="your-api-key" \
  -e SONARR_URL="https://sonarr.example.com" \
  -e TAUTULLI_API_KEY="your-api-key" \
  -e TAUTULLI_URL="https://tautulli.example.com" \
  ghcr.io/hploeg/prunarr:latest movies list --limit 10
```

### With Persistent Cache

Create a volume for cache persistence:

```bash
docker volume create prunarr-cache

docker run --rm \
  -e RADARR_API_KEY="your-api-key" \
  -e RADARR_URL="https://radarr.example.com" \
  -e SONARR_API_KEY="your-api-key" \
  -e SONARR_URL="https://sonarr.example.com" \
  -e TAUTULLI_API_KEY="your-api-key" \
  -e TAUTULLI_URL="https://tautulli.example.com" \
  -e CACHE_ENABLED=true \
  -v prunarr-cache:/home/prunarr/.prunarr/cache \
  ghcr.io/hploeg/prunarr:latest series list --limit 10
```

### Using Config File

Mount a config file instead of environment variables:

```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v prunarr-cache:/home/prunarr/.prunarr/cache \
  ghcr.io/hploeg/prunarr:latest --config /app/config.yaml movies list
```

## Docker Compose

### Setup

1. Copy the example docker-compose file:
   ```bash
   # Already included in the repository
   cp docker-compose.yml docker-compose.yml
   ```

2. Create a `.env` file with your API keys:
   ```bash
   cat > .env <<EOF
   RADARR_API_KEY=your-radarr-api-key
   RADARR_URL=https://radarr.example.com
   SONARR_API_KEY=your-sonarr-api-key
   SONARR_URL=https://sonarr.example.com
   TAUTULLI_API_KEY=your-tautulli-api-key
   TAUTULLI_URL=https://tautulli.example.com
   EOF
   ```

### Running Commands

Run one-time commands:

```bash
# List movies
docker-compose run --rm prunarr movies list --limit 10

# List series
docker-compose run --rm prunarr series list --limit 10

# Remove watched movies
docker-compose run --rm prunarr movies remove --days-watched 60 --dry-run

# Initialize cache
docker-compose run --rm prunarr cache init
```

### Scheduled Execution with Cron

For scheduled cleanup, use your host's cron or a dedicated scheduler container:

**Option 1: Host Cron**

Add to your crontab (`crontab -e`):

```cron
# Run movie cleanup daily at 2 AM
0 2 * * * cd /path/to/prunarr && docker-compose run --rm prunarr movies remove --days-watched 60 --force

# Run series cleanup daily at 3 AM
0 3 * * * cd /path/to/prunarr && docker-compose run --rm prunarr series remove --days-watched 60 --force
```

**Option 2: Ofelia Scheduler (Docker-based)**

Add to your docker-compose.yml:

```yaml
services:
  scheduler:
    image: mcuadros/ofelia:latest
    depends_on:
      - prunarr
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      # Movie cleanup - daily at 2 AM
      ofelia.job-run.prunarr-movies.schedule: "0 0 2 * * *"
      ofelia.job-run.prunarr-movies.container: "prunarr"
      ofelia.job-run.prunarr-movies.command: "movies remove --days-watched 60 --force"

      # Series cleanup - daily at 3 AM
      ofelia.job-run.prunarr-series.schedule: "0 0 3 * * *"
      ofelia.job-run.prunarr-series.container: "prunarr"
      ofelia.job-run.prunarr-series.command: "series remove --days-watched 60 --force"
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `RADARR_API_KEY` | Radarr API key | `abc123...` |
| `RADARR_URL` | Radarr URL | `https://radarr.example.com` |
| `SONARR_API_KEY` | Sonarr API key | `def456...` |
| `SONARR_URL` | Sonarr URL | `https://sonarr.example.com` |
| `TAUTULLI_API_KEY` | Tautulli API key | `ghi789...` |
| `TAUTULLI_URL` | Tautulli URL | `https://tautulli.example.com` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `USER_TAG_REGEX` | User tag regex pattern | `^\d+ - (.+)$` |
| `CACHE_ENABLED` | Enable caching | `true` |
| `CACHE_DIR` | Cache directory | `/home/prunarr/.prunarr/cache` |
| `CACHE_MAX_SIZE_MB` | Max cache size (MB) | `100` |
| `CACHE_TTL_MOVIES` | Movie cache TTL (seconds) | `3600` |
| `CACHE_TTL_SERIES` | Series cache TTL (seconds) | `3600` |
| `CACHE_TTL_HISTORY` | History cache TTL (seconds) | `300` |
| `CACHE_TTL_TAGS` | Tags cache TTL (seconds) | `86400` |
| `CACHE_TTL_METADATA` | Metadata cache TTL (seconds) | `86400` |
| `STREAMING_ENABLED` | Enable streaming checks | `false` |
| `STREAMING_LOCALE` | Streaming locale | `en_US` |
| `STREAMING_PROVIDERS` | Comma-separated providers | `netflix,amazonprime` |
| `LOG_LEVEL` | Logging level | `ERROR` |

## Image Details

### Base Image
- `python:3.12-slim` - Minimal Python runtime

### Image Size
- Builder stage: ~500MB
- Final image: ~150MB

### Security
- Runs as non-root user (UID 1000)
- Minimal attack surface
- No unnecessary packages

### Volumes
- `/home/prunarr/.prunarr/cache` - Cache directory for persistence

## Examples

### Dry Run Before Cleanup

```bash
# See what would be removed without actually deleting
docker-compose run --rm prunarr movies remove --days-watched 60 --dry-run
```

### Filter by User

```bash
# Remove only specific user's watched content
docker-compose run --rm prunarr movies remove --username john_doe --days-watched 30 --force
```

### Debugging

```bash
# Enable debug logging
docker-compose run --rm -e LOG_LEVEL=DEBUG prunarr movies list --limit 5
```

### Multiple Instances

Run different cleanup tasks in parallel:

```bash
# Movies and series cleanup simultaneously
docker-compose run --rm -d prunarr movies remove --days-watched 60 --force
docker-compose run --rm -d prunarr series remove --days-watched 60 --force
```

## Troubleshooting

### Container Exits Immediately

**Problem:** Container exits without error
**Solution:** The default entrypoint shows help. Specify a command:

```bash
docker-compose run --rm prunarr --help
```

### Permission Denied on Cache

**Problem:** Cannot write to cache directory
**Solution:** Ensure volume permissions match the container user (UID 1000):

```bash
docker volume inspect prunarr-cache
# If needed, fix permissions:
docker run --rm -v prunarr-cache:/cache alpine chown -R 1000:1000 /cache
```

### API Connection Errors

**Problem:** Cannot connect to Radarr/Sonarr/Tautulli
**Solution:**
- Ensure URLs are accessible from container network
- Use `host.docker.internal` for localhost services (Docker Desktop)
- Check API keys are correct

### Cache Not Persisting

**Problem:** Cache resets between runs
**Solution:** Ensure volume is mounted:

```bash
docker-compose run --rm prunarr cache status
# Verify CACHE_DIR matches volume mount point
```

## Next Steps

- [Kubernetes Deployment](KUBERNETES.md) - Deploy with Kubernetes/Helm
- [Configuration Guide](CONFIGURATION.md) - Detailed configuration options
- [Quick Start Guide](QUICK_START.md) - Common workflows
