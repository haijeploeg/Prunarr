"""
PrunArr CLI main application module.

This module serves as the entry point for the PrunArr command-line interface,
providing a unified interface for managing media libraries in Radarr and Sonarr
based on watch status from Tautulli.

The CLI supports:
- Movie management (list, remove watched movies)
- TV series management (list, remove watched series/seasons)
- Watch history analysis and reporting
- Flexible configuration via YAML files or environment variables
- Debug logging for troubleshooting
"""

import typer
from typing import Optional
from pathlib import Path
from pydantic import ValidationError

from prunarr.config import load_settings
from prunarr.commands import movies, series, history
from prunarr.logger import get_logger
app = typer.Typer(
    help="[bold cyan]PrunArr CLI[/bold cyan]: Automated media library cleanup for Radarr and Sonarr based on Tautulli watch status.",
    rich_markup_mode="rich"
)

# Register command sub-applications
app.add_typer(movies.app, name="movies", help="Manage movies in Radarr")
app.add_typer(series.app, name="series", help="Manage TV series in Sonarr")
app.add_typer(history.app, name="history", help="Analyze watch history from Tautulli")


@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        exists=False,
        help="Path to YAML configuration file. If not specified, uses environment variables.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging for detailed output and troubleshooting",
    ),
) -> None:
    """
    Load global configuration and initialize the CLI application.

    This callback function runs before any subcommand and is responsible for:
    - Loading configuration from YAML file or environment variables
    - Validating configuration settings
    - Setting up the global context for commands
    - Enabling debug mode if requested

    Args:
        ctx: Typer context object for storing global state
        config: Optional path to YAML configuration file
        debug: Enable debug logging across all commands

    Raises:
        typer.Exit: On configuration errors or validation failures
    """
    # Initialize logger early to handle any configuration errors
    logger = get_logger("cli", debug=debug)

    try:
        # Load settings from config file or environment variables
        config_path = str(config) if config else None
        settings = load_settings(config_path)

        # Store settings and debug flag in context for access by subcommands
        ctx.obj = {
            "settings": settings,
            "debug": debug
        }

        if debug:
            logger.debug("Debug mode enabled for CLI session")

        if config_path:
            logger.debug(f"Loaded configuration from: {config_path}")
        else:
            logger.debug("Using environment variables for configuration")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise typer.Exit(code=1)

    except ValidationError as e:
        logger.error("Configuration validation failed")
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0]
            message = error.get("msg", "invalid value")
            logger.error(f"  {field}: {message}")
        raise typer.Exit(code=1)

    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        if debug:
            logger.debug(f"Exception details: {type(e).__name__}: {e}")
        raise typer.Exit(code=1)
