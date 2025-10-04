"""
Cache command module for PrunArr CLI.

This module provides commands for managing PrunArr's performance cache,
including initialization, status reporting, and cache clearing operations.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from prunarr.config import Settings
from prunarr.logger import get_logger
from prunarr.prunarr import PrunArr
from prunarr.utils.validators import validate_output_format

app = typer.Typer(help="Manage PrunArr cache.", rich_markup_mode="rich")
console = Console()

# Thread pool configuration
MAX_WORKERS_DEFAULT = 10  # For general parallel operations (tags, metadata)
MAX_WORKERS_API_HEAVY = 5  # For API-heavy operations (episodes, streaming)


# ============================================================================
# Helper Functions
# ============================================================================


def _setup_context(ctx: typer.Context):
    """Extract common context objects."""
    context_obj = ctx.obj
    settings = context_obj["settings"]
    debug = context_obj["debug"]
    logger = get_logger("cache", debug=debug, log_level=settings.log_level)
    return settings, debug, logger


def _validate_cache_enabled(settings: Settings, logger, debug: bool = False, require_enabled: bool = True):
    """Validate cache is enabled and return PrunArr instance."""
    if not settings.cache_enabled:
        if require_enabled:
            logger.error("Caching is disabled in configuration. Set cache_enabled=true to use caching.")
            raise typer.Exit(1)
        else:
            logger.warning("Caching is disabled in configuration")
            return None

    prunarr = PrunArr(settings, debug=debug)
    if not prunarr.cache_manager:
        logger.error("Cache manager not available")
        raise typer.Exit(1)

    return prunarr


def _fetch_data(prunarr: PrunArr, data_type: str, logger):
    """Fetch data with status indicator."""
    actions = {
        "movies": (prunarr.radarr.get_movie, "movies", "movies"),
        "series": (prunarr.sonarr.get_series, "series", "series"),
        "history": (lambda: prunarr.tautulli.get_watch_history(page_size=1000), "watch history", "watch history records"),
    }

    if data_type not in actions:
        return None

    fetch_fn, display_name, item_name = actions[data_type]

    try:
        with console.status(f"[cyan]Caching {display_name}..."):
            data = fetch_fn()
            console.print(f"[green]✓[/green] Cached {len(data)} {item_name}")
            return data
    except Exception as e:
        logger.error(f"Failed to cache {display_name}: {str(e)}")
        return None


def _collect_tag_ids(results: dict) -> set:
    """Collect all tag IDs from movies and series."""
    tag_ids = set()
    for data_type in ["movies", "series"]:
        if data_type in results:
            for item in results[data_type]:
                tag_ids.update(item.get("tags", []))
    return tag_ids


def _collect_rating_keys(history: list) -> set:
    """Extract unique rating keys from watch history."""
    unique_keys = set()
    for record in history:
        # For episodes, we need the grandparent (series) rating key
        if grandparent_key := record.get("grandparent_rating_key"):
            unique_keys.add(str(grandparent_key))
        # For movies, we need the rating key
        if rating_key := record.get("rating_key"):
            unique_keys.add(str(rating_key))
    return unique_keys


def _cache_in_parallel(items, fetch_fn, executor_workers=None):
    """Cache items in parallel and return success count."""
    if not items:
        return 0

    if executor_workers is None:
        executor_workers = MAX_WORKERS_DEFAULT

    cached_count = 0
    with ThreadPoolExecutor(max_workers=executor_workers) as executor:
        futures = {executor.submit(fetch_fn, item): item for item in items}
        for future in as_completed(futures):
            try:
                future.result()
                cached_count += 1
            except Exception:
                pass  # Continue on error
    return cached_count


def _cache_tags(prunarr: PrunArr, tag_ids: set):
    """Cache tags with status indicator."""
    if not tag_ids:
        return

    with console.status(f"[cyan]Caching {len(tag_ids)} tags..."):
        cached = _cache_in_parallel(tag_ids, prunarr.radarr.get_tag)
        console.print(f"[green]✓[/green] Cached {cached} tags")


def _cache_metadata(prunarr: PrunArr, rating_keys: set, logger):
    """Cache Tautulli metadata with status indicator."""
    if not rating_keys:
        return

    logger.info("Fetching Tautulli metadata for watch history...")
    with console.status(f"[cyan]Caching {len(rating_keys)} Tautulli metadata records..."):
        cached = _cache_in_parallel(rating_keys, prunarr.tautulli.get_metadata)
        console.print(f"[green]✓[/green] Cached {cached} Tautulli metadata records")


def _cache_episodes(prunarr: PrunArr, series_data: list):
    """Cache episodes for all series with status indicator."""
    series_ids = [s.get("id") for s in series_data if s.get("id")]
    if not series_ids:
        return

    with console.status(f"[cyan]Caching episodes for {len(series_ids)} series..."):
        cached_series = 0
        total_episodes = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS_API_HEAVY) as executor:
            futures = {executor.submit(prunarr.sonarr.get_episodes_by_series_id, sid): sid for sid in series_ids}
            for future in as_completed(futures):
                try:
                    episodes = future.result()
                    cached_series += 1
                    total_episodes += len(episodes)
                except Exception:
                    pass

        console.print(f"[green]✓[/green] Cached {total_episodes} episodes across {cached_series} series")


def _cache_streaming(prunarr: PrunArr, results: dict, settings: Settings, logger, debug: bool):
    """Cache streaming availability with status indicator."""
    from prunarr.services.streaming_checker import StreamingChecker

    streaming_checker = StreamingChecker(
        locale=settings.streaming_locale,
        providers=settings.streaming_providers,
        cache_manager=prunarr.cache_manager,
        logger=logger,
    )

    # Prepare items to cache
    items_to_cache = []
    for movie in results.get("movies", []):
        items_to_cache.append(("movie", movie))
    for series_item in results.get("series", []):
        items_to_cache.append(("series", series_item))

    if not items_to_cache:
        logger.warning("No items to cache streaming availability for")
        return

    with console.status(f"[cyan]Checking streaming availability for {len(items_to_cache)} items..."):
        cached_items = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS_API_HEAVY) as executor:
            futures = {}
            for item_type, item in items_to_cache:
                if item_type == "movie":
                    future = executor.submit(
                        streaming_checker.check_movie_availability,
                        title=item.get("title"),
                        year=item.get("year"),
                        imdb_id=item.get("imdbId"),
                    )
                else:  # series
                    future = executor.submit(
                        streaming_checker.check_series_availability,
                        title=item.get("title"),
                        tvdb_id=item.get("tvdbId"),
                    )
                futures[future] = (item_type, item)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        cached_items += 1
                except Exception as e:
                    if debug:
                        item_type, item = futures[future]
                        logger.debug(f"Failed to cache streaming for {item_type} '{item.get('title')}': {str(e)}")

        console.print(f"[green]✓[/green] Cached streaming availability for {cached_items} items")


def _clear_cache_types(prunarr: PrunArr, logger, movies: bool = False, series: bool = False,
                       history: bool = False, tags: bool = False, metadata: bool = False,
                       episodes: bool = False, streaming: bool = False, all_cache: bool = False):
    """
    Clear specified cache types and display confirmation message.

    Args:
        prunarr: PrunArr instance with cache_manager
        logger: Logger instance
        movies: Clear movies cache
        series: Clear series cache
        history: Clear history cache
        tags: Clear tags cache
        metadata: Clear metadata cache
        episodes: Clear episodes cache
        streaming: Clear streaming cache
        all_cache: Clear all cache types

    Returns:
        List of cleared cache type names
    """
    cleared_types = []

    if all_cache:
        prunarr.cache_manager.clear_all()
        # Expand "all" to show what was actually cleared
        cleared_types = ["tags", "movies", "series", "episodes", "metadata", "history", "streaming"]
    else:
        if tags:
            prunarr.cache_manager.clear_tags()
            cleared_types.append("tags")
        if movies:
            prunarr.cache_manager.clear_movies()
            cleared_types.append("movies")
        if series:
            prunarr.cache_manager.clear_series()  # This also clears episodes
            cleared_types.append("series")
            cleared_types.append("episodes")  # Show that episodes were also cleared
        if metadata:
            prunarr.cache_manager.clear_metadata()
            cleared_types.append("metadata")
        if history:
            prunarr.cache_manager.clear_history()
            cleared_types.append("history")
        if episodes and not series:  # Only if not already cleared by series
            prunarr.cache_manager.clear_episodes()
            if "episodes" not in cleared_types:
                cleared_types.append("episodes")
        if streaming:
            prunarr.cache_manager.clear_streaming()
            cleared_types.append("streaming")

    if cleared_types:
        cleared_msg = ", ".join(cleared_types)
        console.print(f"[green]✓[/green] Cleared cache: {cleared_msg}")
        logger.info(f"Cleared cache: {cleared_msg}")

    return cleared_types


def _perform_cache_init(prunarr: PrunArr, settings: Settings, logger, debug: bool,
                        movies: bool, series: bool, history: bool, episodes: bool, streaming: bool):
    """Perform cache initialization with specified options."""
    # Phase 1: Fetch main data
    results = {}
    for data_type, enabled in [("movies", movies), ("series", series), ("history", history)]:
        if enabled:
            if data := _fetch_data(prunarr, data_type, logger):
                results[data_type] = data

    if not results:
        logger.warning("No data types selected for caching. Use --movies, --series, or --history flags.")
        raise typer.Exit(0)

    # Phase 2: Cache tags
    tag_ids = _collect_tag_ids(results)
    _cache_tags(prunarr, tag_ids)

    # Phase 3: Cache Tautulli metadata
    if "history" in results:
        rating_keys = _collect_rating_keys(results["history"])
        _cache_metadata(prunarr, rating_keys, logger)

    # Phase 4: Cache episodes if requested
    if episodes and "series" in results:
        _cache_episodes(prunarr, results["series"])

    # Phase 5: Cache streaming availability if requested
    if streaming:
        if settings.streaming_enabled:
            logger.info("Pre-caching streaming availability data...")
            _cache_streaming(prunarr, results, settings, logger, debug)
        else:
            logger.warning(
                "Streaming flag provided but streaming_enabled=false in config. "
                "Set streaming_enabled=true to enable streaming checks."
            )


# ============================================================================
# Commands
# ============================================================================


@app.command("init")
def init_cache(
    ctx: typer.Context,
    movies: bool = typer.Option(True, "--movies/--no-movies", "-m", help="Cache movies data (default: True)"),
    series: bool = typer.Option(True, "--series/--no-series", "-s", help="Cache series data (default: True)"),
    history: bool = typer.Option(True, "--history/--no-history", "-h", help="Cache watch history (default: True)"),
    episodes: bool = typer.Option(False, "--episodes/--no-episodes", "-e", help="Pre-fetch ALL episodes for each series (slower, but fully cached)"),
    streaming: bool = typer.Option(
        False,
        "--streaming/--no-streaming",
        "-t",
        help="Pre-cache streaming availability for all movies and series (requires streaming_enabled=true)",
    ),
):
    """
    [bold cyan]Initialize PrunArr cache with selected data.[/bold cyan]

    Pre-populates the cache with data from Radarr, Sonarr, and Tautulli to
    dramatically improve performance for subsequent commands. First-time setup
    typically takes 30-60 seconds, but makes all other commands near-instant.

    [bold yellow]What gets cached:[/bold yellow]
        • [cyan]Movies[/cyan] (-m/--movies, default: on) - Radarr movie library
        • [cyan]Series[/cyan] (-s/--series, default: on) - Sonarr series library
        • [cyan]History[/cyan] (-h/--history, default: on) - Tautulli watch history
        • [cyan]Tags[/cyan] (automatic) - Movie/series tags when movies or series enabled
        • [cyan]Metadata[/cyan] (automatic) - IMDB/TVDB IDs when history enabled
        • [cyan]Episodes[/cyan] (-e/--episodes, default: off) - All episode files [yellow](slower)[/yellow]
        • [cyan]Streaming[/cyan] (-t/--streaming, default: off) - JustWatch availability [yellow](slower)[/yellow]

    [bold yellow]Common usage:[/bold yellow]
        [dim]# Quick start (recommended for first use)[/dim]
        prunarr cache init

        [dim]# Full cache with episodes and streaming[/dim]
        prunarr cache init [green]-e -t[/green]

        [dim]# Only movies and series (skip watch history)[/dim]
        prunarr cache init [green]--no-history[/green]

        [dim]# Only watch history (for history commands)[/dim]
        prunarr cache init [green]--no-movies --no-series[/green]

        [dim]# Cache with streaming availability check[/dim]
        prunarr cache init [green]-t[/green]

        [dim]# Verbose initialization with debug output[/dim]
        prunarr [blue]--debug[/blue] cache init [green]-e -t[/green]

    [bold yellow]Performance tips:[/bold yellow]
        • Start with default flags (movies, series, history) - fastest
        • Add [green]-e[/green] if you frequently use 'series get' command
        • Add [green]-t[/green] if you filter by streaming availability
        • Use 'cache refresh' to update data without manually clearing first
    """
    settings, debug, logger = _setup_context(ctx)
    prunarr = _validate_cache_enabled(settings, logger, debug)

    logger.info("Initializing PrunArr cache...")

    try:
        _perform_cache_init(prunarr, settings, logger, debug, movies, series, history, episodes, streaming)

        # Show cache stats
        stats = prunarr.cache_manager.get_stats()
        console.print(f"\n[bold green]✓ Cache initialized![/bold green] Size: {stats['size_mb']} MB")
        console.print(f"  Cache location: {stats['cache_dir']}")
    except Exception as e:
        logger.error(f"Failed to initialize cache: {str(e)}")
        raise typer.Exit(1)


@app.command("status")
def cache_status(
    ctx: typer.Context,
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]Show cache status and statistics.[/bold cyan]

    Displays comprehensive information about the current cache including size,
    location, number of cached items, and performance metrics (hit/miss statistics).

    [bold yellow]Output formats:[/bold yellow]
        • [cyan]table[/cyan] (default) - Human-readable table with colored output
        • [cyan]json[/cyan] - Machine-readable JSON for scripting/automation

    [bold yellow]What's displayed:[/bold yellow]
        • Cache status (enabled/disabled)
        • Cache directory location
        • Total cache size in MB
        • Number of cached files
        • Cache hits and misses
        • Hit rate percentage (higher = better performance)
        • Last accessed timestamp
        • TTL (time-to-live) settings for each cache type

    [bold yellow]Examples:[/bold yellow]
        [dim]# Show cache status (default table format)[/dim]
        prunarr cache status

        [dim]# Get status as JSON for scripting[/dim]
        prunarr cache status [green]--output json[/green]

        [dim]# Check cache size and hit rate[/dim]
        prunarr cache status | grep -E "(Total Size|Hit Rate)"

    [bold yellow]Interpreting results:[/bold yellow]
        • Hit rate > 80% = Excellent (cache is very effective)
        • Hit rate 50-80% = Good (cache is helping performance)
        • Hit rate < 50% = Consider running 'cache refresh'
    """
    settings, debug, logger = _setup_context(ctx)
    validate_output_format(output, logger)

    prunarr = _validate_cache_enabled(settings, logger, debug, require_enabled=False)
    if not prunarr:
        return

    try:
        stats = prunarr.cache_manager.get_stats()
        total_requests = stats.get("hits", 0) + stats.get("misses", 0)
        hit_rate = (stats.get("hits", 0) / total_requests * 100) if total_requests > 0 else 0

        if output == "json":
            last_accessed = stats.get("last_accessed", 0)
            json_output = {
                "enabled": stats.get("enabled"),
                "cache_dir": str(stats.get("cache_dir", "")),
                "size_mb": stats.get("size_mb", 0),
                "file_count": stats.get("file_count", 0),
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "hit_rate_percentage": round(hit_rate, 1),
                "last_accessed": datetime.fromtimestamp(last_accessed).isoformat() if last_accessed else None,
                "ttl_settings": {
                    "movies_seconds": settings.cache_ttl_movies,
                    "series_seconds": settings.cache_ttl_series,
                    "history_seconds": settings.cache_ttl_history,
                },
            }
            print(json.dumps(json_output, indent=2))
        else:
            table = Table(title="Cache Status", show_header=False)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Status", "[green]Enabled[/green]" if stats["enabled"] else "[red]Disabled[/red]")
            table.add_row("Cache Directory", str(stats.get("cache_dir", "N/A")))
            table.add_row("Total Size", f"{stats.get('size_mb', 0)} MB")
            table.add_row("Cached Files", str(stats.get("file_count", 0)))
            table.add_row("Cache Hits", str(stats.get("hits", 0)))
            table.add_row("Cache Misses", str(stats.get("misses", 0)))
            table.add_row("Hit Rate", f"{hit_rate:.1f}%")

            if last_accessed := stats.get("last_accessed", 0):
                last_accessed_dt = datetime.fromtimestamp(last_accessed)
                table.add_row("Last Accessed", last_accessed_dt.strftime("%Y-%m-%d %H:%M:%S"))

            console.print(table)
            logger.info(
                f"TTL Settings: Movies={settings.cache_ttl_movies}s, "
                f"Series={settings.cache_ttl_series}s, "
                f"History={settings.cache_ttl_history}s"
            )
    except Exception as e:
        logger.error(f"Failed to get cache status: {str(e)}")
        raise typer.Exit(1)


@app.command("clear")
def clear_cache(
    ctx: typer.Context,
    movies: bool = typer.Option(False, "--movies/--no-movies", "-m", help="Clear movies cache"),
    series: bool = typer.Option(False, "--series/--no-series", "-s", help="Clear series cache"),
    history: bool = typer.Option(False, "--history/--no-history", "-h", help="Clear history cache"),
    tags: bool = typer.Option(False, "--tags/--no-tags", help="Clear tags cache"),
    metadata: bool = typer.Option(False, "--metadata/--no-metadata", help="Clear metadata cache"),
    episodes: bool = typer.Option(False, "--episodes/--no-episodes", "-e", help="Clear episodes cache"),
    streaming: bool = typer.Option(False, "--streaming/--no-streaming", "-t", help="Clear streaming cache"),
    all_cache: bool = typer.Option(False, "--all", "-a", help="Clear all cache"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    [bold cyan]Clear cached data.[/bold cyan]

    Removes cached data to free up disk space or prepare for refresh. By default,
    prompts for confirmation before clearing to prevent accidental data loss.

    [bold yellow]What can be cleared:[/bold yellow]
        • [cyan]Movies[/cyan] (-m/--movies) - Radarr movie library data
        • [cyan]Series[/cyan] (-s/--series) - Sonarr series library data
        • [cyan]History[/cyan] (-h/--history) - Tautulli watch history records
        • [cyan]Tags[/cyan] (--tags) - Movie/series tags
        • [cyan]Metadata[/cyan] (--metadata) - IMDB/TVDB metadata
        • [cyan]Episodes[/cyan] (-e/--episodes) - Episode file data
        • [cyan]Streaming[/cyan] (-t/--streaming) - JustWatch availability data
        • [cyan]All[/cyan] (-a/--all) - Everything (resets statistics)

    [bold yellow]Dependencies:[/bold yellow]
        • Clearing [cyan]series[/cyan] also clears [cyan]episodes[/cyan]
        • Clearing [cyan]all[/cyan] clears everything and resets hit/miss statistics

    [bold yellow]Examples:[/bold yellow]
        [dim]# Clear all cache (prompts for confirmation)[/dim]
        prunarr cache clear [green]--all[/green]

        [dim]# Clear all cache without confirmation[/dim]
        prunarr cache clear [green]-a -f[/green]

        [dim]# Clear only movies[/dim]
        prunarr cache clear [green]-m[/green]

        [dim]# Clear movies and series[/dim]
        prunarr cache clear [green]-m -s[/green]

        [dim]# Clear only streaming availability data[/dim]
        prunarr cache clear [green]-t --force[/green]

        [dim]# Clear history and metadata[/dim]
        prunarr cache clear [green]-h --metadata[/green]

    [bold yellow]Common workflows:[/bold yellow]
        • Want fresh data? Use 'cache refresh' instead (clears + re-fetches)
        • Low disk space? Clear streaming: [green]cache clear -t[/green]
        • Troubleshooting? Clear all: [green]cache clear -a -f && cache init[/green]
    """
    settings, debug, logger = _setup_context(ctx)
    prunarr = _validate_cache_enabled(settings, logger, debug, require_enabled=False)
    if not prunarr:
        return

    # Determine what to clear
    if not any([movies, series, history, tags, metadata, episodes, streaming, all_cache]):
        logger.warning("No cache types selected. Use flags like -m, -s, -h, or --all to specify what to clear.")
        logger.info("Run 'prunarr cache clear --help' for examples")
        raise typer.Exit(0)

    # Build confirmation message
    if not force:
        clear_items = []
        if all_cache:
            msg = "Clear ALL cache data and reset statistics?"
        else:
            if movies:
                clear_items.append("movies")
            if series:
                clear_items.append("series")
            if history:
                clear_items.append("history")
            if tags:
                clear_items.append("tags")
            if metadata:
                clear_items.append("metadata")
            if episodes:
                clear_items.append("episodes")
            if streaming:
                clear_items.append("streaming")
            msg = f"Clear {', '.join(clear_items)} cache?"

        if not typer.confirm(msg):
            logger.info("Cache clear cancelled")
            return

    try:
        _clear_cache_types(
            prunarr, logger,
            movies=movies,
            series=series,
            history=history,
            tags=tags,
            metadata=metadata,
            episodes=episodes,
            streaming=streaming,
            all_cache=all_cache,
        )
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise typer.Exit(1)


@app.command("refresh")
def refresh_cache(
    ctx: typer.Context,
    movies: bool = typer.Option(True, "--movies/--no-movies", "-m", help="Refresh movies data (default: True)"),
    series: bool = typer.Option(True, "--series/--no-series", "-s", help="Refresh series data (default: True)"),
    history: bool = typer.Option(True, "--history/--no-history", "-h", help="Refresh watch history (default: True)"),
    episodes: bool = typer.Option(False, "--episodes/--no-episodes", "-e", help="Refresh ALL episodes for each series (slower)"),
    streaming: bool = typer.Option(
        False,
        "--streaming/--no-streaming",
        "-t",
        help="Refresh streaming availability for all movies and series (requires streaming_enabled=true)",
    ),
):
    """
    [bold cyan]Refresh cached data.[/bold cyan]

    Clears and immediately refetches cached data to ensure it's up to date.
    This is equivalent to running 'cache clear' followed by 'cache init' with the same flags.

    Use this when you want to force-update cached data without manually clearing first,
    such as after adding new movies/series or when Tautulli history has been updated.

    [bold yellow]What gets refreshed:[/bold yellow]
        • [cyan]Radarr movies[/cyan] - All movie data (-m/--movies, default: on)
        • [cyan]Sonarr series[/cyan] - All series data (-s/--series, default: on)
        • [cyan]Tautulli watch history[/cyan] - All watch records (-h/--history, default: on)
        • [cyan]Tags[/cyan] - All movie and series tags (automatic when movies/series enabled)
        • [cyan]Metadata[/cyan] - Tautulli metadata (automatic when history enabled)
        • [cyan]Episodes[/cyan] - All episodes (-e/--episodes, default: off)
        • [cyan]Streaming[/cyan] - JustWatch availability (-t/--streaming, default: off)

    [bold yellow]Examples:[/bold yellow]
        [dim]# Refresh all default cache (movies, series, history, tags, metadata)[/dim]
        prunarr cache refresh

        [dim]# Refresh everything including episodes and streaming[/dim]
        prunarr cache refresh [green]-e[/green] [green]-t[/green]

        [dim]# Refresh only movies (skip series and history)[/dim]
        prunarr cache refresh [green]--no-series[/green] [green]--no-history[/green]

        [dim]# Refresh only watch history and metadata[/dim]
        prunarr cache refresh [green]--no-movies[/green] [green]--no-series[/green]

        [dim]# Refresh streaming availability after updating provider config[/dim]
        prunarr cache refresh [green]-t[/green]
    """
    settings, debug, logger = _setup_context(ctx)
    prunarr = _validate_cache_enabled(settings, logger, debug)

    # Determine what to clear
    clear_items = []
    if movies:
        clear_items.append("movies")
    if series:
        clear_items.append("series")
    if history:
        clear_items.append("history")

    if not clear_items:
        logger.warning("No data types selected for refresh. Use --movies, --series, or --history flags.")
        raise typer.Exit(0)

    logger.info(f"Refreshing cache for: {', '.join(clear_items)}...")

    try:
        # Clear selected cache types (with dependencies)
        # Note: Episodes are cleared automatically with series
        _clear_cache_types(
            prunarr, logger,
            movies=movies,
            series=series,  # This also clears episodes
            history=history,
            tags=(movies or series),  # Tags depend on movies/series
            metadata=history,  # Metadata depends on history
            streaming=streaming,  # Clear streaming if requested
        )
        console.print()  # Add blank line for spacing

        # Re-initialize with the same flags
        _perform_cache_init(prunarr, settings, logger, debug, movies, series, history, episodes, streaming)

        # Show cache stats
        stats = prunarr.cache_manager.get_stats()
        console.print(f"\n[bold green]✓ Cache refreshed![/bold green] Size: {stats['size_mb']} MB")
        console.print(f"  Cache location: {stats['cache_dir']}")

        logger.info("Cache refresh complete")
    except Exception as e:
        logger.error(f"Failed to refresh cache: {str(e)}")
        raise typer.Exit(1)
