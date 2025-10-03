"""
Providers command module for PrunArr CLI.

This module provides commands for managing and checking streaming providers
via JustWatch integration. Users can list available providers for their locale
and check streaming availability for specific content.
"""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from prunarr.config import Settings
from prunarr.justwatch import JustWatchClient
from prunarr.logger import get_logger
from prunarr.services.streaming_checker import StreamingChecker
from prunarr.utils.validators import validate_output_format

console = Console()
app = typer.Typer(help="Manage streaming providers (JustWatch).", rich_markup_mode="rich")


@app.command("list")
def list_providers(
    ctx: typer.Context,
    locale: Optional[str] = typer.Option(
        None, "--locale", "-l", help="Override locale (e.g., en_US, en_GB, de_DE)"
    ),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]List all available streaming providers for a locale.[/bold cyan]

    Shows all streaming providers available in JustWatch for the specified locale.
    By default uses the locale configured in your settings. Filters to show only
    FLATRATE (subscription) providers.

    [bold yellow]Output columns:[/bold yellow]
        • [cyan]Technical Name[/cyan] - Use this in streaming_providers config
        • [cyan]Short Name[/cyan] - Provider abbreviation
        • [cyan]Full Name[/cyan] - Complete provider name

    [bold yellow]Examples:[/bold yellow]
        [dim]# List providers for configured locale[/dim]
        prunarr providers list

        [dim]# List providers for specific locale[/dim]
        prunarr providers list [green]--locale[/green] en_GB

        [dim]# Get JSON output for scripting[/dim]
        prunarr providers list [green]--output[/green] json

        [dim]# Find Netflix technical name[/dim]
        prunarr providers list | grep -i netflix
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("providers", debug=debug, log_level=settings.log_level)

    # Validate output format
    validate_output_format(output, logger)

    # Use provided locale or fall back to settings
    use_locale = locale or settings.streaming_locale

    logger.info(f"Fetching available providers for locale: {use_locale}")

    try:
        # Create JustWatch client
        client = JustWatchClient(locale=use_locale, logger=logger)

        # Get all providers
        all_providers = client.get_providers()

        # Filter to only FLATRATE (subscription) providers
        providers = [p for p in all_providers if "FLATRATE" in p.monetization_types]

        if not providers:
            logger.warning(f"No FLATRATE providers found for locale: {use_locale}")
            return

        logger.info(f"Found {len(providers)} FLATRATE providers")

        # Output based on format
        if output == "json":
            json_output = [
                {
                    "technical_name": p.technical_name,
                    "short_name": p.short_name,
                    "clear_name": p.clear_name,
                }
                for p in providers
            ]
            print(json.dumps(json_output, indent=2))
        else:
            # Create Rich table
            table = Table(
                title=f"Streaming Providers ({use_locale})",
                show_header=True,
                header_style="bold cyan",
            )

            table.add_column("Technical Name", style="green", no_wrap=True)
            table.add_column("Short Name", style="yellow")
            table.add_column("Full Name", style="white")

            # Add rows sorted by clear name
            for provider in sorted(providers, key=lambda p: p.clear_name):
                table.add_row(
                    provider.technical_name,
                    provider.short_name,
                    provider.clear_name,
                )

            console.print(table)

            # Show usage hint
            console.print(
                f"\n[dim]Tip: Add provider technical names to streaming_providers in config.yaml[/dim]"
            )

    except Exception as e:
        logger.error(f"Failed to fetch providers: {str(e)}")
        raise typer.Exit(1)


@app.command("check")
def check_availability(
    ctx: typer.Context,
    title: str = typer.Argument(..., help="Movie or series title to check"),
    media_type: str = typer.Option("movie", "--type", "-t", help="Media type: movie or series"),
    year: Optional[int] = typer.Option(None, "--year", "-y", help="Release year for movies"),
    locale: Optional[str] = typer.Option(
        None, "--locale", "-l", help="Override locale (e.g., en_US, en_GB)"
    ),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table or json"),
):
    """
    [bold cyan]Check streaming availability for specific content.[/bold cyan]

    Queries JustWatch to see which streaming providers have the specified content.
    Shows all available providers, not just those configured in settings.

    [bold yellow]Media Types:[/bold yellow]
        • [cyan]movie[/cyan] - Check movie availability (default)
        • [cyan]series[/cyan] - Check TV series availability

    [bold yellow]Examples:[/bold yellow]
        [dim]# Check if a movie is available[/dim]
        prunarr providers check \"The Matrix\"

        [dim]# Check with specific year for better matching[/dim]
        prunarr providers check \"The Matrix\" [green]--year[/green] 1999

        [dim]# Check TV series availability[/dim]
        prunarr providers check \"Breaking Bad\" [green]--type[/green] series

        [dim]# Check in different locale[/dim]
        prunarr providers check \"Dark\" [green]--type[/green] series [green]--locale[/green] de_DE

        [dim]# Get JSON output[/dim]
        prunarr providers check \"Inception\" [green]--output[/green] json
    """
    context_obj = ctx.obj
    settings: Settings = context_obj["settings"]
    debug: bool = context_obj["debug"]

    logger = get_logger("providers", debug=debug, log_level=settings.log_level)

    # Validate output format and media type
    validate_output_format(output, logger)

    if media_type.lower() not in ["movie", "series", "show", "tv"]:
        logger.error(f"Invalid media type: {media_type}. Must be 'movie' or 'series'")
        raise typer.Exit(1)

    # Normalize media type
    if media_type.lower() in ["show", "tv"]:
        media_type = "series"

    # Use provided locale or fall back to settings
    use_locale = locale or settings.streaming_locale

    logger.info(f"Checking availability for: {title} ({media_type})")

    try:
        # Create JustWatch client (without provider filtering to see all)
        client = JustWatchClient(locale=use_locale, logger=logger)

        # Search for the content
        content_type = "MOVIE" if media_type == "movie" else "SHOW"
        search_results = client.search_title(title, year, content_type)

        if not search_results:
            logger.warning(f"No results found for: {title}")
            console.print(f"[yellow]⚠️  No results found for '{title}'[/yellow]")
            return

        # Use the first (most popular) result
        best_match = search_results[0]
        logger.info(f"Found: {best_match.title} ({best_match.release_year})")

        # Get all streaming offers (no provider filter)
        offers = client.get_offers(best_match.id)

        if not offers:
            console.print(
                f"[yellow]'{best_match.title}' ({best_match.release_year}) is not available on any streaming service[/yellow]"
            )
            return

        # Group offers by provider
        providers_dict = {}
        for offer in offers:
            provider = offer.provider_short_name
            if provider not in providers_dict:
                providers_dict[provider] = []
            providers_dict[provider].append(offer.monetization_type)

        # Output based on format
        if output == "json":
            json_output = {
                "title": best_match.title,
                "year": best_match.release_year,
                "type": best_match.object_type,
                "justwatch_id": best_match.id,
                "locale": use_locale,
                "available": len(providers_dict) > 0,
                "providers": [
                    {
                        "name": provider,
                        "monetization_types": list(set(types)),
                    }
                    for provider, types in providers_dict.items()
                ],
            }
            print(json.dumps(json_output, indent=2))
        else:
            # Create Rich table
            table = Table(
                title=f"Streaming Availability: {best_match.title} ({best_match.release_year})",
                show_header=True,
                header_style="bold cyan",
            )

            table.add_column("Provider", style="green")
            table.add_column("Availability", style="yellow")

            # Add rows sorted by provider name
            for provider in sorted(providers_dict.keys()):
                types = list(set(providers_dict[provider]))
                availability = ", ".join(types)
                table.add_row(provider, availability)

            console.print(table)

            # Show summary
            console.print(
                f"\n[green]✓[/green] Available on {len(providers_dict)} provider(s) in {use_locale}"
            )

    except Exception as e:
        logger.error(f"Failed to check availability: {str(e)}")
        raise typer.Exit(1)
