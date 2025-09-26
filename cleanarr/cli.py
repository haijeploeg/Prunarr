import typer
from pathlib import Path
from pydantic import ValidationError

from .config import load_settings
from .commands import movies, series, history

app = typer.Typer(help="CleanArr CLI: keep your Radarr and Sonarr libraries clean.")

# Sub-apps toevoegen
app.add_typer(movies.app, name="movies")
app.add_typer(series.app, name="series")
app.add_typer(history.app, name="history")


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        exists=False,
        help="Path to YAML config file",
    ),
):
    """Laad globale configuratie."""
    try:
        ctx.obj = load_settings(str(config) if config else None)
    except FileNotFoundError as e:
        typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except ValidationError as e:
        typer.secho("❌ [ERROR] - Validation error on configuration", fg=typer.colors.RED, err=True)
        for err in e.errors():
            field = err.get("loc", ["?"])[0]
            msg = err.get("msg", "invalid value")
            typer.secho(f"  - {field}: {msg}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
