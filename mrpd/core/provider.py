from __future__ import annotations

from typing import Any

import httpx

from mrpd.core.artifacts import store_bytes
from mrpd.core.util import approx_tokens, strip_html, utc_now_rfc3339


SERVICE_ID = "service:mrpd"


def provider_manifest(base_url: str) -> dict[str, Any]:
    # base_url should be full origin, e.g. http://127.0.0.1:8787
    return {
        "capability_id": "capability:mrp/summarize_url",
        "capability": "summarize_url",
        "version": "0.1",
        "tags": ["mrp", "summarize", "web"],
        "inputs": [{"type": "url"}],
        "outputs": [{"type": "markdown"}, {"type": "artifact"}],
        "constraints": {"policy": ["no_pii"]},
        "cost": {"unit": "usd", "estimate": 0.0},
        "latency": {"p50": "200ms"},
        "proofs_required": [],
        "endpoints": {
            "discover": f"{base_url}/mrp/discover",
            "negotiate": f"{base_url}/mrp/negotiate",
            "execute": f"{base_url}/mrp/execute",
        },
    }


def offers_for_discover(_discover_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": "route:mrpd/summarize_url@0.1",
            "capability": "summarize_url",
            "confidence": 0.9,
            "cost": {"unit": "usd", "estimate": 0.0},
            "latency": {"p50": "200ms"},
            "proofs": [],
            "policy": ["no_pii"],
            "risk": {"data_retention_days": 0, "training_use": "none", "subprocessors": []},
            "endpoint": "/mrp/execute",
        }
    ]


async def execute_summarize_url(inputs: list[dict[str, Any]]) -> dict[str, Any]:
    url = None
    for item in inputs:
        if item.get("type") == "url":
            url = item.get("value")
            break
    if not url:
        raise ValueError("missing url input")

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "mrpd/0.1"})
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        raw_bytes = r.content

    text = ""
    if "text/html" in ct:
        text = strip_html(raw_bytes.decode("utf-8", "replace"))
    else:
        # best effort
        text = raw_bytes.decode("utf-8", "replace")

    # store artifact of extracted text
    artifact = store_bytes(text.encode("utf-8"), mime="text/plain", suffix=".txt")

    # crude summary: first ~1200 chars
    summary = text[:1200]
    if len(text) > 1200:
        summary += "\n\n…"

    tokens_in = approx_tokens(text)
    tokens_out = approx_tokens(summary)

    return {
        "outputs": [
            {"type": "markdown", "value": f"## Summary\n\n{summary}\n"},
            artifact,
        ],
        "provenance": {
            "citations": [url],
            "timestamp": utc_now_rfc3339(),
            "source_hashes": [artifact["hash"]],
        },
        "usage": {
            "tokens_in_est": tokens_in,
            "tokens_out_est": tokens_out,
            "bytes_in": len(raw_bytes),
            "bytes_text": len(text.encode("utf-8")),
        },
    }
