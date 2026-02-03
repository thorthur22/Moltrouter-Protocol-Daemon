from __future__ import annotations

import asyncio
import json
import time
from urllib.parse import urlparse

import httpx
import typer

from mrpd.core.defaults import MRP_DEFAULT_REGISTRY_BASE


def publish(
    manifest_url: str,
    registry: str | None,
    poll_seconds: float,
) -> None:
    """Self-register a provider in the public registry using HTTP-01 domain control.

    Flow:
    1) POST /mrp/registry/submit {manifest_url}
    2) Operator publishes challenge at /.well-known/mrp-registry-challenge/<token>
    3) POST /mrp/registry/verify {token}

    This is intentionally zero-trust: registry verifies domain control + manifest reachability.
    """

    async def _run() -> int:
        base = (registry or MRP_DEFAULT_REGISTRY_BASE).rstrip("/")
        submit_url = f"{base}/mrp/registry/submit"
        verify_url = f"{base}/mrp/registry/verify"

        # sanity check
        try:
            u = urlparse(manifest_url)
            if u.scheme not in ("http", "https") or not u.netloc:
                raise ValueError("manifest_url must be an http(s) URL")
        except Exception as e:
            typer.echo(f"Invalid manifest_url: {e}")
            return 2

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            r = await client.post(
                submit_url,
                json={"manifest_url": manifest_url},
                headers={"Content-Type": "application/json", "Accept": "application/mrp+json, application/json"},
            )
            if r.status_code >= 400:
                typer.echo(f"Submit failed ({r.status_code}): {r.text}")
                return 1

            data = r.json()
            challenge = (data.get("challenge") or {})
            token = data.get("token")
            expected = challenge.get("expected")
            path = challenge.get("path")
            url = challenge.get("url")

            if not token or not expected or not path or not url:
                typer.echo("Registry returned malformed challenge:")
                typer.echo(json.dumps(data, indent=2))
                return 1

            typer.echo("\n=== MRP Registry HTTP-01 Challenge ===")
            typer.echo(f"Registry: {base}")
            typer.echo(f"Manifest: {manifest_url}")
            typer.echo("")
            typer.echo("Create a public file at:")
            typer.echo(f"  {path}")
            typer.echo("So that this URL returns EXACTLY this string:")
            typer.echo(f"  {url}")
            typer.echo("")
            typer.echo(expected)
            typer.echo("")
            typer.echo("When ready, I will verify and publish the entry.")

            # Poll verify
            while True:
                vr = await client.post(
                    verify_url,
                    json={"token": token},
                    headers={"Content-Type": "application/json", "Accept": "application/mrp+json, application/json"},
                )

                if vr.status_code == 200:
                    out = vr.json()
                    typer.echo("\n✅ Verified and published:")
                    typer.echo(json.dumps(out.get("entry") or out, indent=2, ensure_ascii=False))
                    return 0

                try:
                    out = vr.json()
                except Exception:
                    out = {"error": vr.text}

                err = out.get("error") or out.get("message") or vr.text
                typer.echo(f"Waiting… ({err})")

                await asyncio.sleep(poll_seconds)

    raise typer.Exit(code=asyncio.run(_run()))
