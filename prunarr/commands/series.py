"""
Series command module for PrunArr CLI.

This module provides commands for managing TV series in Sonarr,
including listing with advanced filtering, watch status tracking, and removal capabilities.
Supports episode-level, season-level, and series-level tracking and filtering.
"""

import json
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from prunarr.config import Settings
from prunarr.logger import get_logger
from prunarr.prunarr import PrunArr
from prunarr.utils import (
    format_completion_percentage,
    format_date_or_default,
    format_episode_count,
    format_file_size,
    format_series_watch_status,
    format_timestamp_to_date,
    safe_get,
    safe_str,
)
from prunarr.utils.serializers import prepare_datetime_for_json, prepare_series_for_json
from prunarr.utils.tables import (
    create_episodes_table,
    create_series_removal_table,
    create_series_table,
)
from prunarr.utils.validators import validate_output_format

console = Console()
app = typer.Typer(help="Manage TV shows in Sonarr.", rich_markup_mode="rich")


@app.command("list")
def list_series(
    ctx: typer.Context,
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Filter by username"),
    series_name: Optional[str] = typer.Option(
        None, "--series", "-s", help="Filter by series title (partial match)"
    ),
    season: Optional[int] = typer.Option(None, "--season", help="Filter by specific season number"),
    watched: bool = typer.Option(False, "--watched", "-w", help="Show only fully watched series"),
    partially_watched: bool = typer.Option(
        False, "--partially-watched", "-p", help="Show only partially watched series"
    ),
    unwatched: bool = typer.Option(False, "--unwatched", help="Show only unwatched series"),
    include_untagged: bool = typer.Option(
        True, "--include-untagged", help="Include series without user tags"
    ),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    on_streaming: bool = typer.Option(
        False, "--on-streaming", help="Show ONLY series available on configured streaming providers"
    ),
    not_on_streaming: bool = typer.Option(
        False, "--not-on-streaming", help="Show ONLY series NOT available on streaming providers"
    ),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]List TV series in Sonarr with advanced filtering options.[/bold cyan]

    Displays a formatted table of TV series with watch status, episode counts, and completion percentages.
    Supports filtering by user, series title, season, watch status, and result limits.

    [bold yellow]Watch Status Types:[/bold yellow]
        • [green]Fully Watched[/green] - All episodes watched by the requester
        • [yellow]Partially Watched[/yellow] - Some episodes watched by the requester
        • [red]Unwatched[/red] - No episodes watched by the requester
        • [dim]No Episodes[/dim] - Series has no downloaded episodes

    [bold yellow]Table columns:[/bold yellow]
        • [cyan]ID[/cyan] - Sonarr series ID
        • [cyan]Title[/cyan] - series name
        • [cyan]User[/cyan] - who requested the series
        • [cyan]Status[/cyan] - watch completion status
        • [cyan]Episodes[/cyan] - watched/total episode counts
        • [cyan]Progress[/cyan] - completion percentage
        • [cyan]Seasons[/cyan] - comma-separated list of downloaded seasons
        • [cyan]Size[/cyan] - total file size
        • [cyan]Last Watched[/cyan] - most recent watch date

    [bold yellow]Examples:[/bold yellow]
        [dim]# List all series (newest first)[/dim]
        prunarr series list

        [dim]# Show only fully watched series from specific user[/dim]
        prunarr series list [green]--watched[/green] [green]--username[/green] \"john\"

        [dim]# Filter specific series and season[/dim]
        prunarr series list [green]--series[/green] \"breaking bad\" [green]--season[/green] 1

        [dim]# Show partially watched series with debug info[/dim]
        prunarr[blue]--debug[/blue] series list [green]--partially-watched[/green]

        [dim]# Show series available on configured streaming providers[/dim]
        prunarr series list [green]--on-streaming[/green]

        [dim]# Show series NOT available on streaming (unique content)[/dim]
        prunarr series list [green]--not-on-streaming[/green]

        [dim]# Latest 10 series without user tags[/dim]
        prunarr series list [green]--limit[/green] 10 [green]--include-untagged[/green]
    """
    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("series", debug=debug, log_level=settings.log_level)

    # Validate output format using shared validator
    validate_output_format(output, logger)

    # Validate streaming filter mutual exclusivity
    if on_streaming and not_on_streaming:
        logger.error("Cannot use both --on-streaming and --not-on-streaming filters together")
        raise typer.Exit(1)

    # Check if streaming filters are requested but not configured
    if (on_streaming or not_on_streaming) and not settings.streaming_enabled:
        logger.error(
            "Streaming filters require streaming_enabled=true in configuration. "
            "Please configure streaming_enabled, streaming_locale, and streaming_providers in your config."
        )
        raise typer.Exit(1)

    logger.info("Retrieving Sonarr series...")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Always check streaming if enabled in config
        check_streaming = settings.streaming_enabled

        # Get series with watch status and apply filters (and populate streaming cache if needed)
        series_list = prunarr.get_series_with_watch_status(
            include_untagged=include_untagged,
            username_filter=username,
            series_filter=series_name,
            season_filter=season,
            check_streaming=check_streaming,
        )

        # Check and log cache status
        if prunarr.cache_manager:
            prunarr.check_and_log_cache_status(prunarr.cache_manager.KEY_SONARR_SERIES, logger)

        if not series_list:
            logger.warning("No series found matching the specified criteria")
            return

        # Apply watch status filters
        filtered_series = []
        for series in series_list:
            watch_status = series.get("watch_status")

            if watched and watch_status != "fully_watched":
                continue
            if partially_watched and watch_status != "partially_watched":
                continue
            if unwatched and watch_status != "unwatched":
                continue

            filtered_series.append(series)

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
            for series in filtered_series:
                # Try to use cached streaming_available field first
                is_available = series.get("streaming_available")

                # If not in cache, check via API (and cache the result)
                if is_available is None:
                    is_available = streaming_checker.is_on_streaming(
                        media_type="series",
                        title=series.get("title", ""),
                        tvdb_id=series.get("tvdb_id"),
                    )

                # Apply the appropriate filter
                if on_streaming and is_available:
                    streaming_filtered.append(series)
                elif not_on_streaming and not is_available:
                    streaming_filtered.append(series)

            filtered_series = streaming_filtered
            filter_type = "on streaming" if on_streaming else "not on streaming"
            logger.info(f"After streaming filter: {len(filtered_series)} series {filter_type}")

        # Apply limit
        if limit:
            filtered_series = filtered_series[:limit]

        if not filtered_series:
            logger.warning("No series found after applying filters")
            return

        logger.info(f"Found {len(filtered_series)} series")

        # Output based on format
        if output == "json":
            # Prepare JSON-serializable data using shared serializer
            json_output = [prepare_series_for_json(series) for series in filtered_series]
            print(json.dumps(json_output, indent=2))
        else:
            # Create Rich table using factory - always include streaming column
            table = create_series_table(include_streaming=True)

            # Populate table with series data
            for series in filtered_series:
                # Use available_seasons from data
                available_seasons = series.get("available_seasons", "")

                # Format last watched date
                last_watched_str = format_date_or_default(
                    series.get("most_recent_watch"), default="Never"
                )

                # Build row data
                row_data = [
                    safe_get(series, "id"),
                    safe_get(series, "title"),
                    safe_str(series.get("user"), default="Untagged"),
                    format_series_watch_status(series.get("watch_status", "unknown")),
                    format_episode_count(
                        series.get("watched_episodes", 0), series.get("total_episodes", 0)
                    ),
                    format_completion_percentage(series.get("completion_percentage", 0)),
                    available_seasons if available_seasons else "-",
                    format_file_size(series.get("total_size_on_disk", 0)),
                ]

                # Add streaming info - always show
                streaming_available = series.get("streaming_available")
                if streaming_available is True:
                    streaming_display = "✓"
                elif streaming_available is False:
                    streaming_display = "✗"
                else:
                    streaming_display = "-"  # Not checked yet
                row_data.append(streaming_display)

                row_data.append(last_watched_str)
                table.add_row(*row_data)

            console.print(table)

        # Log applied filters in debug mode
        if debug:
            logger.debug(
                f"Applied filters: username={username}, series_name={series_name}, "
                f"season={season}, watched={watched}, partially_watched={partially_watched}, "
                f"unwatched={unwatched}, include_untagged={include_untagged}, limit={limit}"
            )

    except Exception as e:
        logger.error(f"Failed to retrieve series: {str(e)}")
        raise typer.Exit(1)


@app.command("remove")
def remove_series(
    ctx: typer.Context,
    days_watched: int = typer.Option(
        60, "--days-watched", "-d", help="Minimum days since last watched before removal"
    ),
    removal_mode: str = typer.Option(
        "series", "--mode", "-m", help="Removal granularity: 'series' or 'season'"
    ),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Filter by username"),
    series_name: Optional[str] = typer.Option(
        None, "--series", "-s", help="Filter by series title (partial match)"
    ),
    season: Optional[int] = typer.Option(None, "--season", help="Filter by specific season number"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be removed without actually removing"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
    on_streaming: bool = typer.Option(
        False,
        "--on-streaming",
        help="Remove ONLY series available on configured streaming providers",
    ),
    not_on_streaming: bool = typer.Option(
        False, "--not-on-streaming", help="Remove ONLY series NOT available on streaming providers"
    ),
):
    """
    [bold cyan]Remove watched TV series with advanced filtering and confirmation.[/bold cyan]

    Removes series or seasons that have been fully watched by the requester for a specified number of days.
    Supports different removal granularities and multiple confirmation steps for safety.

    [bold yellow]Removal Modes:[/bold yellow]
        • [cyan]series[/cyan] - Remove entire series when all episodes are watched
        • [cyan]season[/cyan] - Remove individual seasons when fully watched

    [bold yellow]Safety Features:[/bold yellow]
        • [cyan]Confirmation prompts[/cyan] - Multiple confirmation steps
        • [cyan]Dry run mode[/cyan] - Preview what would be removed
        • [cyan]User tag validation[/cyan] - Only removes content requested by users
        • [cyan]Watch status verification[/cyan] - Ensures content was actually watched

    [bold yellow]Examples:[/bold yellow]
        [dim]# Preview what would be removed (dry run)[/dim]
        prunarr series remove [green]--dry-run[/green]

        [dim]# Remove fully watched series after 30 days[/dim]
        prunarr series remove [green]--days-watched[/green] 30

        [dim]# Remove individual seasons mode[/dim]
        prunarr series remove [green]--mode[/green] season [green]--days-watched[/green] 45

        [dim]# Remove specific user's content without confirmation[/dim]
        prunarr series remove [green]--username[/green] \"john\" [green]--force[/green]

        [dim]# Remove specific series seasons[/dim]
        prunarr series remove [green]--series[/green] \"the office\" [green]--mode[/green] season

        [dim]# Remove watched series available on streaming (you can stream them)[/dim]
        prunarr series remove [green]--on-streaming[/green] [green]--days-watched[/green] 30

        [dim]# Remove watched series NOT on streaming (keep unique content longer)[/dim]
        prunarr series remove [green]--not-on-streaming[/green] [green]--days-watched[/green] 180

    [bold yellow]Note:[/bold yellow]
        This operation permanently deletes files from your system. Use [green]--dry-run[/green] first to preview changes.
    """
    # Validate removal mode
    if removal_mode not in ["series", "season"]:
        console.print("[red]❌ Error: --mode must be either 'series' or 'season'[/red]")
        raise typer.Exit(1)

    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("series", debug=debug, log_level=settings.log_level)

    # Validate streaming filter mutual exclusivity
    if on_streaming and not_on_streaming:
        logger.error("Cannot use both --on-streaming and --not-on-streaming filters together")
        raise typer.Exit(1)

    # Check if streaming filters are requested but not configured
    if (on_streaming or not_on_streaming) and not settings.streaming_enabled:
        logger.error(
            "Streaming filters require streaming_enabled=true in configuration. "
            "Please configure streaming_enabled, streaming_locale, and streaming_providers in your config."
        )
        raise typer.Exit(1)

    logger.info(f"Finding series ready for removal (mode: {removal_mode}, days: {days_watched})...")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Check if we need streaming data
        need_streaming = on_streaming or not_on_streaming

        # Get series ready for removal (and populate streaming cache if needed)
        items_to_remove = prunarr.get_series_ready_for_removal(
            days_watched=days_watched, removal_mode=removal_mode, check_streaming=need_streaming
        )

        # Apply additional filters
        if username:
            items_to_remove = [item for item in items_to_remove if item.get("user") == username]

        if series_name:
            items_to_remove = [
                item
                for item in items_to_remove
                if series_name.lower() in item.get("title", "").lower()
            ]

        if season and removal_mode == "season":
            items_to_remove = [
                item for item in items_to_remove if item.get("season_number") == season
            ]

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
            for item in items_to_remove:
                # Try to use cached streaming_available field first
                is_available = item.get("streaming_available")

                # If not in cache, check via API (and cache the result)
                if is_available is None:
                    is_available = streaming_checker.is_on_streaming(
                        media_type="series",
                        title=item.get("title", ""),
                        tvdb_id=item.get("tvdb_id"),
                    )

                # Apply the appropriate filter
                if on_streaming and is_available:
                    streaming_filtered.append(item)
                elif not_on_streaming and not is_available:
                    streaming_filtered.append(item)

            items_to_remove = streaming_filtered
            filter_type = "on streaming" if on_streaming else "not on streaming"
            logger.info(f"After streaming filter: {len(items_to_remove)} items {filter_type}")

        if not items_to_remove:
            logger.info("No series found that meet the removal criteria")
            return

        # Display what will be removed using factory
        table = create_series_removal_table(
            title=(
                f"Series Ready for Removal ({len(items_to_remove)} items)"
                if removal_mode == "series"
                else f"Seasons Ready for Removal ({len(items_to_remove)} items)"
            ),
            mode=removal_mode,
        )

        if removal_mode == "series":
            for item in items_to_remove:
                last_watched_str = format_date_or_default(
                    item.get("most_recent_watch"), default="Never"
                )

                table.add_row(
                    safe_get(item, "id"),
                    safe_get(item, "title"),
                    safe_get(item, "user"),
                    format_episode_count(
                        item.get("watched_episodes", 0), item.get("total_episodes", 0)
                    ),
                    format_completion_percentage(item.get("completion_percentage", 0)),
                    last_watched_str,
                    safe_str(item.get("days_since_watched")),
                )

        else:  # season mode
            for item in items_to_remove:
                last_watched_str = format_date_or_default(
                    item.get("most_recent_watch"), default="Never"
                )
                season_data = item.get("season_data", {})

                table.add_row(
                    safe_get(item, "id"),
                    safe_get(item, "title"),
                    safe_get(item, "season_number"),
                    safe_get(item, "user"),
                    format_episode_count(
                        season_data.get("watched_by_user", 0), season_data.get("total_episodes", 0)
                    ),
                    last_watched_str,
                    safe_str(item.get("days_since_watched")),
                )

        console.print(table)

        # Dry run mode - just show what would be removed
        if dry_run:
            console.print(
                f"\n[bold yellow]🔍 DRY RUN:[/bold yellow] {len(items_to_remove)} {removal_mode}(s) would be removed"
            )
            logger.info("Dry run completed - no actual removal performed")
            return

        # Confirmation prompts for actual removal
        if not force:
            console.print(
                f"\n[bold red]⚠️  WARNING:[/bold red] This will permanently delete {len(items_to_remove)} {removal_mode}(s) and their files!"
            )

            if not typer.confirm(
                f"Do you want to proceed with removing these {len(items_to_remove)} {removal_mode}(s)?"
            ):
                logger.info("Removal cancelled by user")
                return

            # Final confirmation for extra safety
            if not typer.confirm("Are you absolutely sure? This cannot be undone!"):
                logger.info("Removal cancelled by user at final confirmation")
                return

        # Perform the actual removal
        removed_count = 0
        failed_count = 0

        for item in items_to_remove:
            series_id = item.get("id")
            title = item.get("title", "Unknown")

            try:
                if removal_mode == "series":
                    success = prunarr.sonarr.delete_series(series_id, delete_files=True)
                    if success:
                        logger.info(f"Removed series: {title} (ID: {series_id})")
                        removed_count += 1
                    else:
                        logger.error(f"Failed to remove series: {title} (ID: {series_id})")
                        failed_count += 1
                else:  # season mode
                    # Note: Sonarr doesn't have direct season deletion, this would need custom implementation
                    # For now, we'll log that this feature needs implementation
                    logger.warning(
                        f"Season-level removal not yet implemented for: {title} Season {item.get('season_number')}"
                    )
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error removing {title}: {str(e)}")
                failed_count += 1

        # Summary
        if removed_count > 0:
            logger.info(f"Successfully removed {removed_count} {removal_mode}(s)")
        if failed_count > 0:
            logger.error(f"Failed to remove {failed_count} {removal_mode}(s)")

        # Log applied filters in debug mode
        if debug:
            logger.debug(
                f"Applied filters: days_watched={days_watched}, removal_mode={removal_mode}, "
                f"username={username}, series_name={series_name}, season={season}, "
                f"dry_run={dry_run}, force={force}"
            )

    except Exception as e:
        logger.error(f"Failed to remove series: {str(e)}")
        raise typer.Exit(1)


@app.command("get")
def get_series_details(
    ctx: typer.Context,
    identifier: str = typer.Argument(..., help="Series title or ID"),
    season_filter: Optional[int] = typer.Option(
        None, "--season", "-s", help="Show only specific season"
    ),
    watched_only: bool = typer.Option(
        False, "--watched-only", "-w", help="Show only watched episodes"
    ),
    unwatched_only: bool = typer.Option(
        False, "--unwatched-only", "-u", help="Show only unwatched episodes"
    ),
    show_all_watchers: bool = typer.Option(
        False, "--all-watchers", "-a", help="Show watch info for all users, not just requester"
    ),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]Get detailed information about a specific TV series.[/bold cyan]

    Shows comprehensive episode-level details including watch status, air dates, and user information.
    Accepts either a series title (fuzzy matching) or numeric Sonarr ID.

    [bold yellow]Features:[/bold yellow]
        • [cyan]Smart lookup[/cyan] - Find series by title or ID
        • [cyan]Episode details[/cyan] - Show individual episode information
        • [cyan]Watch tracking[/cyan] - See who watched what and when
        • [cyan]Season filtering[/cyan] - Focus on specific seasons
        • [cyan]Status filtering[/cyan] - Show only watched or unwatched content

    [bold yellow]Episode Information:[/bold yellow]
        • [cyan]Episode numbers[/cyan] and [cyan]titles[/cyan]
        • [cyan]Air dates[/cyan] and [cyan]runtime[/cyan]
        • [cyan]Watch status[/cyan] with color coding
        • [cyan]Watch dates[/cyan] and [cyan]user information[/cyan]
        • [cyan]File status[/cyan] (downloaded/missing)

    [bold yellow]Examples:[/bold yellow]
        [dim]# Get details by series title[/dim]
        prunarr series get \"breaking bad\"

        [dim]# Get details by Sonarr ID[/dim]
        prunarr series get 123

        [dim]# Show only season 2 episodes[/dim]
        prunarr series get \"the office\" [green]--season[/green] 2

        [dim]# Show only unwatched episodes[/dim]
        prunarr series get \"stranger things\" [green]--unwatched-only[/green]

        [dim]# Show watch info for all users[/dim]
        prunarr series get \"game of thrones\" [green]--all-watchers[/green]

        [dim]# Show only watched episodes with debug info[/dim]
        prunarr [blue]--debug[/blue] series get \"westworld\" [green]--watched-only[/green]
    """
    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("series", debug=debug, log_level=settings.log_level)

    # Validate output format using shared validator
    validate_output_format(output, logger)

    logger.info(f"Looking up series: {identifier}")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Find the series using smart identifier resolution
        series_matches = prunarr.find_series_by_identifier(identifier)

        if not series_matches:
            console.print(f"[red]❌ No series found matching: {identifier}[/red]")
            raise typer.Exit(1)

        if len(series_matches) > 1:
            console.print(f"[yellow]⚠️  Multiple series found matching '{identifier}':[/yellow]")
            for i, series in enumerate(series_matches[:5], 1):
                console.print(f"  {i}. {series['title']} ({series['year']}) - ID: {series['id']}")
            console.print("[dim]Please use a more specific title or the series ID.[/dim]")
            raise typer.Exit(1)

        series_data = series_matches[0]
        series_id = series_data["id"]
        series_title = series_data["title"]

        logger.info(f"Found series: {series_title} (ID: {series_id})")

        # Get detailed series information
        detailed_info = prunarr.get_series_detailed_info(
            series_id=series_id,
            season_filter=season_filter,
            watched_only=watched_only,
            unwatched_only=unwatched_only,
            show_all_watchers=show_all_watchers,
        )

        if not detailed_info:
            console.print(
                f"[red]❌ Could not retrieve detailed information for series: {series_title}[/red]"
            )
            raise typer.Exit(1)

        # Extract data from the nested structure
        series_info = detailed_info.get("series_info", {})
        series_watch_data = detailed_info.get("series_watch_data", {})
        seasons_data = detailed_info.get("seasons_data", {})

        # Show series-level statistics
        total_episodes = detailed_info.get("total_episodes", 0)
        watched_episodes = series_watch_data.get("watched_episodes", 0)
        total_seasons = detailed_info.get("total_seasons", 0)

        # Get episode file data for filesize information
        episode_files = prunarr.sonarr.get_episode_files(series_id)
        episode_file_map = {}
        total_series_size = 0
        for file_data in episode_files:
            file_id = file_data.get("id")
            if file_id:
                episode_file_map[file_id] = file_data
                total_series_size += file_data.get("size", 0)

        # Display seasons and episodes
        seasons = list(seasons_data.values())
        if not seasons:
            if output == "json":
                print(json.dumps({"error": "No episode information available"}, indent=2))
            else:
                console.print("\n[yellow]⚠️  No episode information available[/yellow]")
            return

        # Output based on format
        if output == "json":
            # Prepare JSON-serializable data
            json_output = {
                "series_info": {
                    "id": series_id,
                    "title": series_info.get("title"),
                    "year": series_info.get("year"),
                    "total_seasons": total_seasons,
                    "total_episodes": total_episodes,
                    "watched_episodes": watched_episodes,
                    "completion_percentage": series_watch_data.get("completion_percentage", 0),
                    "total_size_bytes": total_series_size,
                    "user": series_watch_data.get("user"),
                },
                "seasons": [],
            }

            # Add last watched date
            if series_watch_data.get("most_recent_watch"):
                json_output["series_info"]["last_watched"] = series_watch_data[
                    "most_recent_watch"
                ].isoformat()
            else:
                json_output["series_info"]["last_watched"] = None

            # Process seasons and episodes
            for season_data in seasons:
                season_num = season_data.get("season_number")
                season_episodes = season_data.get("episodes", [])
                season_watched = season_data.get("watched_by_user", 0)
                season_total = season_data.get("total_episodes", 0)

                # Skip season if it doesn't match filter
                if season_filter is not None and season_num != season_filter:
                    continue

                if not season_episodes:
                    continue

                # Calculate total season filesize
                season_total_size = 0
                for episode in season_episodes:
                    episode_file_id = episode.get("episode_file_id")
                    if episode_file_id and episode_file_id in episode_file_map:
                        file_data = episode_file_map[episode_file_id]
                        season_total_size += file_data.get("size", 0)

                season_json = {
                    "season_number": season_num,
                    "watched_episodes": season_watched,
                    "total_episodes": season_total,
                    "total_size_bytes": season_total_size,
                    "episodes": [],
                }

                for episode in season_episodes:
                    episode_num = episode.get("episode_number")
                    watched = episode.get("watched", False)
                    watched_at = episode.get("watched_at")
                    episode_file_id = episode.get("episode_file_id")

                    # Apply filtering
                    if watched_only and not watched:
                        continue
                    if unwatched_only and watched:
                        continue

                    # Get episode filesize
                    episode_size = 0
                    if episode_file_id and episode_file_id in episode_file_map:
                        file_data = episode_file_map[episode_file_id]
                        episode_size = file_data.get("size", 0)

                    # Format watched date
                    watched_date_iso = None
                    if watched and watched_at:
                        try:
                            watched_date_iso = datetime.fromtimestamp(int(watched_at)).isoformat()
                        except (ValueError, TypeError):
                            watched_date_iso = None

                    episode_json = {
                        "episode_number": episode_num,
                        "title": episode.get("title"),
                        "air_date": episode.get("air_date"),
                        "runtime": episode.get("runtime", 0),
                        "has_file": episode.get("has_file", False),
                        "watched": watched,
                        "watched_at": watched_date_iso,
                        "watched_by": episode.get("watched_by"),
                        "file_size_bytes": episode_size,
                    }

                    season_json["episodes"].append(episode_json)

                json_output["seasons"].append(season_json)

            print(json.dumps(json_output, indent=2))
        else:
            # Display series header information
            console.print(
                f"\n[bold cyan]📺 {series_info.get('title', 'Unknown Title')}[/bold cyan]"
            )
            if series_info.get("year"):
                console.print(f"[dim]Released: {series_info['year']}[/dim]")

            if series_watch_data.get("user"):
                console.print(f"[blue]Requested by: {series_watch_data['user']}[/blue]")

            console.print(f"[cyan]Seasons:[/cyan] {total_seasons}")
            console.print(
                f"[cyan]Episodes:[/cyan] {format_episode_count(watched_episodes, total_episodes)}"
            )
            console.print(
                f"[cyan]Progress:[/cyan] {format_completion_percentage(series_watch_data.get('completion_percentage', 0))}"
            )

            if series_watch_data.get("most_recent_watch"):
                last_watched = format_date_or_default(series_watch_data["most_recent_watch"])
                console.print(f"[cyan]Last Watched:[/cyan] {last_watched}")

            # Display total series filesize
            if total_series_size > 0:
                console.print(f"[cyan]Total Size:[/cyan] {format_file_size(total_series_size)}")

            for season_data in seasons:
                season_num = season_data.get("season_number")
                season_episodes = season_data.get("episodes", [])
                season_watched = season_data.get("watched_by_user", 0)
                season_total = season_data.get("total_episodes", 0)

                # Skip season if it doesn't match filter
                if season_filter is not None and season_num != season_filter:
                    continue

                if not season_episodes:
                    continue

                # Calculate total season filesize
                season_total_size = 0
                for episode in season_episodes:
                    episode_file_id = episode.get("episode_file_id")
                    if episode_file_id and episode_file_id in episode_file_map:
                        file_data = episode_file_map[episode_file_id]
                        season_total_size += file_data.get("size", 0)

                # Season header with total size
                season_size_str = (
                    format_file_size(season_total_size) if season_total_size > 0 else ""
                )
                size_display = f" - {season_size_str}" if season_size_str else ""
                console.print(
                    f"\n[bold magenta]Season {season_num}[/bold magenta] "
                    f"({format_episode_count(season_watched, season_total)}){size_display}"
                )

                # Create episodes table using factory
                table = create_episodes_table()

                for episode in season_episodes:
                    episode_num = episode.get("episode_number", "N/A")
                    title = episode.get("title", "No Title")
                    air_date = episode.get("air_date", "")
                    runtime = episode.get("runtime", 0)
                    has_file = episode.get("has_file", False)
                    watched = episode.get("watched", False)
                    watched_at = episode.get("watched_at")
                    watched_by = episode.get("watched_by", "")
                    episode_file_id = episode.get("episode_file_id")

                    # Apply filtering
                    if watched_only and not watched:
                        continue
                    if unwatched_only and watched:
                        continue

                    # Format air date
                    air_date_str = air_date if air_date else "TBA"

                    # Format runtime
                    runtime_str = f"{runtime}m" if runtime > 0 else "N/A"

                    # Format file/watch status
                    if has_file:
                        if watched:
                            status = "[green]✓ Watched[/green]"
                        else:
                            status = "[yellow]📁 Downloaded[/yellow]"
                    else:
                        status = "[red]❌ Missing[/red]"

                    # Format episode filesize
                    episode_size = 0
                    if episode_file_id and episode_file_id in episode_file_map:
                        file_data = episode_file_map[episode_file_id]
                        episode_size = file_data.get("size", 0)

                    size_str = format_file_size(episode_size) if episode_size > 0 else "-"

                    # Format watched date and user
                    if watched and watched_at:
                        watched_date = format_timestamp_to_date(watched_at, default="Unknown")
                    else:
                        watched_date = "[yellow]Not watched[/yellow]"

                    user_display = watched_by if watched_by else "-"

                    table.add_row(
                        safe_str(episode_num),
                        safe_str(title),
                        air_date_str,
                        runtime_str,
                        status,
                        size_str,
                        watched_date,
                        user_display,
                    )

                console.print(table)

            # Show summary statistics
            console.print("\n[bold cyan]Summary:[/bold cyan]")
            if season_filter is not None:
                filtered_seasons = [s for s in seasons if s.get("season_number") == season_filter]
                if filtered_seasons:
                    season = filtered_seasons[0]
                    console.print(
                        f"Season {season_filter}: {format_episode_count(season.get('watched_episodes', 0), season.get('total_episodes', 0))}"
                    )
            else:
                console.print(
                    f"Total Progress: {format_episode_count(watched_episodes, total_episodes)} "
                    f"({format_completion_percentage(series_watch_data.get('completion_percentage', 0))})"
                )

        # Log applied filters in debug mode
        if debug:
            logger.debug(
                f"Applied filters: season_filter={season_filter}, "
                f"watched_only={watched_only}, unwatched_only={unwatched_only}, "
                f"show_all_watchers={show_all_watchers}"
            )

    except Exception as e:
        logger.error(f"Failed to get series details: {str(e)}")
        raise typer.Exit(1)
