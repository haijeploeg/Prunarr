"""
Main entry point module for PrunArr CLI application.

This module serves as the primary entry point for the PrunArr command-line interface,
providing a clean separation between the CLI implementation and the main execution logic.
It handles the application startup and delegates all functionality to the CLI module.

The main function serves as the console script entry point defined in pyproject.toml,
allowing the application to be executed as 'prunarr' after installation.

Usage:
    Direct execution:
    $ python -m prunarr.main

    Console script (after pip install):
    $ prunarr

    With arguments:
    $ prunarr --config config.yaml series list
"""

from typing import NoReturn

from prunarr.cli import app


def main() -> NoReturn:
    """
    Execute the PrunArr CLI application.

    This function serves as the main entry point for the PrunArr command-line interface.
    It initializes and runs the Typer application, handling all command parsing,
    validation, and execution through the CLI module.

    The function does not return normally as it delegates control to the Typer
    application which handles command execution and process termination.

    Raises:
        SystemExit: When the CLI application completes or encounters an error

    Examples:
        Direct function call:
        >>> main()  # Runs the CLI with sys.argv

        Module execution:
        $ python -m prunarr.main --help
    """
    app()


if __name__ == "__main__":
    main()
