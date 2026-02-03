from __future__ import annotations

import asyncio

import typer

from mrpd.core.registry import RegistryClient, fetch_manifest
from mrpd.core.scoring import score_entry


def route(
    intent: str,
    capability: str | None,
    policy: str | None,
    registry: str | None,
    limit: int,
    bootstrap_raw: str | None,
) -> None:
    """Discover candidates for an intent from the registry and print ranked results.

    v0: discovery + ranking + manifest fetch.
    v1: negotiate/execute.
    """

    async def _run() -> int:
        if bootstrap_raw:
            import os

            os.environ["MRP_BOOTSTRAP_REGISTRY_RAW"] = bootstrap_raw
        client = RegistryClient(base_url=registry) if registry else RegistryClient()
        try:
            res = await client.query(capability=capability, policy=policy, limit=limit)
        except Exception as ex:
            typer.echo(f"Registry query failed: {ex}")
            return 1

        scored = []
        for e in res.results:
            s = score_entry(e, capability=capability, policy=policy)
            scored.append((s, e))
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            typer.echo("No registry entries matched (and entries must include manifest_url).")
            return 1

        typer.echo(f"Intent: {intent}")
        if capability:
            typer.echo(f"Filter capability: {capability}")
        if policy:
            typer.echo(f"Filter policy: {policy}")
        typer.echo("")

        for s, e in scored[:limit]:
            typer.echo(f"- score={s:.2f} id={e.id} name={e.name}")
            typer.echo(f"  manifest: {e.manifest_url}")
            if e.repo:
                typer.echo(f"  repo: {e.repo}")
            # Fetch manifest to prove it resolves + show declared endpoints/capabilities
            try:
                manifest = await fetch_manifest(e.manifest_url)
                caps = manifest.get("capability") or manifest.get("capability_id")
                typer.echo(f"  manifest.capability: {caps}")
                endpoints = manifest.get("endpoints") or {}
                if endpoints:
                    typer.echo(f"  endpoints: {endpoints}")
            except Exception as ex:
                typer.echo(f"  manifest fetch FAILED: {ex}")
            typer.echo("")

        return 0

    raise typer.Exit(code=asyncio.run(_run()))
