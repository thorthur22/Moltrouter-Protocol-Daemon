from __future__ import annotations

import json
from pathlib import Path

import typer


def bridge_mcp(
    tools_json: str,
    out_dir: str,
    provider_id: str,
    mcp_command: str,
    mcp_args: list[str],
) -> None:
    """Generate an MRP provider wrapper from an MCP tool list.

    v0 behavior:
    - one MRP capability per MCP tool name
    - generates per-tool manifests served at /mrp/manifest/<tool>

    NOTE: This is a scaffold only. You must implement the actual MCP execution
    (stdio) inside the generated app.
    """

    tools = json.loads(Path(tools_json).read_text(encoding="utf-8"))
    if not isinstance(tools, list) or not tools:
        raise typer.Exit(code=2)

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "mrp_manifests").mkdir(exist_ok=True)

    for t in tools:
        name = t.get("name") if isinstance(t, dict) else None
        if not name or not isinstance(name, str):
            continue
        route_id = f"route:mcp/{name}@0.1"
        manifest = {
            "capability_id": f"capability:mcp/{name}",
            "capability": name,
            "version": "0.1",
            "tags": ["mrp", "mcp"],
            "inputs": [{"type": "json"}],
            "outputs": [{"type": "json"}],
            "constraints": {"policy": []},
            "proofs_required": [],
            "endpoints": {"discover": "/mrp/discover", "execute": "/mrp/execute"},
            "metadata": {
                "mcp": {
                    "tool": name,
                    "route_id": route_id,
                    "stdio": {"command": mcp_command, "args": mcp_args},
                }
            },
        }
        (out / "mrp_manifests" / f"{name}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    app_py = '''from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

APP_DIR = Path(__file__).resolve().parent
MANIFEST_DIR = APP_DIR / "mrp_manifests"
MCP_COMMAND = ''' + json.dumps(mcp_command) + '''
MCP_ARGS = ''' + json.dumps(mcp_args) + '''

app = FastAPI(title="MRP MCP Bridge")


def _load_manifest(name: str) -> dict:
    fp = MANIFEST_DIR / f"{name}.json"
    return json.loads(fp.read_text(encoding="utf-8"))


def _tool_from_route_id(route_id: str) -> str:
    # route:mcp/<tool>@0.1
    if not route_id.startswith("route:mcp/"):
        raise ValueError("invalid route_id")
    rest = route_id[len("route:mcp/"):]
    tool = rest.split("@", 1)[0]
    return tool


@app.get("/.well-known/mrp.json")
def well_known() -> dict:
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
        "name": "MRP MCP Bridge",
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
        meta = (m.get("metadata") or {}).get("mcp") or {}
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
    # TODO: implement MCP execution using MCP_COMMAND + MCP_ARGS (stdio).
    req_id = envelope.get("msg_id")
    sender = (envelope.get("sender") or {}).get("id")

    payload = envelope.get("payload") or {}
    tool = _tool_from_route_id(payload.get("route_id"))

    return {
        "mrp_version": "0.1",
        "msg_id": str(__import__("uuid").uuid4()),
        "msg_type": "ERROR",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "sender": {"id": "''' + provider_id + '''"},
        "receiver": {"id": sender} if sender else None,
        "in_reply_to": req_id,
        "payload": {
            "code": "MRP_NOT_IMPLEMENTED",
            "message": f"MCP execution not implemented for tool: {tool}",
            "retryable": False,
        },
    }
'''

    (out / "app.py").write_text(app_py, encoding="utf-8")
    (out / "README.md").write_text(
        "# MRP MCP Bridge (scaffold)\n\n"
        "Generated by `mrpd bridge mcp`.\n\n"
        "This is a scaffold: you still need to implement the actual MCP connection\n"
        "(stdio) in `app.py` /mrp/execute.\n\n"
        "## Publish\n\n"
        "After deploying, publish each manifest you want discoverable:\n\n"
        "```bash\n"
        "mrpd publish --manifest-url https://YOUR_DOMAIN/mrp/manifest/<tool>\n"
        "```\n",
        encoding="utf-8",
    )

    typer.echo(f"Generated MCP bridge scaffold in: {out}")
