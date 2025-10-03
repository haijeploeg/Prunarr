"""
Movies command module for PrunArr CLI.

This module provides commands for managing movies in Radarr,
including listing with advanced filtering, watch status tracking, and removal capabilities.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console

from prunarr.config import Settings
from prunarr.justwatch import JustWatchClient
from prunarr.logger import get_logger
from prunarr.prunarr import PrunArr
from prunarr.utils import (
    format_date_or_default,
    format_file_size,
    format_movie_watch_status,
    safe_get,
)
from prunarr.utils.parsers import parse_file_size, parse_iso_datetime
from prunarr.utils.serializers import prepare_datetime_for_json, prepare_movie_for_json
from prunarr.utils.tables import create_movies_table
from prunarr.utils.validators import validate_output_format, validate_sort_option

console = Console()
app = typer.Typer(help="Manage movies in Radarr.", rich_markup_mode="rich")


def sort_movies(
    movies: List[Dict[str, Any]], sort_by: str, desc: bool = False
) -> List[Dict[str, Any]]:
    """
    Sort movies by specified criteria.

    Args:
        movies: List of movie dictionaries
        sort_by: Sort criteria (title, date, filesize, watched_date)
        desc: Sort in descending order

    Returns:
        Sorted list of movies
    """

    def get_sort_key(movie):
        if sort_by == "title":
            return movie.get("title", "").lower()
        elif sort_by == "date":
            # Sort by added date
            added = movie.get("added")
            return parse_iso_datetime(added) or datetime.min
        elif sort_by == "filesize":
            return movie.get("file_size", 0)
        elif sort_by == "watched_date":
            watched_at = movie.get("watched_at")
            return watched_at if watched_at else datetime.min
        elif sort_by == "days_watched":
            days_since = movie.get("days_since_watched")
            return days_since if days_since is not None else 0
        else:
            return movie.get("title", "").lower()

    return sorted(movies, key=get_sort_key, reverse=desc)


def validate_and_parse_options(sort_by: str, min_filesize: Optional[str], logger) -> tuple:
    """
    Validate and parse common options used by both list and remove commands.

    Args:
        sort_by: Sort option to validate
        min_filesize: File size string to parse
        logger: Logger instance for error reporting

    Returns:
        Tuple of (valid_sort_by, min_filesize_bytes)

    Raises:
        typer.Exit: If validation fails
    """
    # Validate sort_by parameter using shared validator
    valid_sort_options = ["title", "date", "filesize", "watched_date", "days_watched"]
    validate_sort_option(sort_by, valid_sort_options, logger, "sort option")

    # Parse minimum file size if provided
    min_filesize_bytes = None
    if min_filesize:
        try:
            min_filesize_bytes = parse_file_size(min_filesize)
        except ValueError as e:
            logger.error(f"Invalid file size format: {e}")
            raise typer.Exit(1)

    return sort_by, min_filesize_bytes


def _matches_watch_status_filter(
    movie_status: str, watched_only: bool, unwatched_only: bool, watched_by_other_only: bool
) -> bool:
    """Check if movie matches watch status filters (helper)."""
    if not (watched_only or unwatched_only or watched_by_other_only):
        return True

    return (
        (watched_only and movie_status == "watched")
        or (unwatched_only and movie_status == "unwatched")
        or (watched_by_other_only and movie_status == "watched_by_other")
    )


def _meets_days_watched_requirement(movie: Dict[str, Any], days_watched: Optional[int]) -> bool:
    """Check if movie meets days watched requirement (helper)."""
    if days_watched is None:
        return True

    days_since = movie.get("days_since_watched")
    return days_since is not None and days_since >= days_watched


def _meets_filesize_requirement(movie: Dict[str, Any], min_filesize_bytes: Optional[int]) -> bool:
    """Check if movie meets filesize requirement (helper)."""
    if min_filesize_bytes is None:
        return True

    return movie.get("file_size", 0) >= min_filesize_bytes


def apply_movie_filters(
    movies: List[Dict[str, Any]],
    watched_only: bool = False,
    unwatched_only: bool = False,
    watched_by_other_only: bool = False,
    days_watched: Optional[int] = None,
    min_filesize_bytes: Optional[int] = None,
    include_untagged: bool = True,
    remove_mode: bool = False,
) -> List[Dict[str, Any]]:
    """
    Apply filtering logic to movies list.

    Args:
        movies: List of movies to filter
        watched_only: Show only watched movies
        unwatched_only: Show only unwatched movies
        watched_by_other_only: Show only movies watched by others
        days_watched: Minimum days since watched
        min_filesize_bytes: Minimum file size in bytes
        include_untagged: Include movies without user tags
        remove_mode: If True, applies remove-specific filtering (only "watched" status)

    Returns:
        Filtered list of movies
    """
    filtered_movies = []

    for movie in movies:
        # For remove mode, only consider movies watched by the correct user
        if remove_mode:
            if movie.get("watch_status") != "watched" or not _meets_days_watched_requirement(
                movie, days_watched
            ):
                continue
        else:
            # Apply watch status and days watched filters for list mode
            if not _matches_watch_status_filter(
                movie.get("watch_status", ""), watched_only, unwatched_only, watched_by_other_only
            ):
                continue

            if not _meets_days_watched_requirement(movie, days_watched):
                continue

        # File size filtering (common to both modes)
        if not _meets_filesize_requirement(movie, min_filesize_bytes):
            continue

        filtered_movies.append(movie)

    return filtered_movies


def create_debug_filter_info(
    username: Optional[str] = None,
    watched_only: bool = False,
    unwatched_only: bool = False,
    watched_by_other_only: bool = False,
    days_watched: Optional[int] = None,
    min_filesize: Optional[str] = None,
    include_untagged: bool = True,
    sort_by: str = "title",
    sort_desc: bool = False,
    limit: Optional[int] = None,
) -> str:
    """
    Create debug information string about applied filters.

    Returns:
        Formatted string describing all applied filters
    """
    filters = []

    if username:
        filters.append(f"username={username}")

    # Watch status filters (for list mode)
    watch_status_filters = []
    if watched_only:
        watch_status_filters.append("watched")
    if unwatched_only:
        watch_status_filters.append("unwatched")
    if watched_by_other_only:
        watch_status_filters.append("watched_by_other")
    if watch_status_filters:
        filters.append(f"watch_status=[{', '.join(watch_status_filters)}]")

    if days_watched is not None:
        filters.append(f"days_watched>={days_watched}")
    if min_filesize:
        filters.append(f"min_filesize={min_filesize}")
    if not include_untagged:
        filters.append("exclude_untagged=True")

    sort_info = f"sort_by={sort_by}"
    if sort_desc:
        sort_info += "_desc"
    else:
        sort_info += "_asc"
    filters.append(sort_info)

    if limit:
        filters.append(f"limit={limit}")

    return ", ".join(filters) if filters else "none"


@app.command("list")
def list_movies(
    ctx: typer.Context,
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Filter by specific username"
    ),
    watched_only: bool = typer.Option(False, "--watched", "-w", help="Show only watched movies"),
    unwatched_only: bool = typer.Option(False, "--unwatched", help="Show only unwatched movies"),
    watched_by_other_only: bool = typer.Option(
        False,
        "--watched-by-other",
        help="Show only movies watched by someone other than the requester",
    ),
    include_untagged: bool = typer.Option(
        True, "--include-untagged/--exclude-untagged", help="Include movies without user tags"
    ),
    days_watched: Optional[int] = typer.Option(
        None, "--days-watched", "-d", help="Show movies watched more than X days ago"
    ),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    sort_by: Optional[str] = typer.Option(
        "title",
        "--sort-by",
        "-s",
        help="Sort by: title, date, filesize, watched_date (default: title)",
    ),
    sort_desc: bool = typer.Option(
        False, "--desc", help="Sort in descending order (default: ascending)"
    ),
    min_filesize: Optional[str] = typer.Option(
        None, "--min-filesize", help="Minimum file size (e.g., '1GB', '500MB', '2.5GB')"
    ),
    on_streaming: bool = typer.Option(
        False, "--on-streaming", help="Show ONLY movies available on configured streaming providers"
    ),
    not_on_streaming: bool = typer.Option(
        False, "--not-on-streaming", help="Show ONLY movies NOT available on streaming providers"
    ),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]List movies in Radarr with advanced filtering options.[/bold cyan]

    Displays a formatted table of movies with detailed information including
    watch status, file information, and user assignments.

    [bold yellow]Table columns:[/bold yellow]
        • [cyan]Title[/cyan] and [cyan]Year[/cyan] - movie information
        • [cyan]User[/cyan] - who requested the movie (or "[dim]Untagged[/dim]")
        • [cyan]Watch Status[/cyan] - watched/unwatched status with colors
        • [cyan]Watched By[/cyan] - who actually watched it
        • [cyan]Days Ago[/cyan] - days since last watched
        • [cyan]File Size[/cyan] - downloaded file size
        • [cyan]Added[/cyan] - when added to Radarr

    [bold yellow]Filtering options:[/bold yellow]
        • [green]--username[/green] - filter by specific user
        • [green]--watched[/green] - show only watched movies
        • [green]--unwatched[/green] - show only unwatched movies
        • [green]--watched-by-other[/green] - show only movies watched by someone other than requester
        • [green]--days-watched[/green] - movies watched X+ days ago
        • [green]--include-untagged/--exclude-untagged[/green] - control untagged movies
        • [green]--min-filesize[/green] - minimum file size (e.g., '1GB', '500MB')
        • [green]--on-streaming[/green] - show ONLY movies available on streaming providers
        • [green]--not-on-streaming[/green] - show ONLY movies NOT available on streaming
        • [green]--limit[/green] - limit number of results

    [bold yellow]Sorting options:[/bold yellow]
        • [green]--sort-by[/green] - sort by: title (default), date, filesize, watched_date
        • [green]--desc[/green] - sort in descending order (default: ascending)

    [bold yellow]Examples:[/bold yellow]
        [dim]# List all movies with watch status[/dim]
        prunarr movies list

        [dim]# Show watched movies for specific user[/dim]
        prunarr movies list [green]--username[/green] "john" [green]--watched[/green]

        [dim]# Find movies ready for cleanup (watched 30+ days ago)[/dim]
        prunarr movies list [green]--days-watched[/green] 30

        [dim]# Show unwatched movies excluding untagged[/dim]
        prunarr movies list [green]--unwatched[/green] [green]--exclude-untagged[/green]

        [dim]# Find movies watched by other people but not the requester[/dim]
        prunarr movies list [green]--watched-by-other[/green]

        [dim]# Show both watched and unwatched (exclude watched-by-other)[/dim]
        prunarr movies list [green]--watched[/green] [green]--unwatched[/green]

        [dim]# Find large files sorted by size (biggest first)[/dim]
        prunarr movies list [green]--min-filesize[/green] 2GB [green]--sort-by[/green] filesize [green]--desc[/green]

        [dim]# Recent movies sorted by date added[/dim]
        prunarr movies list [green]--sort-by[/green] date [green]--desc[/green] [green]--limit[/green] 20

        [dim]# Show movies available on configured streaming providers[/dim]
        prunarr movies list [green]--on-streaming[/green]

        [dim]# Show movies NOT available on streaming (unique content)[/dim]
        prunarr movies list [green]--not-on-streaming[/green]

        [dim]# Find large files that are streamable[/dim]
        prunarr movies list [green]--on-streaming[/green] [green]--min-filesize[/green] 5GB

        [dim]# Get latest 10 movies with debug info[/dim]
        prunarr[blue]--debug[/blue] movies list [green]--limit[/green] 10
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("movies", debug=debug, log_level=settings.log_level)

    # Validate output format using shared validator
    validate_output_format(output, logger)

    # Validate streaming filter mutual exclusivity
    if on_streaming and not_on_streaming:
        logger.error("Cannot use both --on-streaming and --not-on-streaming filters together")
        raise typer.Exit(1)

    # Validate and parse options
    sort_by, min_filesize_bytes = validate_and_parse_options(sort_by, min_filesize, logger)

    # Check if streaming filters are requested but not configured
    if (on_streaming or not_on_streaming) and not settings.streaming_enabled:
        logger.error(
            "Streaming filters require streaming_enabled=true in configuration. "
            "Please configure streaming_enabled, streaming_locale, and streaming_providers in your config."
        )
        raise typer.Exit(1)

    logger.info("Retrieving movies from Radarr with watch status...")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Always check streaming if enabled in config
        check_streaming = settings.streaming_enabled

        # Get movies with watch status (and populate streaming cache if needed)
        movies = prunarr.get_movies_with_watch_status(
            include_untagged=include_untagged,
            username_filter=username,
            check_streaming=check_streaming,
        )

        # Check and log cache status
        if prunarr.cache_manager:
            prunarr.check_and_log_cache_status(prunarr.cache_manager.KEY_RADARR_MOVIES, logger)

        # Apply filtering using shared function
        filtered_movies = apply_movie_filters(
            movies=movies,
            watched_only=watched_only,
            unwatched_only=unwatched_only,
            watched_by_other_only=watched_by_other_only,
            days_watched=days_watched,
            min_filesize_bytes=min_filesize_bytes,
            include_untagged=include_untagged,
            remove_mode=False,
        )

        # Apply streaming filters if requested - now using cached data!
        if on_streaming or not_on_streaming:
            from prunarr.services.streaming_checker import StreamingChecker

            logger.info("Filtering by streaming availability (using cached data)...")
            streaming_checker = StreamingChecker(
                locale=settings.streaming_locale,
                providers=settings.streaming_providers,
                cache_manager=prunarr.cache_manager,
                logger=logger,
            )

            streaming_filtered = []
            for movie in filtered_movies:
                # Try to use cached streaming_available field first
                is_available = movie.get("streaming_available")

                # If not in cache, check via API (and cache the result)
                if is_available is None:
                    is_available = streaming_checker.is_on_streaming(
                        media_type="movie",
                        title=movie.get("title", ""),
                        year=movie.get("year"),
                        imdb_id=movie.get("imdb_id"),
                    )

                # Apply the appropriate filter
                if on_streaming and is_available:
                    streaming_filtered.append(movie)
                elif not_on_streaming and not is_available:
                    streaming_filtered.append(movie)

            filtered_movies = streaming_filtered
            filter_type = "on streaming" if on_streaming else "not on streaming"
            logger.info(f"After streaming filter: {len(filtered_movies)} movies {filter_type}")

        # Apply sorting
        filtered_movies = sort_movies(filtered_movies, sort_by, sort_desc)

        # Apply limit after sorting
        if limit:
            filtered_movies = filtered_movies[:limit]

        if not filtered_movies:
            logger.warning("No movies found matching the specified criteria")
            return

        logger.info(f"Found {len(filtered_movies)} movies")

        # Output based on format
        if output == "json":
            # Prepare JSON-serializable data using shared serializer
            json_output = []
            for movie in filtered_movies:
                json_output.append(
                    {
                        "id": movie.get("id"),
                        "title": movie.get("title"),
                        "year": movie.get("year"),
                        "user": movie.get("user"),
                        "watch_status": movie.get("watch_status"),
                        "watched_by": movie.get("watched_by"),
                        "days_since_watched": movie.get("days_since_watched"),
                        "file_size_bytes": movie.get("file_size", 0),
                        "added": prepare_datetime_for_json(parse_iso_datetime(movie.get("added"))),
                        "most_recent_watch": prepare_datetime_for_json(
                            movie.get("most_recent_watch")
                        ),
                        "imdb_id": movie.get("imdb_id"),
                        "tmdb_id": movie.get("tmdb_id"),
                    }
                )
            print(json.dumps(json_output, indent=2))
        else:
            # Create Rich table using factory - always include streaming column
            table = create_movies_table(include_streaming=True)

            # Populate table
            for movie in filtered_movies:
                # Format user display
                user_display = movie.get("user") or "[dim]Untagged[/dim]"

                # Format days since watched
                days_ago = (
                    str(movie.get("days_since_watched", ""))
                    if movie.get("days_since_watched") is not None
                    else "N/A"
                )

                # Format watched by (handle multiple users)
                watched_by = movie.get("watched_by") or "N/A"

                # Format added date
                added_date = format_date_or_default(parse_iso_datetime(movie.get("added")))

                # Build row data
                row_data = [
                    safe_get(movie, "title"),
                    safe_get(movie, "year"),
                    user_display,
                    format_movie_watch_status(movie.get("watch_status", "unknown")),
                    watched_by,
                    days_ago,
                    format_file_size(movie.get("file_size", 0)),
                ]

                # Add streaming info - always show
                streaming_available = movie.get("streaming_available")
                if streaming_available is True:
                    streaming_display = "✓"
                elif streaming_available is False:
                    streaming_display = "✗"
                else:
                    streaming_display = "-"  # Not checked yet
                row_data.append(streaming_display)

                row_data.append(added_date)
                table.add_row(*row_data)

            console.print(table)

        # Log applied filters in debug mode
        if debug:
            filter_info = create_debug_filter_info(
                username=username,
                watched_only=watched_only,
                unwatched_only=unwatched_only,
                watched_by_other_only=watched_by_other_only,
                days_watched=days_watched,
                min_filesize=min_filesize,
                include_untagged=include_untagged,
                sort_by=sort_by,
                sort_desc=sort_desc,
                limit=limit,
            )
            logger.debug(f"Applied filters/sorting: {filter_info}")

    except Exception as e:
        logger.error(f"Failed to retrieve movies: {str(e)}")
        raise typer.Exit(1)


@app.command("remove")
def remove_movies(
    ctx: typer.Context,
    days_watched: int = typer.Option(
        60, "--days-watched", "-d", help="Remove movies watched more than X days ago (default: 60)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be removed without actually deleting"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Filter by specific username"
    ),
    min_filesize: Optional[str] = typer.Option(
        None, "--min-filesize", help="Minimum file size (e.g., '1GB', '500MB', '2.5GB')"
    ),
    sort_by: Optional[str] = typer.Option(
        "days_watched",
        "--sort-by",
        "-s",
        help="Sort by: title, date, filesize, days_watched (default: days_watched)",
    ),
    sort_desc: bool = typer.Option(
        True, "--sort-asc", help="Sort in ascending order (default: descending for days_watched)"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-l", help="Limit number of movies to process"
    ),
    include_untagged: bool = typer.Option(
        False,
        "--include-untagged/--exclude-untagged",
        help="Include movies without user tags (default: exclude untagged)",
    ),
    on_streaming: bool = typer.Option(
        False,
        "--on-streaming",
        help="Remove ONLY movies available on configured streaming providers",
    ),
    not_on_streaming: bool = typer.Option(
        False, "--not-on-streaming", help="Remove ONLY movies NOT available on streaming providers"
    ),
):
    """
    [bold cyan]Remove watched movies with advanced filtering and confirmation.[/bold cyan]

    Identifies and removes movies that have been watched by their requesting user
    for more than the specified number of days. Supports the same filtering and
    sorting options as the list command for precise control.

    [bold yellow]Safety features:[/bold yellow]
        • [cyan]--dry-run[/cyan] - preview what would be removed
        • [cyan]--force[/cyan] - skip confirmation prompts
        • Only removes movies watched by the same user who requested them
        • Interactive confirmation by default
        • Skips movies without user tags

    [bold yellow]Filtering options:[/bold yellow]
        • [green]--username[/green] - filter by specific user
        • [green]--days-watched[/green] - movies watched X+ days ago
        • [green]--min-filesize[/green] - minimum file size (e.g., '1GB', '500MB')
        • [green]--include-untagged/--exclude-untagged[/green] - control untagged movies
        • [green]--on-streaming[/green] - remove ONLY movies available on streaming providers
        • [green]--not-on-streaming[/green] - remove ONLY movies NOT available on streaming
        • [green]--limit[/green] - limit number of movies to process

    [bold yellow]Sorting options:[/bold yellow]
        • [green]--sort-by[/green] - sort by: title, date, filesize, days_watched (default)
        • [green]--sort-asc[/green] - sort ascending (default: descending for days_watched)

    [bold yellow]Examples:[/bold yellow]
        [dim]# Preview removal (safe dry run)[/dim]
        prunarr movies remove [green]--dry-run[/green]

        [dim]# Remove old large movies for specific user[/dim]
        prunarr movies remove [green]--username[/green] "john" [green]--min-filesize[/green] 2GB [green]--days-watched[/green] 90

        [dim]# Remove untagged movies that have been watched[/dim]
        prunarr movies remove [green]--include-untagged[/green] [green]--days-watched[/green] 30

        [dim]# Force remove without confirmation[/dim]
        prunarr movies remove [green]--days-watched[/green] 180 [green]--force[/green]

        [dim]# Remove oldest watched movies first, limit to 10[/dim]
        prunarr movies remove [green]--sort-by[/green] days_watched [green]--limit[/green] 10

        [dim]# Quick cleanup by file size (largest first)[/dim]
        prunarr movies remove [green]--sort-by[/green] filesize [green]--limit[/green] 5

        [dim]# Remove watched movies available on streaming (you can stream them)[/dim]
        prunarr movies remove [green]--on-streaming[/green] [green]--days-watched[/green] 30

        [dim]# Remove watched movies NOT on streaming (keep unique content longer)[/dim]
        prunarr movies remove [green]--not-on-streaming[/green] [green]--days-watched[/green] 180
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("movies", debug=debug, log_level=settings.log_level)

    # Validate streaming filter mutual exclusivity
    if on_streaming and not_on_streaming:
        logger.error("Cannot use both --on-streaming and --not-on-streaming filters together")
        raise typer.Exit(1)

    # Validate and parse options
    sort_by, min_filesize_bytes = validate_and_parse_options(sort_by, min_filesize, logger)

    # Check if streaming filters are requested but not configured
    if (on_streaming or not_on_streaming) and not settings.streaming_enabled:
        logger.error(
            "Streaming filters require streaming_enabled=true in configuration. "
            "Please configure streaming_enabled, streaming_locale, and streaming_providers in your config."
        )
        raise typer.Exit(1)

    # Fix the sort order logic (--sort-asc means ascending, default is descending)
    sort_desc_actual = not sort_desc

    if dry_run:
        logger.info("[DRY RUN] Finding movies for removal with filters...")
    else:
        logger.info("Finding movies for removal with filters...")

    prunarr = PrunArr(settings, debug=debug)

    try:
        # Check if we need streaming data
        need_streaming = on_streaming or not_on_streaming

        # Get all movies with watch status first (and populate streaming cache if needed)
        all_movies = prunarr.get_movies_with_watch_status(
            include_untagged=include_untagged,
            username_filter=username,
            check_streaming=need_streaming,
        )

        # Apply filtering using shared function (remove mode)
        movies_to_remove = apply_movie_filters(
            movies=all_movies,
            days_watched=days_watched,
            min_filesize_bytes=min_filesize_bytes,
            include_untagged=include_untagged,
            remove_mode=True,
        )

        # Apply streaming filters if requested - now using cached data!
        if on_streaming or not_on_streaming:
            from prunarr.services.streaming_checker import StreamingChecker

            logger.info("Filtering by streaming availability (using cached data)...")
            streaming_checker = StreamingChecker(
                locale=settings.streaming_locale,
                providers=settings.streaming_providers,
                cache_manager=prunarr.cache_manager,
                logger=logger,
            )

            streaming_filtered = []
            for movie in movies_to_remove:
                # Try to use cached streaming_available field first
                is_available = movie.get("streaming_available")

                # If not in cache, check via API (and cache the result)
                if is_available is None:
                    is_available = streaming_checker.is_on_streaming(
                        media_type="movie",
                        title=movie.get("title", ""),
                        year=movie.get("year"),
                        imdb_id=movie.get("imdb_id"),
                    )

                # Apply the appropriate filter
                if on_streaming and is_available:
                    streaming_filtered.append(movie)
                elif not_on_streaming and not is_available:
                    streaming_filtered.append(movie)

            movies_to_remove = streaming_filtered
            filter_type = "on streaming" if on_streaming else "not on streaming"
            logger.info(f"After streaming filter: {len(movies_to_remove)} movies {filter_type}")

        # Apply sorting
        movies_to_remove = sort_movies(movies_to_remove, sort_by, sort_desc_actual)

        # Apply limit
        if limit:
            movies_to_remove = movies_to_remove[:limit]

        if not movies_to_remove:
            logger.info("No movies found ready for removal")
            return

        # Show what will be removed
        logger.info(f"Found {len(movies_to_remove)} movies for removal")

        # Create table showing what would be removed using factory
        title = "Movies to Remove (Dry Run)" if dry_run else "Movies to Remove"
        table = create_movies_table(title=title)

        # Remove "Added" column as it's not needed for removal preview
        # Note: We'll create rows without the "Added" value

        for movie in movies_to_remove:
            table.add_row(
                safe_get(movie, "title"),
                safe_get(movie, "year"),
                safe_get(movie, "user"),
                safe_get(movie, "watched_by"),
                safe_get(movie, "days_since_watched"),
                format_file_size(movie.get("file_size", 0)),
                "",  # Empty "Added" column since it's not needed for removal
            )

        console.print(table)

        if dry_run:
            logger.info(
                f"[DRY RUN] Use without --dry-run to actually remove these {len(movies_to_remove)} movies"
            )
            return

        # Log applied filters in debug mode
        if debug:
            filter_info = create_debug_filter_info(
                username=username,
                days_watched=days_watched,
                min_filesize=min_filesize,
                include_untagged=include_untagged,
                sort_by=sort_by,
                sort_desc=sort_desc_actual,
                limit=limit,
            )
            logger.debug(f"Applied filters/sorting: {filter_info}")

        # Confirmation prompt (unless force is used)
        if not force:
            console.print(
                f"\n[bold red]⚠️  WARNING: This will permanently delete {len(movies_to_remove)} movies and their files![/bold red]"
            )

            # Show summary of applied filters
            filter_summary = []
            if username:
                filter_summary.append(f"user: {username}")
            filter_summary.append(f"days watched: {days_watched}+")
            if min_filesize:
                filter_summary.append(f"min size: {min_filesize}")
            if limit:
                filter_summary.append(f"limit: {limit}")

            console.print(f"[dim]Applied filters: {', '.join(filter_summary)}[/dim]")

            if not typer.confirm("\nAre you sure you want to proceed with deletion?"):
                logger.info("Removal cancelled by user")
                return

        # Actually remove the movies
        removed_count = 0
        for movie in movies_to_remove:
            movie_id = movie.get("id")
            title = movie.get("title", "Unknown")

            if debug:
                logger.debug(f"Removing movie: {title} (ID: {movie_id})")

            try:
                success = prunarr.radarr.delete_movie(movie_id, delete_files=True)
                if success:
                    removed_count += 1
                    logger.info(f"Removed: {title}")
                else:
                    logger.warning(f"Failed to remove: {title}")
            except Exception as e:
                logger.error(f"Error removing {title}: {str(e)}")

        logger.info(f"Successfully removed {removed_count} out of {len(movies_to_remove)} movies")

    except Exception as e:
        logger.error(f"Failed during movie removal process: {str(e)}")
        raise typer.Exit(1)


@app.command("get")
def get_movie_details(
    ctx: typer.Context,
    identifier: str = typer.Argument(..., help="Movie title or Radarr ID"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]Get detailed information about a specific movie.[/bold cyan]

    Shows comprehensive movie details including watch status, file information,
    and complete streaming availability across all providers (not just configured ones).

    [bold yellow]Lookup methods:[/bold yellow]
        • By [cyan]title[/cyan] - Partial match (e.g., "Matrix", "Breaking")
        • By [cyan]ID[/cyan] - Exact Radarr movie ID

    [bold yellow]Examples:[/bold yellow]
        [dim]# Get details by title[/dim]
        prunarr movies get "The Matrix"

        [dim]# Get details by Radarr ID[/dim]
        prunarr movies get 123

        [dim]# Get JSON output[/dim]
        prunarr movies get "Inception" [green]--output[/green] json
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("movies", debug=debug, log_level=settings.log_level)

    # Validate output format
    validate_output_format(output, logger)

    logger.info(f"Looking up movie: {identifier}")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Try to find the movie by ID or title
        movies = prunarr.get_movies_with_watch_status(include_untagged=True, check_streaming=False)

        # Try numeric ID first
        movie = None
        movie_id_int = None
        try:
            movie_id_int = int(identifier)
            movie = next((m for m in movies if m.get("id") == movie_id_int), None)
        except ValueError:
            # Search by title (case-insensitive partial match)
            identifier_lower = identifier.lower()
            matches = [m for m in movies if identifier_lower in m.get("title", "").lower()]

            if not matches:
                logger.error(f"No movie found matching: {identifier}")
                raise typer.Exit(1)

            if len(matches) > 1:
                console.print(f"[yellow]⚠️  Multiple movies found matching '{identifier}':[/yellow]")
                for i, m in enumerate(matches[:5], 1):
                    console.print(f"  {i}. {m.get('title')} ({m.get('year')}) [ID: {m.get('id')}]")
                console.print("\n[dim]Please be more specific or use the Radarr ID[/dim]")
                raise typer.Exit(1)

            movie = matches[0]
            movie_id_int = movie.get("id")

        if not movie:
            logger.error(f"No movie found with ID: {identifier}")
            raise typer.Exit(1)

        # Get full movie details from Radarr for additional info
        full_movie = prunarr.radarr.get_movie(movie_id_int)
        movie_file = full_movie.get("movieFile", {})

        # Get all streaming providers (not filtered by config)
        from prunarr.services.streaming_checker import StreamingChecker

        all_providers = []
        if settings.streaming_enabled:
            logger.info("Checking streaming availability across all providers...")
            # Create checker without provider filtering
            streaming_client = JustWatchClient(
                locale=settings.streaming_locale,
                logger=logger,
                cache_manager=prunarr.cache_manager,
            )

            # Search and get offers
            try:
                search_results = streaming_client.search_title(
                    movie.get("title", ""), movie.get("year"), "MOVIE"
                )

                if search_results:
                    offers = streaming_client.get_offers(
                        search_results[0].id, providers=None
                    )  # No filter

                    # Get provider details for full names
                    all_jw_providers = streaming_client.get_providers()
                    provider_name_map = {p.technical_name: p.clear_name for p in all_jw_providers}

                    # Group by provider
                    providers_dict = {}
                    for offer in offers:
                        if offer.monetization_type == "FLATRATE":  # Only subscriptions
                            provider_short = offer.provider_short_name
                            if provider_short not in providers_dict:
                                providers_dict[provider_short] = []
                            providers_dict[provider_short].append(offer.monetization_type)

                    # Map to full names
                    all_providers = [provider_name_map.get(p, p) for p in providers_dict.keys()]
            except Exception as e:
                logger.warning(f"Could not fetch streaming data: {e}")

        if output == "json":
            # Prepare JSON output
            json_output = prepare_movie_for_json(movie)
            json_output["all_streaming_providers"] = all_providers
            print(json.dumps(json_output, indent=2))
        else:
            # Display detailed information
            console.print(
                f"\n[bold cyan]Movie Details: {movie.get('title')} ({movie.get('year')})[/bold cyan]\n"
            )

            # Create details table
            from prunarr.utils.tables import create_history_details_table

            table = create_history_details_table(movie.get("id", 0))
            table.title = None

            # Basic info
            table.add_row("Title", movie.get("title", "N/A"))
            table.add_row("Year", str(movie.get("year", "N/A")))

            # IDs
            table.add_row("Radarr ID", str(movie.get("id", "N/A")))
            table.add_row("IMDB ID", movie.get("imdb_id", "N/A"))
            if full_movie.get("tmdbId"):
                table.add_row("TMDB ID", str(full_movie.get("tmdbId")))

            # Status info
            table.add_row("Status", full_movie.get("status", "N/A"))
            table.add_row("Monitored", "Yes" if full_movie.get("monitored") else "No")

            # User info
            table.add_row("User", movie.get("user") or "[dim]Untagged[/dim]")
            table.add_row(
                "Watch Status", format_movie_watch_status(movie.get("watch_status", "unknown"))
            )
            table.add_row("Watched By", movie.get("watched_by") or "N/A")

            if movie.get("watched_at"):
                table.add_row("Watched Date", format_date_or_default(movie.get("watched_at")))
                days_ago = movie.get("days_since_watched")
                if days_ago is not None:
                    table.add_row("Days Since Watched", str(days_ago))

            # File info
            table.add_row("File Size", format_file_size(movie.get("file_size", 0)))
            if movie_file.get("quality"):
                quality_name = (
                    movie_file.get("quality", {}).get("quality", {}).get("name", "Unknown")
                )
                table.add_row("Quality", quality_name)
            if movie_file.get("mediaInfo"):
                media_info = movie_file.get("mediaInfo", {})
                if media_info.get("videoCodec"):
                    table.add_row("Video Codec", media_info.get("videoCodec"))
                if media_info.get("audioCodec"):
                    table.add_row("Audio Codec", media_info.get("audioCodec"))
                if media_info.get("resolution"):
                    table.add_row("Resolution", media_info.get("resolution"))

            # Dates
            table.add_row(
                "Added to Radarr",
                format_date_or_default(parse_iso_datetime(full_movie.get("added"))),
            )
            if movie_file.get("dateAdded"):
                table.add_row(
                    "File Downloaded",
                    format_date_or_default(parse_iso_datetime(movie_file.get("dateAdded"))),
                )
            if full_movie.get("inCinemas"):
                table.add_row(
                    "In Cinemas",
                    format_date_or_default(parse_iso_datetime(full_movie.get("inCinemas"))),
                )
            if full_movie.get("digitalRelease"):
                table.add_row(
                    "Digital Release",
                    format_date_or_default(parse_iso_datetime(full_movie.get("digitalRelease"))),
                )
            if full_movie.get("physicalRelease"):
                table.add_row(
                    "Physical Release",
                    format_date_or_default(parse_iso_datetime(full_movie.get("physicalRelease"))),
                )

            # Path
            if full_movie.get("path"):
                table.add_row("Path", full_movie.get("path"))

            # Streaming information
            if all_providers:
                table.add_row("Streaming On", ", ".join(sorted(all_providers)))
            elif settings.streaming_enabled:
                table.add_row("Streaming On", "[dim]Not available on subscription services[/dim]")

            console.print(table)

    except Exception as e:
        logger.error(f"Failed to get movie details: {str(e)}")
        raise typer.Exit(1)
