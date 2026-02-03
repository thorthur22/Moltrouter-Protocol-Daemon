from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml


def _load_spec(path_or_url: str) -> dict:
    # v0: local file only (URL support later)
    p = Path(path_or_url)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(raw)
    return json.loads(raw)


def bridge_openapi(
    spec: str,
    out_dir: str,
    provider_id: str,
    backend_base_url: str | None,
) -> None:
    """Generate an MRP provider wrapper from an OpenAPI spec.

    v0 behavior:
    - one MRP capability per OpenAPI operationId
    - generates per-operation manifests served at /mrp/manifest/<operationId>
    - execute expects a json input containing optional {path_params, query, body, headers}
    """

    spec_obj = _load_spec(spec)
    paths = spec_obj.get("paths") or {}

    servers = spec_obj.get("servers") or []
    default_server = servers[0].get("url") if servers and isinstance(servers[0], dict) else None
    base_url = (backend_base_url or default_server or "").rstrip("/")

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "mrp_manifests").mkdir(exist_ok=True)

    operations: list[dict] = []

    for pth, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if not op_id or not isinstance(op_id, str):
                continue

            route_id = f"route:openapi/{op_id}@0.1"

            manifest = {
                "capability_id": f"capability:openapi/{op_id}",
                "capability": op_id,
                "version": "0.1",
                "tags": ["mrp", "openapi"],
                "inputs": [{"type": "json"}],
                "outputs": [{"type": "json"}],
                "constraints": {"policy": []},
                "proofs_required": [],
                "endpoints": {
                    "discover": "/mrp/discover",
                    "execute": "/mrp/execute",
                },
                "metadata": {
                    "openapi": {
                        "method": method.upper(),
                        "path": pth,
                        "operationId": op_id,
                        "base_url": base_url,
                        "route_id": route_id,
                    }
                },
            }

            (out / "mrp_manifests" / f"{op_id}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            operations.append({"operationId": op_id, "method": method.upper(), "path": pth, "route_id": route_id})

    if not operations:
        raise typer.Exit(code=2)

    # Wrapper server
    app_py = '''from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI

APP_DIR = Path(__file__).resolve().parent
MANIFEST_DIR = APP_DIR / "mrp_manifests"

# Configure backend base URL here (or via env in a real deployment)
BACKEND_BASE_URL = ("''' + base_url + '''").rstrip("/")

app = FastAPI(title="MRP OpenAPI Bridge")


def _load_manifest(op_id: str) -> dict:
    fp = MANIFEST_DIR / f"{op_id}.json"
    return json.loads(fp.read_text(encoding="utf-8"))


def _operation_from_route_id(route_id: str) -> str:
    # route:openapi/<operationId>@0.1
    if not route_id.startswith("route:openapi/"):
        raise ValueError("invalid route_id")
    rest = route_id[len("route:openapi/"):]
    op_id = rest.split("@", 1)[0]
    return op_id


@app.get("/.well-known/mrp.json")
def well_known() -> dict:
    # NOTE: This lists multiple capabilities; manifests are per-capability.
    caps = []
    for fp in sorted(MANIFEST_DIR.glob("*.json")):
        try:
            m = json.loads(fp.read_text(encoding="utf-8"))
            c = m.get("capability")
            if isinstance(c, str):
                caps.append(c)
        except Exception:
            continue

    return {
        "mrp_version": "0.1",
        "id": "''' + provider_id + '''",
        "name": "MRP OpenAPI Bridge",
        "manifest_url": "/mrp/manifest/" + (caps[0] if caps else ""),
        "capabilities": caps,
    }


@app.get("/mrp/manifest/{capability}")
def mrp_manifest(capability: str) -> dict:
    return _load_manifest(capability)


@app.post("/mrp/discover")
def mrp_discover(envelope: dict) -> dict:
    req_id = envelope.get("msg_id")
    sender = (envelope.get("sender") or {}).get("id")
    constraints = (envelope.get("payload") or {}).get("constraints") or {}

    wanted = constraints.get("capability")

    offers = []
    for fp in sorted(MANIFEST_DIR.glob("*.json")):
        m = json.loads(fp.read_text(encoding="utf-8"))
        cap = m.get("capability")
        meta = (m.get("metadata") or {}).get("openapi") or {}
        route_id = meta.get("route_id")
        if wanted and cap != wanted:
            continue
        offers.append({
            "route_id": route_id,
            "capability": cap,
            "constraints": m.get("constraints") or {},
            "cost": {"unit": "usd", "estimate": 0},
            "latency_ms": 0,
            "proofs": [],
        })

    return {
        "mrp_version": "0.1",
        "msg_id": str(__import__("uuid").uuid4()),
        "msg_type": "OFFER",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "sender": {"id": "''' + provider_id + '''"},
        "receiver": {"id": sender} if sender else None,
        "in_reply_to": req_id,
        "payload": {"offers": offers[:25]},
    }


@app.post("/mrp/execute")
def mrp_execute(envelope: dict) -> dict:
    req_id = envelope.get("msg_id")
    sender = (envelope.get("sender") or {}).get("id")

    payload = envelope.get("payload") or {}
    route_id = payload.get("route_id")
    op_id = _operation_from_route_id(route_id)

    m = _load_manifest(op_id)
    meta = (m.get("metadata") or {}).get("openapi") or {}

    method = meta.get("method")
    pth = meta.get("path")

    if not BACKEND_BASE_URL:
        raise RuntimeError("BACKEND_BASE_URL is not configured")

    # Convention: json input value may include {path_params, query, body, headers}
    inputs = payload.get("inputs") or []
    inp = next((i for i in inputs if isinstance(i, dict) and i.get("type") == "json"), None)
    spec = inp.get("value") if isinstance(inp, dict) else None
    spec = spec if isinstance(spec, dict) else {}

    path_params = spec.get("path_params") or {}
    query = spec.get("query") or {}
    body = spec.get("body")
    headers = spec.get("headers") or {}

    url_path = pth
    for k, v in path_params.items():
        url_path = url_path.replace("{" + str(k) + "}", str(v))

    url = BACKEND_BASE_URL + url_path
    if query:
        url = url + "?" + urlencode(query, doseq=True)

    with httpx.Client(timeout=60.0, follow_redirects=False) as client:
        r = client.request(method, url, json=body, headers=headers)
        data = None
        try:
            data = r.json()
        except Exception:
            data = {"status_code": r.status_code, "text": r.text}

    return {
        "mrp_version": "0.1",
        "msg_id": str(__import__("uuid").uuid4()),
        "msg_type": "EVIDENCE",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "sender": {"id": "''' + provider_id + '''"},
        "receiver": {"id": sender} if sender else None,
        "in_reply_to": req_id,
        "payload": {
            "route_id": route_id,
            "outputs": [{"type": "json", "value": data}],
            "provenance": {"citations": [url], "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"},
            "usage": {"tokens_in_est": 0, "tokens_out_est": 0},
            "job_id": (payload.get("job") or {}).get("id"),
        },
    }
'''

    (out / "app.py").write_text(app_py, encoding="utf-8")

    (out / "README.md").write_text(
        "# MRP OpenAPI Bridge\n\n"
        "Generated by `mrpd bridge openapi`.\n\n"
        "## Run locally\n\n"
        "```bash\n"
        "python -m venv .venv\n"
        "pip install fastapi uvicorn httpx pyyaml\n"
        "uvicorn app:app --host 127.0.0.1 --port 8787 --reload\n"
        "```\n\n"
        "## Publish\n\n"
        "Each OpenAPI operationId becomes a capability. After deploying, publish each manifest you want discoverable:\n\n"
        "Example:\n\n"
        "```bash\n"
        "mrpd publish --manifest-url https://YOUR_DOMAIN/mrp/manifest/<operationId>\n"
        "```\n",
        encoding="utf-8",
    )

    typer.echo(f"Generated OpenAPI bridge in: {out}")
    typer.echo(f"Operations: {len(operations)}")
    if base_url:
        typer.echo(f"Backend base URL: {base_url}")
    else:
        typer.echo("Backend base URL: (unset) - edit app.py BACKEND_BASE_URL")
