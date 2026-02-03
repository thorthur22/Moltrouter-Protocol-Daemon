from __future__ import annotations

import json
import os
from typing import Optional
from urllib.parse import urlparse

import httpx

from mrpd.core.defaults import MRP_BOOTSTRAP_REGISTRY_RAW, MRP_DEFAULT_REGISTRY_BASE
from mrpd.core.models import RegistryEntry, RegistryQueryResponse


def normalize_manifest_endpoints(manifest: dict, manifest_url: str) -> dict:
    """Ensure manifest.endpoints contain absolute URLs.

    If endpoints are relative ("/mrp/execute"), prefix with the origin of manifest_url.
    """

    out = dict(manifest)
    endpoints = dict(out.get("endpoints") or {})

    parsed = urlparse(manifest_url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

    for k, v in list(endpoints.items()):
        if isinstance(v, str) and v.startswith("/") and origin:
            endpoints[k] = origin + v

    out["endpoints"] = endpoints
    return out


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
            entries = await self._fetch_raw_entries()
            if capability:
                entries = [e for e in entries if capability in e.capabilities]
            if policy:
                entries = [e for e in entries if policy in e.policies]
            return RegistryQueryResponse(results=entries)

    async def _fetch_raw_entries(self) -> list[RegistryEntry]:
        raw_url = os.getenv("MRP_BOOTSTRAP_REGISTRY_RAW") or MRP_BOOTSTRAP_REGISTRY_RAW
        if not raw_url:
            # No bootstrap configured; callers should rely on the hosted registry API.
            return []

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
            if not isinstance(item, dict) or not item.get("manifest_url"):
                continue
            entries.append(RegistryEntry.model_validate(item))

        dedup: dict[str, RegistryEntry] = {}
        for e in entries:
            if e.id not in dedup:
                dedup[e.id] = e
        return list(dedup.values())


async def fetch_manifest(manifest_url: str, timeout: float = 10.0) -> dict:
    if manifest_url.startswith("file://"):
        path = manifest_url[len("file://") :]
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return json.loads(open(path, "r", encoding="utf-8").read())

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        r = await client.get(manifest_url, headers={"Accept": "application/mrp-manifest+json, application/json"})
        r.raise_for_status()
        return r.json()
