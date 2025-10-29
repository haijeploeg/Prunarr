# Tag System Guide

Complete guide to PrunArr's tag system for user tracking and content organization.

## Table of Contents

- [Overview](#overview)
- [User Tags (Required for Removal)](#user-tags-required-for-removal)
- [Automatic Tags with Overseerr](#automatic-tags-with-overseerr-recommended)
- [Manual User Tags](#manual-user-tags)
- [Custom Tag Patterns](#custom-tag-patterns)
- [Organizational Tags](#organizational-tags)
- [Tag Filtering](#tag-filtering)

---

## Overview

PrunArr uses tags in Radarr/Sonarr for two purposes:

1. **User Tracking** - Associate content with specific users for removal
2. **Content Organization** - Filter and manage content by categories (4K, HDR, Kids, etc.)

---

## User Tags (Required for Removal)

**Format:** `"userid - username"` (e.g., `"123 - john_doe"`)

User tags tell PrunArr:
- Who requested this content
- Who should be able to remove it
- Which Tautulli user to match for watch status

**Important Rules:**
- Only movies/shows with user tags are processed for removal
- The username must match a user in Tautulli
- Content is only removed when watched by the user specified in the tag
- Pattern is configurable via `user_tag_regex` in config (default: `^\d+ - (.+)$`)

---

## Automatic Tags with Overseerr (Recommended)

**The easiest way to set up user tags is with Overseerr's "Tag Requests" feature!**

Overseerr can automatically add user tags to Radarr/Sonarr when users request content. This means PrunArr will automatically know who requested what, and only remove content watched by the original requester.

### Setup in Overseerr

1. Open Overseerr web interface
2. Go to **Settings** → **Radarr** (or **Sonarr**)
3. Edit your Radarr/Sonarr server configuration
4. Enable **"Tag Requests"**
5. Save settings

That's it! Now when users request movies or shows through Overseerr:
- Overseerr automatically creates a tag like `"123 - john_doe"`
- The tag is added to the content in Radarr/Sonarr
- PrunArr can match the username with Tautulli users
- Content is only removed when watched by the original requester

### Benefits

- ✅ No manual tag management needed
- ✅ Perfect for multi-user Plex/Jellyfin servers
- ✅ Ensures users only affect their own requested content
- ✅ Works automatically for all new requests
- ✅ Integrates seamlessly with PrunArr's default configuration

### How It Works

1. **User requests content** in Overseerr (e.g., user "alice" requests "The Matrix")
2. **Overseerr creates tag** in format `"123 - alice"` (where 123 is the user's ID)
3. **Content is added** to Radarr/Sonarr with the user tag
4. **User watches content** tracked by Tautulli
5. **PrunArr matches** the tag username ("alice") with Tautulli username
6. **Content is removed** only when alice has watched it for the configured period

---

## Manual User Tags

If you're not using Overseerr, you can manually create tags in Radarr/Sonarr.

### Creating Manual Tags

1. **In Radarr/Sonarr**, go to **Settings** → **Tags**
2. **Create tags** following the pattern: `"123 - john_doe"`, `"456 - alice"`, etc.
   - The number can be any ID (doesn't have to be a real user ID)
   - The username after the dash must match the username in Tautulli
3. **Assign tags** to movies/series when adding or editing them
4. **Verify** the username matches exactly with Tautulli usernames

### Example Manual Tags

```
123 - john_doe
456 - alice
789 - bob
100 - family_account
```

Each content item should have one user tag indicating who requested it.

---

## Custom Tag Patterns

You can customize the user tag pattern in `config.yaml` if you have a different tagging scheme:

```yaml
# Default pattern (works with Overseerr)
user_tag_regex: "^\\d+ - (.+)$"

# Custom patterns:
user_tag_regex: "^user:(.+)$"           # For tags like "user:john_doe"
user_tag_regex: "^\\[(.+)\\]$"          # For tags like "[john_doe]"
user_tag_regex: "^req_by_(.+)$"         # For tags like "req_by_alice"
user_tag_regex: "^(.+)@.+$"             # For tags like "john@family"
```

**Pattern Requirements:**
- Must be a valid regex pattern
- Must have exactly one capture group `()` that extracts the username
- The extracted username must match a username in Tautulli

**Testing Your Pattern:**

```bash
# Enable debug mode to see how tags are parsed
prunarr --debug movies list --limit 5
```

---

## Organizational Tags

**Examples:** `"4K"`, `"HDR"`, `"Kids"`, `"Action"`, `"Documentary"`

These are regular tags that don't match the user tag pattern. Use them to organize and filter content by categories, quality, genre, etc.

### Common Organizational Tags

- **Quality**: `4K`, `HDR`, `1080p`, `REMUX`
- **Genre**: `Action`, `Drama`, `Comedy`, `Horror`, `Sci-Fi`
- **Audience**: `Kids`, `Family`, `Adults`
- **Source**: `Bluray`, `WEB-DL`, `HDTV`
- **Status**: `Favorites`, `Must-Keep`, `Temporary`

### Creating Organizational Tags

1. In Radarr/Sonarr, go to **Settings** → **Tags**
2. Create tags for your organizational system
3. Assign tags to content as needed
4. Use tags for filtering in PrunArr

---

## Tag Filtering

PrunArr supports powerful tag-based filtering for both user tags and organizational tags.

### Basic Tag Filtering

```bash
# Include only items with specific tag
prunarr movies list --tag "4K"

# Exclude items with specific tag
prunarr movies list --exclude-tag "Kids"

# Combine include and exclude
prunarr movies list --tag "Action" --exclude-tag "Kids"
```

### Multiple Tags (OR Logic)

By default, multiple `--tag` options use OR logic (item has at least one tag):

```bash
# Show movies with Action OR Sci-Fi tag
prunarr movies list --tag "Action" --tag "Sci-Fi"

# Show series with Drama OR Thriller tag
prunarr series list --tag "Drama" --tag "Thriller"
```

### Multiple Tags (AND Logic)

Use `--tag-match-all` to require ALL specified tags:

```bash
# Show movies with BOTH 4K AND HDR tags
prunarr movies list --tag "4K" --tag "HDR" --tag-match-all

# Show series with BOTH Drama AND HBO tags
prunarr series list --tag "Drama" --tag "HBO" --tag-match-all
```

### Complex Tag Filters

```bash
# 4K movies that are NOT kids content
prunarr movies list --tag "4K" --exclude-tag "Kids"

# Action or Sci-Fi movies, but not kids content
prunarr movies list --tag "Action" --tag "Sci-Fi" --exclude-tag "Kids"

# Movies with BOTH 4K and HDR, excluding favorites
prunarr movies list --tag "4K" --tag "HDR" --tag-match-all --exclude-tag "Favorites"
```

### Tag Filtering in Remove Commands

All tag filters work in remove commands:

```bash
# Remove kids content after 2 weeks
prunarr movies remove --watched --tag "Kids" --days-watched 14

# Remove 4K content after 90 days (keep longer due to quality)
prunarr movies remove --watched --tag "4K" --days-watched 90

# Remove content without favorite tag after 60 days
prunarr movies remove --watched --exclude-tag "Favorites" --days-watched 60
```

---

## Tag Display

### In List Commands

- **User tags** are shown in the "User" column
- **Organizational tags** are shown in the "Tags" column
- Maximum of 3 tags displayed, with "+N more" if there are additional tags
- Tag matching is case-insensitive

### Example Output

```
Title                User        Tags                Status
─────────────────────────────────────────────────────────────
The Matrix           john_doe    4K, HDR            Watched
Toy Story            alice       Kids, Family       Watched
Breaking Bad         bob         Drama, Crime, +1   Partial
```

---

## Best Practices

### 1. Use Overseerr for User Tags

If you have Overseerr, enable "Tag Requests" for automatic user tag management.

### 2. Consistent Organizational Tags

Create a standard set of organizational tags and use them consistently:
- Quality tags: 4K, HDR, 1080p
- Genre tags: Action, Drama, Comedy, etc.
- Audience tags: Kids, Family, Adults

### 3. Keep User Tags Clean

- One user tag per content item
- Username must match Tautulli exactly
- Don't reuse user tags for organizational purposes

### 4. Test Your Tag System

Before removing content, verify tags are working:

```bash
# List content by user to verify tags
prunarr movies list --username "alice"

# Check that organizational tags work
prunarr movies list --tag "4K"
```

### 5. Document Your Tag Scheme

Keep a document of your tag meanings for consistency across your team.

---

## Troubleshooting

### Content Not Being Removed

**Problem**: Movies/series aren't being removed even though they're watched.

**Possible Causes**:
1. No user tag on the content
2. Username in tag doesn't match Tautulli username
3. Content watched by different user than requester

**Solution**:
```bash
# Check if content has user tags
prunarr --debug movies list | grep "tag"

# Verify usernames match between tags and Tautulli
prunarr history list --username "alice"
```

### Tag Pattern Not Matching

**Problem**: Tags aren't being recognized.

**Solution**:
```bash
# Enable debug to see how tags are parsed
prunarr --debug movies list --limit 5

# Verify your regex pattern in config
# Test pattern at: https://regex101.com/
```

### Multiple User Tags

**Problem**: Content has multiple user tags.

**Solution**: PrunArr uses the first matching user tag. Remove extra user tags from content in Radarr/Sonarr.

---

## Examples

### Complete Workflow with Tags

```bash
# 1. List content by user (verify tags work)
prunarr movies list --username "alice"

# 2. List content by organizational tag
prunarr movies list --tag "4K"

# 3. Combine filters
prunarr movies list --username "alice" --tag "4K" --watched

# 4. Remove with tag filters
prunarr movies remove --watched --tag "Kids" --days-watched 14 --dry-run

# 5. Remove excluding favorites
prunarr movies remove --watched --exclude-tag "Favorites" --days-watched 60
```

---

[← Back to README](../README.md) | [Next: Streaming Integration →](STREAMING.md)
