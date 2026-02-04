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
            typer.echo("")
            typer.echo("Notes:")
            typer.echo("- The challenge URL must return ONLY the expected string above (raw text).")
            typer.echo("- No JSON. No quotes. Avoid a trailing newline if you can.")
            typer.echo("- Re-running publish generates a NEW token. Old tokens won't verify.")

            async def _debug_fetch_challenge(challenge_url: str) -> None:
                try:
                    fr = await client.get(
                        challenge_url,
                        headers={"Accept": "text/plain", "User-Agent": "mrpd/0.1"},
                    )
                    body = fr.text
                    preview = body.replace("\n", "\\n")
                    if len(preview) > 200:
                        preview = preview[:200] + "…"
                    typer.echo(
                        f"  debug: GET {challenge_url} -> {fr.status_code}, len={len(body)} body='{preview}'"
                    )
                except Exception as e:
                    typer.echo(f"  debug: GET {challenge_url} failed: {e}")

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

                # Improve debugging for the most common failure modes.
                if isinstance(out, dict):
                    ch_url = out.get("challenge_url") or out.get("challengeUrl")
                    got = out.get("got")
                    exp = out.get("expected")
                    if ch_url and (err in ("challenge_not_found", "challenge_mismatch") or got or exp):
                        if exp and got:
                            typer.echo(f"  expected: {str(exp)[:200]}")
                            typer.echo(f"  got     : {str(got)[:200]}")
                        await _debug_fetch_challenge(str(ch_url))

                await asyncio.sleep(poll_seconds)

    raise typer.Exit(code=asyncio.run(_run()))
