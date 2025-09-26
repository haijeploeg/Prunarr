import typer

app = typer.Typer(help="Manage TV shows in Sonarr.")

@app.command("list")
def list_series():
    typer.echo("TV show list (not implemented yet).")
