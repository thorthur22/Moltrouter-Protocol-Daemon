from __future__ import annotations

import json
import sys
from importlib import resources

import typer

from mrpd.core.schema import validate_envelope


def _validate_one(raw: str, label: str, *, quiet: bool = False) -> bool:
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as e:
        if not quiet:
            typer.echo(f"INVALID ({label}): invalid JSON: {e}")
        return False

    try:
        validate_envelope(envelope)
    except Exception as e:
        if not quiet:
            typer.echo(f"INVALID ({label}): {e}")
        return False

    return True


def validate(path: str, fixtures: bool = False) -> None:
    """Validate an envelope file or run bundled fixture validation."""

    if fixtures:
        base = resources.files("mrpd.spec").joinpath("fixtures")
        valid_dir = base.joinpath("valid")
        invalid_dir = base.joinpath("invalid")

        ok = True

        # Valid fixtures must pass
        for p in sorted(valid_dir.glob("*.json")):
            raw = p.read_text(encoding="utf-8")
            if not _validate_one(raw, f"valid/{p.name}"):
                ok = False

        # Invalid fixtures must fail
        for p in sorted(invalid_dir.glob("*.json")):
            raw = p.read_text(encoding="utf-8")
            if _validate_one(raw, f"invalid/{p.name}", quiet=True):
                typer.echo(f"INVALID FIXTURE PASSED ({p.name})")
                ok = False
            else:
                typer.echo(f"EXPECTED FAIL ({p.name})")

        if not ok:
            raise typer.Exit(code=1)

        typer.echo("OK (fixtures)")
        return

    if path == "-":
        raw = sys.stdin.read()
        label = "stdin"
    else:
        raw = open(path, "r", encoding="utf-8").read()
        label = path

    if not _validate_one(raw, label):
        raise typer.Exit(code=1)

    typer.echo("OK")
