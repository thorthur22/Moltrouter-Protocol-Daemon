from __future__ import annotations

from pathlib import Path

import typer

from mrpd.commands.bridge_openapi import bridge_openapi
from mrpd.commands.publish import publish


def mrpify_openapi(
    spec: str,
    out_dir: str,
    provider_id: str,
    backend_base_url: str | None,
    capability_prefix: str | None,
    public_base_url: str | None,
    do_publish: bool,
    yes: bool,
    registry: str | None,
    poll_seconds: float,
) -> None:
    """End-to-end developer flow for OpenAPI -> MRP.

    1) Generate a bridge wrapper (FastAPI) from an OpenAPI spec
    2) Print the manifest URLs you should publish after deploying
    3) Optionally run `mrpd publish` for each manifest URL (requires public HTTPS deploy)

    Notes:
    - v0 uses one MRP capability per OpenAPI operationId (optionally prefixed)
    - publish requires the manifest URL to be publicly reachable on HTTPS
    """

    bridge_openapi(
        spec=spec,
        out_dir=out_dir,
        provider_id=provider_id,
        backend_base_url=backend_base_url,
        capability_prefix=capability_prefix,
    )

    manifests_dir = Path(out_dir).resolve() / "mrp_manifests"
    caps = sorted([p.stem for p in manifests_dir.glob("*.json")])
    if not caps:
        raise typer.Exit(code=2)

    typer.echo("")
    typer.echo("Generated capabilities:")
    for c in caps:
        typer.echo(f"- {c}")

    typer.echo("")
    typer.echo("Next: deploy the generated app, then publish these manifest URLs:")

    if public_base_url:
        base = public_base_url.rstrip("/")
        urls = [f"{base}/mrp/manifest/{c}" for c in caps]
        for u in urls:
            typer.echo(f"  mrpd publish --manifest-url {u}")
    else:
        urls = []
        typer.echo("  (pass --public-base-url https://YOUR_DOMAIN to print full publish commands)")

    if do_publish:
        if not public_base_url:
            typer.echo("\nERROR: --publish requires --public-base-url")
            raise typer.Exit(code=2)

        if not yes:
            ok = typer.confirm(
                f"Run mrpd publish now for {len(urls)} manifest URLs? (requires public HTTPS + http-01 hosting)",
                default=False,
            )
            if not ok:
                raise typer.Exit(code=1)

        for u in urls:
            typer.echo("")
            typer.echo(f"Publishing: {u}")
            publish(manifest_url=u, registry=registry, poll_seconds=poll_seconds)
