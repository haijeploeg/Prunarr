# Quick Start Guide

Get up and running with PrunArr in minutes.

## Prerequisites

Before starting, make sure you have:
- ✅ PrunArr installed ([Installation Guide](INSTALLATION.md))
- ✅ Configuration file created ([Configuration Guide](CONFIGURATION.md))
- ✅ User tags set up in Radarr/Sonarr ([Tag System Guide](TAG_SYSTEM.md))

---

## Your First Commands

### Step 1: List Your Content

Start by viewing your movies and series:

```bash
# List movies with watch status
prunarr --config config.yaml movies list --limit 10

# List TV series with watch progress
prunarr --config config.yaml series list --limit 10
```

### Step 2: Check Watch History

Verify that Tautulli is tracking watch history:

```bash
# View recent watch history
prunarr --config config.yaml history list --limit 20
```

### Step 3: Preview Removal (Dry Run)

**Always start with dry-run mode** to see what would be removed:

```bash
# Preview movie removal (60+ days old by default)
prunarr --config config.yaml movies remove --dry-run

# Preview series removal
prunarr --config config.yaml series remove --dry-run
```

Review the output carefully. The preview shows exactly what will be removed.

### Step 4: Remove Content

If you're happy with the preview, remove the `--dry-run` flag:

```bash
# Remove watched movies (60+ days old)
prunarr --config config.yaml movies remove

# Remove watched series (60+ days old)
prunarr --config config.yaml series remove
```

---

## Common First Tasks

### View Detailed Series Information

```bash
# Get episode-level details for a series
prunarr --config config.yaml series get "Breaking Bad"

# Show only unwatched episodes
prunarr --config config.yaml series get "The Office" --unwatched-only
```

### Filter by User

```bash
# List movies for a specific user
prunarr --config config.yaml movies list --username "alice"

# Remove movies for a specific user
prunarr --config config.yaml movies remove --username "alice" --days-watched 30
```

### Target Large Files

```bash
# Find large movies
prunarr --config config.yaml movies list --min-filesize "5GB" --sort-by filesize --desc

# Remove large watched movies
prunarr --config config.yaml movies remove --min-filesize "5GB" --days-watched 60
```

### Filter by Tags

```bash
# List 4K content
prunarr --config config.yaml movies list --tag "4K"

# Remove kids content after 2 weeks
prunarr --config config.yaml movies remove --tag "Kids" --days-watched 14
```

---

## Pro Tips

### 1. Use Shorter Commands

Set an alias or environment variable to avoid typing `--config config.yaml` every time:

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias p="prunarr --config /path/to/config.yaml"

# Now use shorter commands
p movies list
p series remove --dry-run
```

### 2. Initialize Cache for Better Performance

For large libraries, initialize the cache:

```bash
prunarr --config config.yaml cache init
```

This significantly improves performance by caching API responses.

### 3. Always Test with Dry Run

Before running any remove command for the first time:

```bash
# ALWAYS preview first
prunarr movies remove --days-watched 90 --dry-run

# Then run for real if happy
prunarr movies remove --days-watched 90
```

### 4. Use JSON Output for Scripts

Get machine-readable output:

```bash
prunarr movies list --output json > movies.json
prunarr series list --output json | jq '.[] | select(.watched_episodes > 0)'
```

### 5. Enable Debug Mode for Troubleshooting

If something isn't working:

```bash
prunarr --debug movies list
```

---

## Common Workflows

### Weekly Cleanup Routine

```bash
#!/bin/bash
# weekly-cleanup.sh

CONFIG="/path/to/config.yaml"

# Preview what would be removed
prunarr --config $CONFIG movies remove --days-watched 60 --dry-run
prunarr --config $CONFIG series remove --days-watched 90 --dry-run

# If happy, uncomment to run:
# prunarr --config $CONFIG movies remove --days-watched 60
# prunarr --config $CONFIG series remove --days-watched 90
```

### Free Up Space Quickly

```bash
# Target large files first
prunarr movies list --min-filesize "10GB" --sort-by filesize --desc --limit 20
prunarr movies remove --min-filesize "5GB" --days-watched 30 --dry-run
```

### Smart Streaming-Based Cleanup

If you have streaming providers configured:

```bash
# Remove watched movies available on streaming
prunarr movies remove --on-streaming --days-watched 30

# Keep unique content longer
prunarr movies remove --not-on-streaming --days-watched 180
```

---

## Next Steps

- **Learn all commands**: See [Command Reference](COMMANDS.md)
- **Understand tag system**: Read [Tag System Guide](TAG_SYSTEM.md)
- **Set up streaming**: Check [Streaming Integration](STREAMING.md)
- **Automate**: See [Advanced Features](ADVANCED.md)

---

## Need Help?

- **Troubleshooting**: See [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Report Issues**: https://github.com/haijeploeg/prunarr/issues

---

[← Back to README](../README.md) | [Next: Command Reference →](COMMANDS.md)
