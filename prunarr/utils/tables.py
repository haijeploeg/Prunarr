"""
Table factory utilities for PrunArr CLI application.

This module provides reusable table creation functions for consistent
table structures across all command modules.
"""

from rich.table import Table


def create_movies_table(title: str = "Radarr Movies") -> Table:
    """
    Create standard movies table with consistent columns.

    Args:
        title: Table title (default: "Radarr Movies")

    Returns:
        Configured Rich Table for movies display
    """
    table = Table(title=title)
    table.add_column("Title", style="bright_white")
    table.add_column("Year", style="yellow")
    table.add_column("User", style="blue")
    table.add_column("Watch Status")
    table.add_column("Watched By", style="cyan")
    table.add_column("Days Ago", style="green")
    table.add_column("File Size", style="magenta")
    table.add_column("Added", style="dim")
    return table


def create_series_table(title: str = "Sonarr TV Series") -> Table:
    """
    Create standard series table with consistent columns.

    Args:
        title: Table title (default: "Sonarr TV Series")

    Returns:
        Configured Rich Table for series display
    """
    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="bright_white")
    table.add_column("User", style="blue")
    table.add_column("Status")
    table.add_column("Episodes", style="cyan")
    table.add_column("Progress", style="green")
    table.add_column("Seasons", style="magenta")
    table.add_column("Size", style="cyan")
    table.add_column("Last Watched", style="dim")
    return table


def create_series_removal_table(title: str, mode: str = "series") -> Table:
    """
    Create table for series removal preview.

    Args:
        title: Table title
        mode: Removal mode ("series" or "season")

    Returns:
        Configured Rich Table for series removal preview
    """
    table = Table(title=title)

    if mode == "series":
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bright_white")
        table.add_column("User", style="blue")
        table.add_column("Episodes", style="green")
        table.add_column("Progress", style="green")
        table.add_column("Last Watched", style="dim")
        table.add_column("Days Ago", style="yellow")
    else:  # season mode
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bright_white")
        table.add_column("Season", style="magenta")
        table.add_column("User", style="blue")
        table.add_column("Episodes", style="green")
        table.add_column("Last Watched", style="dim")
        table.add_column("Days Ago", style="yellow")

    return table


def create_episodes_table() -> Table:
    """
    Create standard episodes table with consistent columns.

    Returns:
        Configured Rich Table for episode details display
    """
    table = Table(show_header=True, header_style="bold cyan", expand=False)
    table.add_column("Ep", style="cyan")
    table.add_column("Title", style="bright_white")
    table.add_column("Date", style="cyan")
    table.add_column("Runtime", style="dim")
    table.add_column("Status")
    table.add_column("Size", style="cyan")
    table.add_column("Watched", style="green")
    table.add_column("User", style="blue")
    return table


def create_history_table(title: str = "Tautulli Watch History") -> Table:
    """
    Create standard history table with consistent columns.

    Args:
        title: Table title (default: "Tautulli Watch History")

    Returns:
        Configured Rich Table for history display
    """
    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="bright_white")
    table.add_column("User", style="blue")
    table.add_column("Type", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Progress", style="green", justify="center")
    table.add_column("Duration", style="cyan", justify="center")
    table.add_column("Watched At", style="dim")
    table.add_column("Platform", style="blue")
    return table


def create_history_details_table(history_id: int) -> Table:
    """
    Create details table for history record inspection.

    Args:
        history_id: History ID for the table title

    Returns:
        Configured Rich Table for history details (no headers, key-value format)
    """
    table = Table(
        title=f"History Details - ID: {history_id}",
        show_header=False,
        box=None,
    )
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")
    return table
