import typer
from cleanarr.cleanarr import CleanArr
from cleanarr.config import Settings

app = typer.Typer(help="Manage Tautulli history.")

@app.command("list")
def list_history(ctx: typer.Context):
    """Toon bekeken films uit Tautulli geschiedenis."""
    settings: Settings = ctx.obj
    cleanarr = CleanArr(settings)
    history = cleanarr.tautulli.get_movie_completed_history()
    for h in history:
        typer.echo(h)