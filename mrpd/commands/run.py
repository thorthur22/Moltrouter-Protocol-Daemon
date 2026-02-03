from __future__ import annotations

import asyncio
import json

import httpx
import typer

from mrpd.core.defaults import MRP_DEFAULT_REGISTRY_BASE
from mrpd.core.envelopes import mk_envelope
from mrpd.core.registry import RegistryClient, fetch_manifest, normalize_manifest_endpoints
from mrpd.core.scoring import score_entry


def run(
    intent: str,
    url: str,
    capability: str,
    policy: str | None,
    registry: str | None,
    manifest_url: str | None,
    max_tokens: int | None,
    max_cost: float | None,
) -> None:
    """End-to-end demo: query registry -> discover -> execute -> print evidence.

    v0: expects provider implements /mrp/discover and /mrp/execute per manifest endpoints.
    """

    async def _run() -> int:
        manifest: dict
        if manifest_url:
            manifest = await fetch_manifest(manifest_url)
            manifest = normalize_manifest_endpoints(manifest, manifest_url)
        else:
            client = RegistryClient(base_url=registry) if registry else RegistryClient(base_url=MRP_DEFAULT_REGISTRY_BASE)
            res = await client.query(capability=capability, policy=policy, limit=25)

            scored = [(score_entry(e, capability=capability, policy=policy), e) for e in res.results]
            scored.sort(key=lambda x: x[0], reverse=True)
            if not scored:
                typer.echo("No registry entries matched (requires manifest_url entries).")
                typer.echo("Tip: use --manifest-url http://host/mrp/manifest for local testing.")
                return 1

            # Pick top
            entry = scored[0][1]
            manifest = await fetch_manifest(entry.manifest_url)
            manifest = normalize_manifest_endpoints(manifest, entry.manifest_url)

        endpoints = manifest.get("endpoints") or {}
        discover_url = endpoints.get("discover")
        execute_url = endpoints.get("execute")
        if not discover_url or not execute_url:
            typer.echo("Selected manifest is missing endpoints.discover/execute")
            return 1

        # DISCOVER
        discover_payload: dict = {
            "intent": intent,
            "inputs": [{"type": "url", "value": url}],
            "constraints": {},
        }
        if max_cost is not None:
            discover_payload["constraints"]["max_cost"] = max_cost
        if policy:
            discover_payload["constraints"]["policy"] = [policy]
        # token budget is not in the core schema yet; put it in constraints extension
        if max_tokens is not None:
            discover_payload["constraints"]["max_context_tokens"] = max_tokens

        discover_env = mk_envelope("DISCOVER", discover_payload)

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as http:
            r = await http.post(discover_url, json=discover_env, headers={"Content-Type": "application/mrp+json"})
            r.raise_for_status()
            offer_env = r.json()

        offers = (offer_env.get("payload") or {}).get("offers") or []
        if not offers:
            typer.echo("No offers returned.")
            typer.echo(json.dumps(offer_env, indent=2))
            return 1

        offer = offers[0]
        route_id = offer.get("route_id")
        if not route_id:
            typer.echo("Offer missing route_id")
            return 1

        # EXECUTE
        exec_payload = {
            "route_id": route_id,
            "inputs": [{"type": "url", "value": url}],
            "output_format": "markdown",
        }
        exec_env = mk_envelope("EXECUTE", exec_payload)

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=False) as http:
            r = await http.post(execute_url, json=exec_env, headers={"Content-Type": "application/mrp+json"})
            r.raise_for_status()
            out = r.json()

        typer.echo(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    raise typer.Exit(code=asyncio.run(_run()))
