from __future__ import annotations

import asyncio
import json
import uuid

import httpx
import typer

from mrpd.core.defaults import MRP_DEFAULT_REGISTRY_BASE
from mrpd.core.envelopes import mk_envelope
from mrpd.core.evidence import write_evidence_bundle
from mrpd.core.registry import RegistryClient, fetch_manifest, normalize_manifest_endpoints
from mrpd.core.scoring import rank_entries
from mrpd.core.util import utc_now_rfc3339


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
        receiver_id: str | None = None
        if manifest_url:
            typer.echo("Fetching manifest...")
            manifest = await fetch_manifest(manifest_url)
            manifest = normalize_manifest_endpoints(manifest, manifest_url)
        else:
            client = RegistryClient(base_url=registry) if registry else RegistryClient(base_url=MRP_DEFAULT_REGISTRY_BASE)
            typer.echo("Querying registry...")
            res = await client.query(capability=capability, policy=policy, limit=25)

            ranked = rank_entries(res.results, capability=capability, policy=policy)
            satisfying = [r for r in ranked if r.satisfied]
            if not ranked:
                typer.echo("No registry entries matched (requires manifest_url entries).")
                typer.echo("Tip: use --manifest-url http://host/mrp/manifest for local testing.")
                return 1
            if not satisfying:
                typer.echo("No registry entries satisfied required capability/policy.")
                for r in ranked[:5]:
                    missing = ", ".join(r.missing) if r.missing else "none"
                    typer.echo(f"- score={r.score:.2f} id={r.entry.id} missing: {missing}")
                return 1

            # Pick top
            entry = satisfying[0].entry
            receiver_id = entry.id
            typer.echo(f"Selected entry: {entry.id} ({entry.name})")
            typer.echo("Fetching manifest...")
            manifest = await fetch_manifest(entry.manifest_url)
            manifest = normalize_manifest_endpoints(manifest, entry.manifest_url)

        endpoints = manifest.get("endpoints") or {}
        discover_url = endpoints.get("discover")
        execute_url = endpoints.get("execute")
        if not discover_url or not execute_url:
            typer.echo("Selected manifest is missing endpoints.discover/execute")
            return 1

        # DISCOVER
        typer.echo("Sending DISCOVER...")
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

        discover_env = mk_envelope("DISCOVER", discover_payload, receiver_id=receiver_id)

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
        typer.echo("Sending EXECUTE...")
        job_id = str(uuid.uuid4())
        exec_payload = {
            "route_id": route_id,
            "inputs": [{"type": "url", "value": url}],
            "output_format": "markdown",
            "job": {"id": job_id, "intent": intent},
        }
        exec_env = mk_envelope("EXECUTE", exec_payload, receiver_id=receiver_id)

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=False) as http:
            r = await http.post(execute_url, json=exec_env, headers={"Content-Type": "application/mrp+json"})
            r.raise_for_status()
            out = r.json()

        typer.echo("Received evidence.")

        payload = out.get("payload") or {}
        response_job_id = payload.get("job_id") or job_id
        outputs = payload.get("outputs") or []
        artifact_refs = [o for o in outputs if isinstance(o, dict) and o.get("type") == "artifact"]

        def envelope_meta(env: dict) -> dict:
            return {
                "msg_id": env.get("msg_id"),
                "msg_type": env.get("msg_type"),
                "timestamp": env.get("timestamp"),
                "sender": env.get("sender"),
                "receiver": env.get("receiver"),
                "in_reply_to": env.get("in_reply_to"),
            }

        bundle = {
            "job_id": response_job_id,
            "created_at": utc_now_rfc3339(),
            "transcript": {
                "intent": intent,
                "capability": capability,
                "policy": policy,
                "discover": {
                    "endpoint": discover_url,
                    "request": envelope_meta(discover_env),
                    "response": envelope_meta(offer_env),
                },
                "execute": {
                    "endpoint": execute_url,
                    "request": envelope_meta(exec_env),
                    "response": envelope_meta(out),
                },
            },
            "artifact_refs": artifact_refs,
            "evidence_envelope": out,
        }
        evidence_path = write_evidence_bundle(response_job_id, bundle)
        typer.echo(f"Evidence bundle written: {evidence_path}")

        typer.echo(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    raise typer.Exit(code=asyncio.run(_run()))
