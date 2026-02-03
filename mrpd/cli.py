from __future__ import annotations

import typer

from mrpd.commands.serve import serve

app = typer.Typer(add_completion=False)


@app.command()
def version() -> None:
    """Print version."""
    typer.echo("mrpd 0.1.0")


@app.command()
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Run the MRP HTTP server."""
    serve(host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
