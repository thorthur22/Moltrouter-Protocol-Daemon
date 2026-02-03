from __future__ import annotations

import json
from typing import Optional

import httpx

import os

from mrpd.core.defaults import MRP_BOOTSTRAP_REGISTRY_RAW, MRP_DEFAULT_REGISTRY_BASE
from mrpd.core.models import RegistryEntry, RegistryQueryResponse


class RegistryClient:
    def __init__(self, base_url: str = MRP_DEFAULT_REGISTRY_BASE, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def query(
        self,
        *,
        capability: Optional[str] = None,
        policy: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> RegistryQueryResponse:
        """Query the MRP registry API. Falls back to raw GitHub JSON if API is unavailable."""

        url = f"{self.base_url}/mrp/registry/query"
        params = {"limit": str(limit)}
        if capability:
            params["capability"] = capability
        if policy:
            params["policy"] = policy
        if cursor:
            params["cursor"] = cursor

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                r = await client.get(url, params=params, headers={"Accept": "application/json"})
                r.raise_for_status()
                return RegistryQueryResponse.model_validate(r.json())
        except Exception:
            # Fallback: raw JSON list (bootstrap)
            entries = await self._fetch_raw_entries()
            if capability:
                entries = [e for e in entries if capability in e.capabilities]
            if policy:
                entries = [e for e in entries if policy in e.policies]
            return RegistryQueryResponse(results=entries)

    async def _fetch_raw_entries(self) -> list[RegistryEntry]:
        raw_url = os.getenv("MRP_BOOTSTRAP_REGISTRY_RAW", MRP_BOOTSTRAP_REGISTRY_RAW)

        if raw_url.startswith("file://"):
            path = raw_url[len("file://") :]
            # Windows file URLs sometimes come through as /C:/...
            if len(path) >= 3 and path[0] == "/" and path[2] == ":":
                path = path[1:]
            payload = json.loads(open(path, "r", encoding="utf-8").read())
        else:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                r = await client.get(raw_url, headers={"Accept": "application/json"})
                r.raise_for_status()
                payload = r.json()

        if not isinstance(payload, list):
            raise ValueError("bootstrap registry did not return a list")

        entries: list[RegistryEntry] = []
        for item in payload:
            # Require manifest_url (per user direction)
            if not isinstance(item, dict) or not item.get("manifest_url"):
                continue
            entries.append(RegistryEntry.model_validate(item))

        # de-dupe by id
        dedup: dict[str, RegistryEntry] = {}
        for e in entries:
            if e.id not in dedup:
                dedup[e.id] = e
        return list(dedup.values())


async def fetch_manifest(manifest_url: str, timeout: float = 10.0) -> dict:
    # Local development helpers
    if manifest_url.startswith("file://"):
        path = manifest_url[len("file://") :]
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return json.loads(open(path, "r", encoding="utf-8").read())

    # If the registry points at raw GitHub content for thorthur22/moltrouter,
    # try to resolve to a local checkout during development.
    prefix = "https://raw.githubusercontent.com/thorthur22/moltrouter/main/"
    if manifest_url.startswith(prefix):
        import os
        from pathlib import Path

        local_root = Path(os.getenv("MRP_DEV_MOLTROUTER_DIR", r"C:\Users\thort\Documents\moltrouter"))
        rel = manifest_url[len(prefix) :].replace("/", os.sep)
        candidate = local_root / rel
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        r = await client.get(manifest_url, headers={"Accept": "application/mrp-manifest+json, application/json"})
        r.raise_for_status()
        return r.json()
