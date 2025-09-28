"""
Series command module for PrunArr CLI.

This module provides commands for managing TV series in Sonarr,
including listing with advanced filtering, watch status tracking, and removal capabilities.
Supports episode-level, season-level, and series-level tracking and filtering.
"""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from prunarr.config import Settings
from prunarr.logger import get_logger
from prunarr.prunarr import PrunArr

console = Console()
app = typer.Typer(help="Manage TV shows in Sonarr.", rich_markup_mode="rich")


def format_watch_status(status: str) -> str:
    """
    Format watch status with Rich markup colors.

    Args:
        status: Watch status (fully_watched, partially_watched, unwatched, no_episodes)

    Returns:
        Colored status string with Rich markup
    """
    if status == "fully_watched":
        return "[green]✓ Fully Watched[/green]"
    elif status == "partially_watched":
        return "[yellow]📺 Partially Watched[/yellow]"
    elif status == "unwatched":
        return "[red]✗ Unwatched[/red]"
    elif status == "no_episodes":
        return "[dim]❌ No Episodes[/dim]"
    else:
        return "[dim]❓ Unknown[/dim]"


def format_completion_percentage(percentage: float) -> str:
    """
    Format completion percentage with color coding.

    Args:
        percentage: Completion percentage (0-100)

    Returns:
        Colored percentage string with Rich markup
    """
    if percentage >= 100:
        return f"[green]{percentage:.0f}%[/green]"
    elif percentage >= 50:
        return f"[yellow]{percentage:.0f}%[/yellow]"
    elif percentage > 0:
        return f"[red]{percentage:.0f}%[/red]"
    else:
        return "[dim]0%[/dim]"


def format_episode_count(watched: int, total: int) -> str:
    """
    Format episode count with color coding.

    Args:
        watched: Number of watched episodes
        total: Total number of episodes

    Returns:
        Colored episode count string
    """
    if total == 0:
        return "[dim]0/0[/dim]"
    elif watched == total:
        return f"[green]{watched}/{total}[/green]"
    elif watched > 0:
        return f"[yellow]{watched}/{total}[/yellow]"
    else:
        return f"[red]{watched}/{total}[/red]"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.2 GB", "450 MB")
    """
    if size_bytes == 0:
        return "0 B"

    # Define size units
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Format with appropriate decimal places
    if size >= 100:
        return f"{size:.0f} {units[unit_index]}"
    elif size >= 10:
        return f"{size:.1f} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


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
        • [cyan]Title[/cyan] and [cyan]Year[/cyan] - series information
        • [cyan]User[/cyan] - who requested the series
        • [cyan]Status[/cyan] - watch completion status
        • [cyan]Episodes[/cyan] - watched/total episode counts
        • [cyan]Progress[/cyan] - completion percentage
        • [cyan]Seasons[/cyan] - number of seasons
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

        [dim]# Latest 10 series without user tags[/dim]
        prunarr series list [green]--limit[/green] 10 [green]--include-untagged[/green]
    """
    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("series", debug=debug)

    logger.info("Retrieving Sonarr series...")
    prunarr = PrunArr(settings)

    try:
        # Get series with watch status and apply filters
        series_list = prunarr.get_series_with_watch_status(
            include_untagged=include_untagged,
            username_filter=username,
            series_filter=series_name,
            season_filter=season,
            debug=debug,
        )

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

        # Apply limit
        if limit:
            filtered_series = filtered_series[:limit]

        if not filtered_series:
            logger.warning("No series found after applying filters")
            return

        logger.success(f"Found {len(filtered_series)} series")

        # Create Rich table with appropriate styling
        table = Table(title="Sonarr TV Series")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Title", style="bright_white", min_width=20)
        table.add_column("Year", style="yellow", width=6)
        table.add_column("User", style="blue", width=12)
        table.add_column("Status", width=15)
        table.add_column("Episodes", style="cyan", width=12)
        table.add_column("Progress", style="green", width=8)
        table.add_column("Seasons", style="magenta", width=8)
        table.add_column("Size", style="cyan", width=10)
        table.add_column("Last Watched", style="dim", width=12)

        # Populate table with series data
        for series in filtered_series:
            # Use seasons_count from data
            season_count = series.get("seasons_count", 0)

            # Format last watched date
            last_watched = series.get("most_recent_watch")
            last_watched_str = last_watched.strftime("%Y-%m-%d") if last_watched else "Never"

            table.add_row(
                str(series.get("id", "N/A")),
                str(series.get("title", "N/A")),
                str(series.get("year", "N/A")),
                str(series.get("user", "Untagged") if series.get("user") else "Untagged"),
                format_watch_status(series.get("watch_status", "unknown")),
                format_episode_count(
                    series.get("watched_episodes", 0), series.get("total_episodes", 0)
                ),
                format_completion_percentage(series.get("completion_percentage", 0)),
                str(season_count),
                format_file_size(series.get("total_size_on_disk", 0)),
                last_watched_str,
            )

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
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically confirm removal without prompting"
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
        prunarr series remove [green]--username[/green] \"john\" [green]--yes[/green]

        [dim]# Remove specific series seasons[/dim]
        prunarr series remove [green]--series[/green] \"the office\" [green]--mode[/green] season

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

    logger = get_logger("series", debug=debug)

    logger.info(f"Finding series ready for removal (mode: {removal_mode}, days: {days_watched})...")
    prunarr = PrunArr(settings)

    try:
        # Get series ready for removal
        items_to_remove = prunarr.get_series_ready_for_removal(
            days_watched=days_watched, removal_mode=removal_mode
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

        if not items_to_remove:
            logger.info("No series found that meet the removal criteria")
            return

        # Display what will be removed
        if removal_mode == "series":
            table = Table(title=f"Series Ready for Removal ({len(items_to_remove)} items)")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Title", style="bright_white", min_width=20)
            table.add_column("User", style="blue", width=12)
            table.add_column("Episodes", style="green", width=12)
            table.add_column("Progress", style="green", width=8)
            table.add_column("Last Watched", style="dim", width=12)
            table.add_column("Days Ago", style="yellow", width=8)

            for item in items_to_remove:
                last_watched = item.get("most_recent_watch")
                last_watched_str = last_watched.strftime("%Y-%m-%d") if last_watched else "Never"

                table.add_row(
                    str(item.get("id", "N/A")),
                    str(item.get("title", "N/A")),
                    str(item.get("user", "N/A")),
                    format_episode_count(
                        item.get("watched_episodes", 0), item.get("total_episodes", 0)
                    ),
                    format_completion_percentage(item.get("completion_percentage", 0)),
                    last_watched_str,
                    str(item.get("days_since_watched", "N/A")),
                )

        else:  # season mode
            table = Table(title=f"Seasons Ready for Removal ({len(items_to_remove)} items)")
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Title", style="bright_white", min_width=20)
            table.add_column("Season", style="magenta", width=8)
            table.add_column("User", style="blue", width=12)
            table.add_column("Episodes", style="green", width=12)
            table.add_column("Last Watched", style="dim", width=12)
            table.add_column("Days Ago", style="yellow", width=8)

            for item in items_to_remove:
                last_watched = item.get("most_recent_watch")
                last_watched_str = last_watched.strftime("%Y-%m-%d") if last_watched else "Never"
                season_data = item.get("season_data", {})

                table.add_row(
                    str(item.get("id", "N/A")),
                    str(item.get("title", "N/A")),
                    str(item.get("season_number", "N/A")),
                    str(item.get("user", "N/A")),
                    format_episode_count(
                        season_data.get("watched_by_user", 0), season_data.get("total_episodes", 0)
                    ),
                    last_watched_str,
                    str(item.get("days_since_watched", "N/A")),
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
        if not auto_confirm:
            console.print(
                f"\n[bold red]⚠️  WARNING:[/bold red] This will permanently delete {len(items_to_remove)} {removal_mode}(s) and their files!"
            )

            if not Confirm.ask(
                f"Do you want to proceed with removing these {len(items_to_remove)} {removal_mode}(s)?"
            ):
                logger.info("Removal cancelled by user")
                return

            # Final confirmation for extra safety
            if not Confirm.ask(
                "[bold red]Are you absolutely sure? This cannot be undone![/bold red]"
            ):
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
                        logger.success(f"Removed series: {title} (ID: {series_id})")
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
            logger.success(f"Successfully removed {removed_count} {removal_mode}(s)")
        if failed_count > 0:
            logger.error(f"Failed to remove {failed_count} {removal_mode}(s)")

        # Log applied filters in debug mode
        if debug:
            logger.debug(
                f"Applied filters: days_watched={days_watched}, removal_mode={removal_mode}, "
                f"username={username}, series_name={series_name}, season={season}, "
                f"dry_run={dry_run}, auto_confirm={auto_confirm}"
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

    logger = get_logger("series", debug=debug)

    logger.info(f"Looking up series: {identifier}")
    prunarr = PrunArr(settings)

    # Set debug logger for detailed episode debugging
    if debug:
        prunarr._debug_logger = logger

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

        # Display series header information
        console.print(f"\n[bold cyan]📺 {series_info.get('title', 'Unknown Title')}[/bold cyan]")
        if series_info.get("year"):
            console.print(f"[dim]Released: {series_info['year']}[/dim]")

        if series_watch_data.get("user"):
            console.print(f"[blue]Requested by: {series_watch_data['user']}[/blue]")

        # Show series-level statistics
        total_episodes = detailed_info.get("total_episodes", 0)
        watched_episodes = series_watch_data.get("watched_episodes", 0)
        total_seasons = detailed_info.get("total_seasons", 0)

        console.print(f"[cyan]Seasons:[/cyan] {total_seasons}")
        console.print(
            f"[cyan]Episodes:[/cyan] {format_episode_count(watched_episodes, total_episodes)}"
        )
        console.print(
            f"[cyan]Progress:[/cyan] {format_completion_percentage(series_watch_data.get('completion_percentage', 0))}"
        )

        if series_watch_data.get("most_recent_watch"):
            last_watched = series_watch_data["most_recent_watch"].strftime("%Y-%m-%d")
            console.print(f"[cyan]Last Watched:[/cyan] {last_watched}")

        # Get episode file data for filesize information
        episode_files = prunarr.sonarr.get_episode_files(series_id)
        episode_file_map = {}
        total_series_size = 0
        for file_data in episode_files:
            file_id = file_data.get("id")
            if file_id:
                episode_file_map[file_id] = file_data
                total_series_size += file_data.get("size", 0)

        # Display total series filesize
        if total_series_size > 0:
            console.print(f"[cyan]Total Size:[/cyan] {format_file_size(total_series_size)}")

        # Display seasons and episodes
        seasons = list(seasons_data.values())
        if not seasons:
            console.print("\n[yellow]⚠️  No episode information available[/yellow]")
            return

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
            season_size_str = format_file_size(season_total_size) if season_total_size > 0 else ""
            size_display = f" - {season_size_str}" if season_size_str else ""
            console.print(
                f"\n[bold magenta]Season {season_num}[/bold magenta] "
                f"({format_episode_count(season_watched, season_total)}){size_display}"
            )

            # Create episodes table with forced width to show all columns
            table = Table(show_header=True, header_style="bold cyan", expand=False)
            table.add_column("Ep", style="cyan", width=4)
            table.add_column("Title", style="bright_white", width=25)
            table.add_column("Date", style="cyan", width=10)
            table.add_column("Runtime", style="dim", width=7)
            table.add_column("Status", width=13)
            table.add_column("Size", style="cyan", width=8)
            table.add_column("Watched", style="green", width=12)
            table.add_column("User", style="blue", width=10)

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
                    try:
                        watched_date = datetime.fromtimestamp(int(watched_at)).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        watched_date = "Unknown"
                else:
                    watched_date = "[yellow]Not watched[/yellow]"

                user_display = watched_by if watched_by else "-"

                table.add_row(
                    str(episode_num),
                    title,
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
