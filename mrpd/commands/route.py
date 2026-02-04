from __future__ import annotations

import asyncio

import typer

from mrpd.core.registry import RegistryClient, fetch_manifest
from mrpd.core.scoring import ScoreResult, rank_entries


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

    def loss_reason(winner: ScoreResult, candidate: ScoreResult) -> str:
        if candidate.missing:
            return f"missing requirements: {', '.join(candidate.missing)}"
        if candidate.score != winner.score:
            return f"lower score ({candidate.score:.2f} vs {winner.score:.2f})"
        if candidate.required_matches != winner.required_matches:
            return "fewer required matches"
        if candidate.trust_score != winner.trust_score:
            return "lower trust score"
        if candidate.proofs_count != winner.proofs_count:
            return "fewer proofs"
        if (candidate.entry.name or "").lower() != (winner.entry.name or "").lower():
            return "tiebreaker: name order"
        return "tiebreaker: id order"

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

        entries = list(res.results)
        if not entries and (capability or policy):
            try:
                res = await client.query(limit=limit)
                entries = list(res.results)
            except Exception as ex:
                typer.echo(f"Registry query failed: {ex}")
                return 1

        if not entries:
            typer.echo("No registry entries matched.")
            return 1

        # Registry may return mixed results. Only entries with manifest_url are routable.
        leads = [e for e in entries if not getattr(e, "manifest_url", None)]
        entries = [e for e in entries if getattr(e, "manifest_url", None)]

        if not entries:
            typer.echo("No routable providers found (no entries with manifest_url).")
            if leads:
                typer.echo(f"Indexed leads found: {len(leads)} (not MRP providers yet).")
            return 1

        ranked = rank_entries(entries, capability=capability, policy=policy)
        satisfying = [r for r in ranked if r.satisfied]

        typer.echo(f"Intent: {intent}")
        if capability:
            typer.echo(f"Filter capability: {capability}")
        if policy:
            typer.echo(f"Filter policy: {policy}")
        typer.echo("")

        if satisfying:
            winner = satisfying[0]
            typer.echo(
                f"Winner: score={winner.score:.2f} id={winner.entry.id} name={winner.entry.name}"
            )
            winner_reason = ", ".join(winner.reasons) if winner.reasons else "best tiebreaker"
            typer.echo(f"Why winner won: {winner_reason}")
            typer.echo(f"Manifest: {winner.entry.manifest_url}")
            if winner.entry.repo:
                typer.echo(f"Repo: {winner.entry.repo}")
            try:
                manifest = await fetch_manifest(winner.entry.manifest_url)
                caps = manifest.get("capability") or manifest.get("capability_id")
                typer.echo(f"Manifest capability: {caps}")
                endpoints = manifest.get("endpoints") or {}
                if endpoints:
                    typer.echo(f"Endpoints: {endpoints}")
            except Exception as ex:
                typer.echo(f"Manifest fetch FAILED: {ex}")
            typer.echo("")

            for r in satisfying[1:limit]:
                typer.echo(f"- score={r.score:.2f} id={r.entry.id} name={r.entry.name}")
                typer.echo(f"  why lost: {loss_reason(winner, r)}")
                typer.echo(f"  manifest: {r.entry.manifest_url}")
                if r.entry.repo:
                    typer.echo(f"  repo: {r.entry.repo}")
                try:
                    manifest = await fetch_manifest(r.entry.manifest_url)
                    caps = manifest.get("capability") or manifest.get("capability_id")
                    typer.echo(f"  manifest.capability: {caps}")
                    endpoints = manifest.get("endpoints") or {}
                    if endpoints:
                        typer.echo(f"  endpoints: {endpoints}")
                except Exception as ex:
                    typer.echo(f"  manifest fetch FAILED: {ex}")
                typer.echo("")
        else:
            typer.echo("No candidates satisfied the requested requirements. Near-miss list:")
            typer.echo("")
            for r in ranked[:limit]:
                missing = ", ".join(r.missing) if r.missing else "none"
                typer.echo(f"- score={r.score:.2f} id={r.entry.id} name={r.entry.name}")
                typer.echo(f"  missing: {missing}")
                typer.echo(f"  manifest: {r.entry.manifest_url}")
                if r.entry.repo:
                    typer.echo(f"  repo: {r.entry.repo}")
                typer.echo("")

        if leads:
            typer.echo("Indexed leads (not MRP providers yet):")
            for e in leads[: min(limit, 20)]:
                url = e.metadata.get("url") if isinstance(e.metadata, dict) else None
                trust = getattr(e, "trust", None)
                level = trust.level if trust and getattr(trust, "level", None) else None
                typer.echo(f"- id={e.id} name={e.name} canonical_id={getattr(e,'canonical_id',None)}")
                if level:
                    typer.echo(f"  trust.level: {level}")
                if url:
                    typer.echo(f"  url: {url}")
            typer.echo("")

        return 0

    raise typer.Exit(code=asyncio.run(_run()))
