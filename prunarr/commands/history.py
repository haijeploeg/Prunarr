"""
History command module for PrunArr CLI.

This module provides commands for managing and viewing Tautulli watch history,
including filtering, sorting, and detailed record inspection.
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
    format_duration,
    format_history_watch_status,
    format_timestamp,
    safe_get,
    safe_str,
)
from prunarr.utils.validators import validate_output_format, validate_media_type
from prunarr.utils.serializers import prepare_datetime_for_json
from prunarr.utils.tables import create_history_table, create_history_details_table

app = typer.Typer(help="Manage Tautulli history.", rich_markup_mode="rich")
console = Console()


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
    all_records: bool = typer.Option(
        False, "--all", "-a", help="Fetch all available records (ignores --limit)"
    ),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
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
        [dim]# List recent history (default: 100 records)[/dim]
        prunarr history list

        [dim]# Get ALL available records (no limit)[/dim]
        prunarr history list [green]--all[/green]

        [dim]# Show only watched movies from specific user[/dim]
        prunarr history list [green]--watched[/green] [green]--username[/green] "john" [green]--media-type[/green] movie

        [dim]# Get all records for a specific user[/dim]
        prunarr history list [green]--all[/green] [green]--username[/green] "alice"

        [dim]# Custom limit (ignores --all if both specified)[/dim]
        prunarr history list [green]--limit[/green] 500

        [dim]# Filter TV episodes for user with debug info[/dim]
        prunarr[blue]--debug[/blue] history list [green]--username[/green] "alice" [green]--media-type[/green] episode [green]--all[/green]
    """
    # Extract settings and debug flag from global context
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("history", debug=debug, log_level=settings.log_level)

    # Validate output format using shared validator
    validate_output_format(output, logger)

    # Validate that --all and --limit are not used together
    if all_records and limit != 100:  # 100 is the default value
        logger.error("Cannot use both --all and --limit together. Use either --all for all records or --limit for a specific number.")
        raise typer.Exit(1)

    if all_records:
        logger.info("Retrieving ALL Tautulli history records...")
    else:
        logger.info(f"Retrieving Tautulli history (limit: {limit})...")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Determine the limit to use
        effective_limit = None if all_records else limit

        # Fetch filtered and sorted history records
        history = prunarr.tautulli.get_filtered_history(
            watched_only=watched_only,
            username=username,
            media_type=media_type,
            limit=effective_limit,
        )

        # Check and log cache status (history uses dynamic keys based on filters)
        # So we just check if cache is enabled and has any files
        if prunarr.cache_manager and prunarr.cache_manager.is_enabled():
            cache_stats = prunarr.cache_manager.get_stats()
            if cache_stats.get('file_count', 0) > 0:
                logger.info("[dim](using cached data)[/dim]")

        if not history:
            logger.warning("No history records found matching the specified criteria")
            return

        logger.info(f"Found {len(history)} history records")

        # Output based on format
        if output == "json":
            # Prepare JSON-serializable data using shared serializer
            from prunarr.utils.serializers import prepare_history_for_json
            json_output = [prepare_history_for_json(record) for record in history]
            print(json.dumps(json_output, indent=2))
        else:
            # Create Rich table using factory
            table = create_history_table()

            # Populate table with history data
            for record in history:
                progress = (
                    f"{record.get('percent_complete', 0)}%" if record.get("percent_complete") else "N/A"
                )

                table.add_row(
                    safe_get(record, "history_id"),
                    safe_get(record, "title"),
                    safe_get(record, "user"),
                    safe_get(record, "media_type"),
                    format_history_watch_status(record.get("watched_status", -1)),
                    progress,
                    format_duration(record.get("duration", 0)),
                    format_timestamp(record.get("watched_at", "")),
                    safe_get(record, "platform"),
                )

            console.print(table)

        # Log applied filters in debug mode
        if debug:
            limit_info = "all records" if all_records else f"limit={limit}"
            logger.debug(
                f"Applied filters: watched_only={watched_only}, "
                f"username={username}, media_type={media_type}, {limit_info}"
            )

    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}")
        raise typer.Exit(1)


@app.command("get")
def get_history_details(
    ctx: typer.Context,
    history_id: int = typer.Argument(..., help="History ID to get details for"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
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

    logger = get_logger("history", debug=debug, log_level=settings.log_level)

    # Validate output format using shared validator
    validate_output_format(output, logger)

    logger.info(f"Retrieving details for history ID: {history_id}")
    prunarr = PrunArr(settings, debug=debug)

    try:
        # Fetch detailed information for the specific history ID
        details = prunarr.tautulli.get_history_item_details(history_id)

        if not details:
            logger.error(f"No history record found with ID: {history_id}")
            raise typer.Exit(1)

        logger.info("History details retrieved successfully")

        # Output based on format
        if output == "json":
            # Prepare JSON-serializable data with all available fields
            json_output = {
                "history_id": history_id,
                "title": details.get("title"),
                "year": details.get("year"),
                "media_type": details.get("media_type"),
                "rating_key": details.get("rating_key"),
                "imdb_id": details.get("imdb_id"),
                "user": details.get("user"),
                "user_id": details.get("user_id"),
                "percent_complete": details.get("percent_complete"),
                "duration": details.get("duration"),
                "paused_counter": details.get("paused_counter"),
                "watched_status": details.get("watched_status"),
                "platform": details.get("platform"),
                "player": details.get("player"),
                "ip_address": details.get("ip_address"),
                "location": details.get("location"),
                "secure": details.get("secure"),
                "relayed": details.get("relayed"),
                "bandwidth": details.get("bandwidth"),
            }

            # Parse timestamps
            for timestamp_field in ["watched_at", "started", "stopped"]:
                if details.get(timestamp_field):
                    try:
                        ts_dt = datetime.fromtimestamp(int(details.get(timestamp_field)))
                        json_output[timestamp_field] = ts_dt.isoformat()
                    except (ValueError, TypeError):
                        json_output[timestamp_field] = None
                else:
                    json_output[timestamp_field] = None

            # Add optional metadata fields
            if details.get("summary"):
                json_output["summary"] = details.get("summary")
            if details.get("rating"):
                json_output["rating"] = details.get("rating")
            if details.get("content_rating"):
                json_output["content_rating"] = details.get("content_rating")
            if details.get("studio"):
                json_output["studio"] = details.get("studio")
            if details.get("genres"):
                json_output["genres"] = [g.get("tag") for g in details.get("genres", []) if isinstance(g, dict)]
            if details.get("directors"):
                json_output["directors"] = [d.get("tag") for d in details.get("directors", []) if isinstance(d, dict)]
            if details.get("writers"):
                json_output["writers"] = [w.get("tag") for w in details.get("writers", []) if isinstance(w, dict)]
            if details.get("actors"):
                json_output["actors"] = [a.get("tag") for a in details.get("actors", []) if isinstance(a, dict)]

            print(json.dumps(json_output, indent=2))
        else:
            # Create detailed view table using factory
            table = create_history_details_table(history_id)

            # Basic media information
            table.add_row("Title", safe_get(details, "title"))
            table.add_row("Year", safe_get(details, "year"))
            table.add_row("Media Type", safe_get(details, "media_type"))
            table.add_row("Rating Key", safe_get(details, "rating_key"))
            table.add_row("IMDb ID", safe_get(details, "imdb_id"))
            table.add_row("", "")  # Visual spacer

            # User information
            table.add_row("User", safe_get(details, "user"))
            table.add_row("User ID", safe_get(details, "user_id"))
            table.add_row("", "")  # Visual spacer

            # Watch session details
            table.add_row("Watched At", format_timestamp(details.get("watched_at", "")))
            table.add_row("Started", format_timestamp(details.get("started", "")))
            table.add_row("Stopped", format_timestamp(details.get("stopped", "")))
            table.add_row("Status", format_history_watch_status(details.get("watched_status", -1)))
            table.add_row("Progress", f"{details.get('percent_complete', 0)}%")
            table.add_row("Duration", format_duration(details.get("duration", 0)))
            table.add_row("Paused Counter", str(details.get("paused_counter", 0)))
            table.add_row("", "")  # Visual spacer

            # Technical streaming information
            table.add_row("Platform", safe_get(details, "platform"))
            table.add_row("Player", safe_get(details, "player"))
            table.add_row("IP Address", safe_get(details, "ip_address"))
            table.add_row("Location", safe_get(details, "location"))
            table.add_row("Secure", "Yes" if details.get("secure") else "No")
            table.add_row("Relayed", "Yes" if details.get("relayed") else "No")
            table.add_row(
                "Bandwidth",
                f"{details.get('bandwidth', 0)} kbps" if details.get("bandwidth") else "N/A",
            )

            # Optional metadata fields (only show if available)
            if details.get("summary"):
                table.add_row("", "")  # Visual spacer
                summary_text = safe_get(details, "summary")
                # Truncate long summaries for readability
                if len(summary_text) > 100:
                    summary_text = summary_text[:100] + "..."
                table.add_row("Summary", summary_text)

            if details.get("rating"):
                table.add_row("Rating", safe_get(details, "rating"))

            if details.get("content_rating"):
                table.add_row("Content Rating", safe_get(details, "content_rating"))

            if details.get("studio"):
                table.add_row("Studio", safe_get(details, "studio"))

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
