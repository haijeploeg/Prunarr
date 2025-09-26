import typer
from rich.console import Console
from rich.table import Table

from cleanarr.cleanarr import CleanArr
from cleanarr.config import Settings

console = Console()
app = typer.Typer(help="Manage movies in Radarr.")

@app.command("list")
def list_movies(
    ctx: typer.Context,
    user: list[str] = typer.Option(
        None,
        "--user",
        "-u",
        help="Filter results on specific user(s). Can be supplied multiple times.",
    ),
):
    """List all requested movies in Radarr (optioneel gefilterd op gebruiker)."""
    settings: Settings = ctx.obj
    cleanarr = CleanArr(settings)

    movies = cleanarr.radarr_movies

    if user:
        movies = [m for m in movies if m.get("user", "") in user]

    if not movies:
        typer.secho(f"No requested movies found", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    table = Table("Title", "Requested by")
    for movie in movies:
        table.add_row(movie.get("title", ""), movie.get("user", ""))

    console.print(table)

@app.command("remove")
def remove_movies(ctx: typer.Context):
    """Remove watched movies after x days."""
    settings: Settings = ctx.obj
    cleanarr = CleanArr(settings)
    removed = cleanarr.remove_watched_movies()
    typer.secho(f"✅ {len(removed)} movie removed", fg=typer.colors.GREEN)
