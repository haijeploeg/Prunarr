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
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)

from prunarr.config import Settings
from prunarr.logger import get_logger
from prunarr.prunarr import PrunArr
from prunarr.utils.validators import validate_output_format
from prunarr.utils.serializers import prepare_datetime_for_json

app = typer.Typer(help="Manage PrunArr cache.", rich_markup_mode="rich")
console = Console()


@app.command("init")
def init_cache(
    ctx: typer.Context,
    full: bool = typer.Option(
        False,
        "--full",
        "-f",
        help="Pre-fetch ALL data including episodes for each series (slower, but fully cached)",
    ),
):
    """
    [bold cyan]Initialize PrunArr cache with all data.[/bold cyan]

    Pre-populates the cache with data from Radarr, Sonarr, and Tautulli to
    improve performance for subsequent commands.

    [bold yellow]What gets cached:[/bold yellow]
        • [cyan]Radarr movies[/cyan] - All movie data
        • [cyan]Sonarr series[/cyan] - All series data
        • [cyan]Tautulli watch history[/cyan] - All watch records
        • [cyan]Tags[/cyan] - All movie and series tags
        • [cyan]Episodes[/cyan] - All episodes (only with --full flag)

    [bold yellow]Cache modes:[/bold yellow]
        • [green]Default[/green] - Fast init, episodes cached on-demand
        • [green]--full[/green] - Complete init, everything pre-cached (slower)

    [bold yellow]Examples:[/bold yellow]
        [dim]# Quick initialization (recommended)[/dim]
        prunarr cache init

        [dim]# Full initialization with all episodes[/dim]
        prunarr cache init [green]--full[/green]

        [dim]# Initialize with debug output[/dim]
        prunarr[blue]--debug[/blue] cache init
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("cache", debug=debug, log_level=settings.log_level)

    if not settings.cache_enabled:
        logger.error("Caching is disabled in configuration. Set cache_enabled=true to use caching.")
        raise typer.Exit(1)

    logger.info("Initializing PrunArr cache...")
    prunarr = PrunArr(settings, debug=debug)

    if not prunarr.cache_manager:
        logger.error("Cache manager not available")
        raise typer.Exit(1)

    try:
        # Phase 1: Fetch main data (movies, series, history) in parallel
        logger.info("Fetching movies, series, and watch history...")
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            futures = {
                executor.submit(prunarr.radarr.get_movie): "movies",
                executor.submit(prunarr.sonarr.get_series): "series",
                executor.submit(prunarr.tautulli.get_watch_history, page_size=1000): "history",
            }

            # Process results as they complete
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    results[task_name] = result

                    # Log immediately as each completes
                    if task_name == "movies":
                        logger.info(f"Cached {len(result)} movies")
                    elif task_name == "series":
                        logger.info(f"Cached {len(result)} series")
                    elif task_name == "history":
                        logger.info(f"Cached {len(result)} watch history records")
                except Exception as e:
                    logger.error(f"Failed to cache {task_name}: {str(e)}")

        # Phase 2: Pre-fetch all tags for movies and series
        tag_ids = set()

        # Collect all tag IDs from movies and series
        if "movies" in results:
            for movie in results["movies"]:
                tag_ids.update(movie.get("tags", []))

        if "series" in results:
            for series_item in results["series"]:
                tag_ids.update(series_item.get("tags", []))

        if tag_ids:
            logger.info(f"Fetching {len(tag_ids)} tags...")
            cached_tags = 0

            with ThreadPoolExecutor(max_workers=10) as tag_executor:
                # Submit tag fetch tasks
                tag_futures = {
                    tag_executor.submit(prunarr.radarr.get_tag, tag_id): tag_id
                    for tag_id in tag_ids
                }

                # Wait for all tag fetches to complete
                for tag_future in as_completed(tag_futures):
                    try:
                        tag_future.result()
                        cached_tags += 1
                    except Exception:
                        # Continue on error, some tags might not exist
                        pass

            logger.info(f"Cached {cached_tags} tags")

        # Phase 3: Pre-fetch metadata for watch history (needed by series list)
        if "history" in results:
            logger.info("Fetching metadata for watch history...")

            # Extract unique rating keys from history
            unique_rating_keys = set()
            for record in results["history"]:
                # For episodes, we need the grandparent (series) rating key
                grandparent_key = record.get("grandparent_rating_key")
                if grandparent_key:
                    unique_rating_keys.add(str(grandparent_key))
                # For movies, we need the rating key
                rating_key = record.get("rating_key")
                if rating_key:
                    unique_rating_keys.add(str(rating_key))

            if unique_rating_keys:
                cached_metadata = 0
                with ThreadPoolExecutor(max_workers=10) as meta_executor:
                    # Submit metadata fetch tasks
                    meta_futures = {
                        meta_executor.submit(prunarr.tautulli.get_metadata, rating_key): rating_key
                        for rating_key in unique_rating_keys
                    }

                    # Wait for all metadata fetches to complete
                    for meta_future in as_completed(meta_futures):
                        try:
                            meta_future.result()
                            cached_metadata += 1
                        except Exception:
                            # Continue on error
                            pass

                logger.info(f"Cached {cached_metadata} metadata records")

        # Phase 4: Pre-fetch all episodes if --full flag is used
        if full and "series" in results:
            # Get all series IDs
            series_ids = [s.get("id") for s in results["series"] if s.get("id")]

            if series_ids:
                logger.info(f"Fetching episodes for {len(series_ids)} series (full mode)...")
                cached_episodes = 0
                total_episodes = 0

                with ThreadPoolExecutor(max_workers=5) as ep_executor:
                    # Submit episode fetch tasks
                    ep_futures = {
                        ep_executor.submit(
                            prunarr.sonarr.get_episodes_by_series_id, series_id
                        ): series_id
                        for series_id in series_ids
                    }

                    # Wait for all episode fetches to complete
                    for ep_future in as_completed(ep_futures):
                        try:
                            episodes = ep_future.result()
                            cached_episodes += 1
                            total_episodes += len(episodes)
                        except Exception:
                            # Continue on error
                            pass

                logger.info(f"Cached {total_episodes} episodes across {cached_episodes} series")

        # Show cache stats
        stats = prunarr.cache_manager.get_stats()
        logger.info(f"Cache initialized! Size: {stats['size_mb']} MB")
        logger.info(f"Cache location: {stats['cache_dir']}")

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

    Displays information about the current cache including size, location,
    number of cached items, and hit/miss statistics.

    [bold yellow]Examples:[/bold yellow]
        [dim]# Show cache status[/dim]
        prunarr cache status
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("cache", debug=debug, log_level=settings.log_level)

    # Validate output format using shared validator
    validate_output_format(output, logger)

    if not settings.cache_enabled:
        logger.warning("Caching is disabled in configuration")
        return

    prunarr = PrunArr(settings, debug=debug)

    if not prunarr.cache_manager:
        logger.error("Cache manager not available")
        raise typer.Exit(1)

    try:
        stats = prunarr.cache_manager.get_stats()

        # Calculate hit rate
        total_requests = stats.get("hits", 0) + stats.get("misses", 0)
        hit_rate = (stats.get("hits", 0) / total_requests * 100) if total_requests > 0 else 0

        # Output based on format
        if output == "json":
            # Prepare JSON-serializable data
            json_output = {
                "enabled": stats.get("enabled"),
                "cache_dir": str(stats.get("cache_dir", "")),
                "size_mb": stats.get("size_mb", 0),
                "file_count": stats.get("file_count", 0),
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "hit_rate_percentage": round(hit_rate, 1),
                "ttl_settings": {
                    "movies_seconds": settings.cache_ttl_movies,
                    "series_seconds": settings.cache_ttl_series,
                    "history_seconds": settings.cache_ttl_history,
                },
            }

            # Parse last accessed
            last_accessed = stats.get("last_accessed", 0)
            if last_accessed:
                last_accessed_dt = datetime.fromtimestamp(last_accessed)
                json_output["last_accessed"] = last_accessed_dt.isoformat()
            else:
                json_output["last_accessed"] = None

            print(json.dumps(json_output, indent=2))
        else:
            # Create status table
            table = Table(title="Cache Status", show_header=False)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row(
                "Status", "[green]Enabled[/green]" if stats["enabled"] else "[red]Disabled[/red]"
            )
            table.add_row("Cache Directory", str(stats.get("cache_dir", "N/A")))
            table.add_row("Total Size", f"{stats.get('size_mb', 0)} MB")
            table.add_row("Cached Files", str(stats.get("file_count", 0)))
            table.add_row("Cache Hits", str(stats.get("hits", 0)))
            table.add_row("Cache Misses", str(stats.get("misses", 0)))
            table.add_row("Hit Rate", f"{hit_rate:.1f}%")

            # Last accessed
            last_accessed = stats.get("last_accessed", 0)
            if last_accessed:
                last_accessed_dt = datetime.fromtimestamp(last_accessed)
                table.add_row("Last Accessed", last_accessed_dt.strftime("%Y-%m-%d %H:%M:%S"))

            console.print(table)

            # Show TTL settings
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
    cache_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Cache type to clear (movies, series, history, tags, metadata, all)",
    ),
    expired_only: bool = typer.Option(False, "--expired", help="Clear only expired entries"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    [bold cyan]Clear cached data.[/bold cyan]

    Removes cached data to free up space or force refresh. By default,
    prompts for confirmation before clearing.

    [bold yellow]Cache types:[/bold yellow]
        • [cyan]movies[/cyan] - Radarr movie data
        • [cyan]series[/cyan] - Sonarr series data
        • [cyan]history[/cyan] - Tautulli watch history
        • [cyan]tags[/cyan] - Radarr/Sonarr tags
        • [cyan]metadata[/cyan] - IMDB/TVDB metadata
        • [cyan]all[/cyan] - All cached data

    [bold yellow]Examples:[/bold yellow]
        [dim]# Clear all cache (with confirmation)[/dim]
        prunarr cache clear --type all

        [dim]# Clear only history cache without confirmation[/dim]
        prunarr cache clear --type history --force

        [dim]# Clear only expired entries[/dim]
        prunarr cache clear --expired
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("cache", debug=debug, log_level=settings.log_level)

    if not settings.cache_enabled:
        logger.warning("Caching is disabled in configuration")
        return

    prunarr = PrunArr(settings, debug=debug)

    if not prunarr.cache_manager:
        logger.error("Cache manager not available")
        raise typer.Exit(1)

    # Confirm before clearing
    if not force:
        if cache_type:
            msg = f"Clear {cache_type} cache?"
        elif expired_only:
            msg = "Clear expired cache entries?"
        else:
            msg = "Clear all cache?"

        if not typer.confirm(msg):
            logger.info("Cache clear cancelled")
            return

    try:
        # Clear based on type
        if expired_only:
            logger.warning("Expired-only clearing not yet implemented, clearing by type instead")

        if cache_type == "movies":
            prunarr.cache_manager.clear_movies()
            logger.info("Cleared movies cache")
        elif cache_type == "series":
            prunarr.cache_manager.clear_series()
            logger.info("Cleared series cache")
        elif cache_type == "history":
            prunarr.cache_manager.clear_history()
            logger.info("Cleared history cache")
        elif cache_type == "tags":
            prunarr.cache_manager.clear_tags()
            logger.info("Cleared tags cache")
        elif cache_type == "metadata":
            prunarr.cache_manager.clear_metadata()
            logger.info("Cleared metadata cache")
        elif cache_type == "all" or cache_type is None:
            prunarr.cache_manager.clear_all()
            logger.info("Cleared all cache")
        else:
            logger.error(f"Unknown cache type: {cache_type}")
            logger.info("Valid types: movies, series, history, tags, metadata, all")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise typer.Exit(1)


@app.command("refresh")
def refresh_cache(
    ctx: typer.Context,
    cache_type: str = typer.Option(
        "all", "--type", "-t", help="Cache type to refresh (history, all)"
    ),
):
    """
    [bold cyan]Refresh cached data.[/bold cyan]

    Clears and immediately refetches cached data to ensure it's up to date.

    [bold yellow]Examples:[/bold yellow]
        [dim]# Refresh all cache[/dim]
        prunarr cache refresh

        [dim]# Refresh only history[/dim]
        prunarr cache refresh --type history
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("cache", debug=debug, log_level=settings.log_level)

    if not settings.cache_enabled:
        logger.error("Caching is disabled in configuration")
        raise typer.Exit(1)

    prunarr = PrunArr(settings, debug=debug)

    if not prunarr.cache_manager:
        logger.error("Cache manager not available")
        raise typer.Exit(1)

    try:
        logger.info(f"Refreshing {cache_type} cache...")

        # Clear first
        if cache_type == "history":
            prunarr.cache_manager.clear_history()
        elif cache_type == "all":
            prunarr.cache_manager.clear_all()
        else:
            logger.error(f"Unknown cache type: {cache_type}")
            raise typer.Exit(1)

        # Refetch based on type
        if cache_type == "history":
            logger.info("Refreshing watch history...")
            history = prunarr.tautulli.get_watch_history(page_size=1000)
            logger.info(f"Refreshed watch history ({len(history)} records)")
        elif cache_type == "all":
            logger.info("Refreshing all cache data...")
            results = {}

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(prunarr.radarr.get_movie): "movies",
                    executor.submit(prunarr.sonarr.get_series): "series",
                    executor.submit(prunarr.tautulli.get_watch_history, page_size=1000): "history",
                }

                for future in as_completed(futures):
                    task_name = futures[future]
                    try:
                        result = future.result()
                        results[task_name] = result

                        # Log immediately as each completes
                        if task_name == "movies":
                            logger.info(f"Refreshed {len(result)} movies")
                        elif task_name == "series":
                            logger.info(f"Refreshed {len(result)} series")
                        elif task_name == "history":
                            logger.info(f"Refreshed {len(result)} watch history records")
                    except Exception as e:
                        logger.error(f"Failed to refresh {task_name}: {str(e)}")

            # Phase 2: Pre-fetch all tags for movies and series
            tag_ids = set()

            # Collect all tag IDs from movies and series
            if "movies" in results:
                for movie in results["movies"]:
                    tag_ids.update(movie.get("tags", []))

            if "series" in results:
                for series_item in results["series"]:
                    tag_ids.update(series_item.get("tags", []))

            if tag_ids:
                logger.info(f"Fetching {len(tag_ids)} tags...")
                cached_tags = 0

                with ThreadPoolExecutor(max_workers=10) as tag_executor:
                    # Submit tag fetch tasks
                    tag_futures = {
                        tag_executor.submit(prunarr.radarr.get_tag, tag_id): tag_id
                        for tag_id in tag_ids
                    }

                    # Wait for all tag fetches to complete
                    for tag_future in as_completed(tag_futures):
                        try:
                            tag_future.result()
                            cached_tags += 1
                        except Exception:
                            # Continue on error, some tags might not exist
                            pass

                logger.info(f"Cached {cached_tags} tags")

            # Phase 3: Pre-fetch metadata for watch history (needed by series list)
            if "history" in results:
                logger.info("Fetching metadata for watch history...")

                # Extract unique rating keys from history
                unique_rating_keys = set()
                for record in results["history"]:
                    # For episodes, we need the grandparent (series) rating key
                    grandparent_key = record.get("grandparent_rating_key")
                    if grandparent_key:
                        unique_rating_keys.add(str(grandparent_key))
                    # For movies, we need the rating key
                    rating_key = record.get("rating_key")
                    if rating_key:
                        unique_rating_keys.add(str(rating_key))

                if unique_rating_keys:
                    cached_metadata = 0
                    with ThreadPoolExecutor(max_workers=10) as meta_executor:
                        # Submit metadata fetch tasks
                        meta_futures = {
                            meta_executor.submit(
                                prunarr.tautulli.get_metadata, rating_key
                            ): rating_key
                            for rating_key in unique_rating_keys
                        }

                        # Wait for all metadata fetches to complete
                        for meta_future in as_completed(meta_futures):
                            try:
                                meta_future.result()
                                cached_metadata += 1
                            except Exception:
                                # Continue on error
                                pass

                    logger.info(f"Cached {cached_metadata} metadata records")

        logger.info("Cache refresh complete")

    except Exception as e:
        logger.error(f"Failed to refresh cache: {str(e)}")
        raise typer.Exit(1)
