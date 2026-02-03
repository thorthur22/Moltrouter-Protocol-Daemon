from __future__ import annotations

import typer

from mrpd.commands.serve import serve
from mrpd.commands.validate import validate

app = typer.Typer(add_completion=False)


@app.command()
def version() -> None:
    """Print version."""
    typer.echo("mrpd 0.1.0")


@app.command(name="serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Run the MRP HTTP server."""
    serve(host=host, port=port, reload=reload)


@app.command(name="validate")
def validate_cmd(
    path: str = typer.Option("-", "--path", help="JSON file path or '-' for stdin"),
) -> None:
    """Validate an MRP envelope against the bundled JSON Schemas."""
    validate(path)


if __name__ == "__main__":
    app()
