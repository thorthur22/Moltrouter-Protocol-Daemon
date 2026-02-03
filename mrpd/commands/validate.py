from __future__ import annotations

import json
import sys

import typer

from mrpd.core.schema import validate_envelope


def validate(path: str) -> None:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = open(path, "r", encoding="utf-8").read()

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"Invalid JSON: {e}")

    try:
        validate_envelope(envelope)
    except Exception as e:
        # Keep it simple for now; later we can emit structured validation errors.
        typer.echo(f"INVALID: {e}")
        raise typer.Exit(code=1)

    typer.echo("OK")
