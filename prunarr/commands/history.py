"""
History command module for PrunArr CLI.

This module provides commands for managing and viewing Tautulli watch history,
including filtering, sorting, and detailed record inspection.
"""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from prunarr.config import Settings
from prunarr.logger import get_logger
from prunarr.prunarr import PrunArr

app = typer.Typer(help="Manage Tautulli history.", rich_markup_mode="rich")
console = Console()


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2h 30m" or "45m")
    """
    if not seconds:
        return "N/A"

    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_timestamp(timestamp: str) -> str:
    """
    Format Unix timestamp to human readable datetime format.

    Args:
        timestamp: Unix timestamp as string

    Returns:
        Formatted datetime string in "YYYY-MM-DD HH:MM" format
    """
    if not timestamp:
        return "N/A"

    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return str(timestamp)


def format_watched_status(status: int) -> str:
    """
    Format watched status with Rich markup colors.

    Args:
        status: Tautulli watched status code
               1 = Fully watched, 0 = Partially watched, other = Stopped

    Returns:
        Colored status string with Rich markup
    """
    if status == 1:
        return "[green]✓ Watched[/green]"
    elif status == 0:
        return "[yellow]⏸ Partial[/yellow]"
    else:
        return "[red]✗ Stopped[/red]"


@app.command("list")
def list_history(
    ctx: typer.Context,
    watched_only: bool = typer.Option(
        False, "--watched", "-w", help="Show only fully watched items"
    ),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Filter by username"),
    media_type: Optional[str] = typer.Option(
        None,
        "--media-type",
        "-m",
        help="Filter by media type (movie, show, episode)",
    ),
    limit: Optional[int] = typer.Option(
        100, "--limit", "-l", help="Limit number of results (default: 100)"
    ),
):
    """
    [bold cyan]List Tautulli watch history with filtering options.[/bold cyan]

    Displays a formatted table of watch history records sorted by [bold]newest first[/bold].
    Supports filtering by watch status, username, media type, and result limits.

    [bold yellow]Table columns:[/bold yellow]
        • [cyan]History ID[/cyan] - for use with 'get' command
        • [cyan]Title[/cyan] and [cyan]Year[/cyan] - media information
        • [cyan]User[/cyan] and [cyan]Type[/cyan] - viewer and media type
        • [cyan]Status[/cyan] and [cyan]Progress[/cyan] - watch completion
        • [cyan]Duration[/cyan] and [cyan]Watched At[/cyan] - timing info
        • [cyan]Platform[/cyan] - playback device

    [bold yellow]Examples:[/bold yellow]
        [dim]# List all history (newest first)[/dim]
        prunarr history list

        [dim]# Show only watched movies from specific user[/dim]
        prunarr history list [green]--watched[/green] [green]--username[/green] "john" [green]--media-type[/green] movie

        [dim]# Get latest 10 records with debug info[/dim]
        prunarr[blue]--debug[/blue] history list [green]--limit[/green] 10

        [dim]# Filter TV episodes for user[/dim]
        prunarr history list [green]--username[/green] "alice" [green]--media-type[/green] episode
    """
    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("history", debug=debug)

    logger.info("Retrieving Tautulli history...")
    prunarr = PrunArr(settings)

    try:
        # Fetch filtered and sorted history records
        history = prunarr.tautulli.get_filtered_history(
            watched_only=watched_only,
            username=username,
            media_type=media_type,
            limit=limit,
        )

        if not history:
            logger.warning("No history records found matching the specified criteria")
            return

        logger.success(f"Found {len(history)} history records")

        # Create Rich table with appropriate styling
        table = Table(title="Tautulli Watch History")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Title", style="bright_white", min_width=25)
        table.add_column("User", style="blue", width=15)
        table.add_column("Type", style="magenta", width=8)
        table.add_column("Year", style="yellow", width=6)
        table.add_column("Status", width=12)
        table.add_column("Progress", style="green", width=8)
        table.add_column("Duration", style="cyan", width=10)
        table.add_column("Watched At", style="dim", width=16)
        table.add_column("Platform", style="blue", width=12)

        # Populate table with history data
        for record in history:
            progress = (
                f"{record.get('percent_complete', 0)}%" if record.get("percent_complete") else "N/A"
            )

            table.add_row(
                str(record.get("history_id", "N/A")),
                str(record.get("title", "N/A")),
                str(record.get("user", "N/A")),
                str(record.get("media_type", "N/A")),
                str(record.get("year", "N/A")),
                format_watched_status(record.get("watched_status", -1)),
                progress,
                format_duration(record.get("duration", 0)),
                format_timestamp(record.get("watched_at", "")),
                str(record.get("platform", "N/A")),
            )

        console.print(table)

        # Log applied filters in debug mode
        if debug:
            logger.debug(
                f"Applied filters: watched_only={watched_only}, "
                f"username={username}, media_type={media_type}, limit={limit}"
            )

    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}")
        raise typer.Exit(1)


@app.command("get")
def get_history_details(
    ctx: typer.Context,
    history_id: int = typer.Argument(..., help="History ID to get details for"),
):
    """
    [bold cyan]Get detailed information about a specific watch history item.[/bold cyan]

    Retrieves comprehensive details for a single history record including all metadata.

    [bold yellow]Information displayed:[/bold yellow]
        • [cyan]Basic media info[/cyan] - title, year, type, IMDb ID
        • [cyan]User details[/cyan] - who watched, user ID
        • [cyan]Watch session[/cyan] - when watched, duration, progress, status
        • [cyan]Technical info[/cyan] - platform, player, network details
        • [cyan]Metadata[/cyan] - summary, ratings, cast, crew, genres

    [bold yellow]Examples:[/bold yellow]
        [dim]# Get details for specific history record[/dim]
        prunarr history get [yellow]2792[/yellow]

        [dim]# With debug logging to see raw data[/dim]
        prunarr[blue]--debug[/blue] history get [yellow]2792[/yellow]

    [bold yellow]Note:[/bold yellow]
        Use the [cyan]History ID[/cyan] shown in the [green]list[/green] command output.
        The command searches through all history records to find the matching entry.
    """
    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("history", debug=debug)

    logger.info(f"Retrieving details for history ID: {history_id}")
    prunarr = PrunArr(settings)

    try:
        # Fetch detailed information for the specific history ID
        details = prunarr.tautulli.get_history_item_details(history_id)

        if not details:
            logger.error(f"No history record found with ID: {history_id}")
            raise typer.Exit(1)

        logger.success("History details retrieved successfully")

        # Create detailed view table without headers
        table = Table(
            title=f"History Details - ID: {history_id}",
            show_header=False,
            box=None,
        )
        table.add_column("Field", style="bold cyan", width=20)
        table.add_column("Value", style="white")

        # Basic media information
        table.add_row("Title", str(details.get("title", "N/A")))
        table.add_row("Year", str(details.get("year", "N/A")))
        table.add_row("Media Type", str(details.get("media_type", "N/A")))
        table.add_row("Rating Key", str(details.get("rating_key", "N/A")))
        table.add_row("IMDb ID", str(details.get("imdb_id", "N/A")))
        table.add_row("", "")  # Visual spacer

        # User information
        table.add_row("User", str(details.get("user", "N/A")))
        table.add_row("User ID", str(details.get("user_id", "N/A")))
        table.add_row("", "")  # Visual spacer

        # Watch session details
        table.add_row("Watched At", format_timestamp(details.get("watched_at", "")))
        table.add_row("Started", format_timestamp(details.get("started", "")))
        table.add_row("Stopped", format_timestamp(details.get("stopped", "")))
        table.add_row("Status", format_watched_status(details.get("watched_status", -1)))
        table.add_row("Progress", f"{details.get('percent_complete', 0)}%")
        table.add_row("Duration", format_duration(details.get("duration", 0)))
        table.add_row("Paused Counter", str(details.get("paused_counter", 0)))
        table.add_row("", "")  # Visual spacer

        # Technical streaming information
        table.add_row("Platform", str(details.get("platform", "N/A")))
        table.add_row("Player", str(details.get("player", "N/A")))
        table.add_row("IP Address", str(details.get("ip_address", "N/A")))
        table.add_row("Location", str(details.get("location", "N/A")))
        table.add_row("Secure", "Yes" if details.get("secure") else "No")
        table.add_row("Relayed", "Yes" if details.get("relayed") else "No")
        table.add_row(
            "Bandwidth",
            f"{details.get('bandwidth', 0)} kbps" if details.get("bandwidth") else "N/A",
        )

        # Optional metadata fields (only show if available)
        if details.get("summary"):
            table.add_row("", "")  # Visual spacer
            summary_text = str(details.get("summary", "N/A"))
            # Truncate long summaries for readability
            if len(summary_text) > 100:
                summary_text = summary_text[:100] + "..."
            table.add_row("Summary", summary_text)

        if details.get("rating"):
            table.add_row("Rating", str(details.get("rating", "N/A")))

        if details.get("content_rating"):
            table.add_row("Content Rating", str(details.get("content_rating", "N/A")))

        if details.get("studio"):
            table.add_row("Studio", str(details.get("studio", "N/A")))

        # Process and display list-type metadata
        if details.get("genres"):
            genres = [g.get("tag", "") for g in details.get("genres", []) if isinstance(g, dict)]
            if genres:
                table.add_row("Genres", ", ".join(genres))

        if details.get("directors"):
            directors = [
                d.get("tag", "") for d in details.get("directors", []) if isinstance(d, dict)
            ]
            if directors:
                table.add_row("Directors", ", ".join(directors))

        if details.get("writers"):
            writers = [w.get("tag", "") for w in details.get("writers", []) if isinstance(w, dict)]
            if writers:
                table.add_row("Writers", ", ".join(writers))

        if details.get("actors"):
            # Limit to first 5 actors to prevent overly long output
            actors = [
                a.get("tag", "") for a in details.get("actors", [])[:5] if isinstance(a, dict)
            ]
            if actors:
                table.add_row("Top Actors", ", ".join(actors))

        console.print(table)

        # Log available data keys in debug mode
        if debug:
            logger.debug(f"Raw details data keys: {list(details.keys())}")

    except Exception as e:
        logger.error(f"Failed to retrieve history details: {str(e)}")
        raise typer.Exit(1)
