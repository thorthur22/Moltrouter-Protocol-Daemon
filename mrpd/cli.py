from __future__ import annotations

import typer

from mrpd.commands.bridge_mcp import bridge_mcp
from mrpd.commands.bridge_openapi import bridge_openapi
from mrpd.commands.init_provider import init_provider
from mrpd.commands.mrpify_mcp import mrpify_mcp
from mrpd.commands.mrpify_openapi import mrpify_openapi
from mrpd.commands.publish import publish
from mrpd.commands.route import route
from mrpd.commands.run import run
from mrpd.commands.serve import serve
from mrpd.commands.validate import validate

app = typer.Typer(add_completion=False)

bridge_app = typer.Typer(help="Generate MRP provider wrappers (bridges)")
app.add_typer(bridge_app, name="bridge")

mrpify_app = typer.Typer(help="MRP-ify existing systems with a guided flow")
app.add_typer(mrpify_app, name="mrpify")


@app.command()
def version() -> None:
    """Print version."""
    typer.echo("mrpd 0.1.0")


@app.command(name="serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Run the MRP HTTP server."""
    serve(host=host, port=port, reload=reload)


@app.command(name="validate")
def validate_cmd(
    path: str = typer.Option("-", "--path", help="JSON file path or '-' for stdin"),
    fixtures: bool = typer.Option(False, "--fixtures", help="Validate bundled fixtures (valid must pass, invalid must fail)"),
) -> None:
    """Validate an MRP envelope against the bundled JSON Schemas."""
    validate(path, fixtures=fixtures)


@app.command(name="route")
def route_cmd(
    intent: str = typer.Argument(..., help="High-level intent (human text)"),
    capability: str | None = typer.Option(None, "--capability", help="Capability filter"),
    policy: str | None = typer.Option(None, "--policy", help="Policy filter"),
    registry: str | None = typer.Option(None, "--registry", help="Registry base URL (default: https://www.moltrouter.dev)"),
    bootstrap_raw: str | None = typer.Option(None, "--bootstrap-raw", help="Override fallback raw registry JSON (URL or file://path)"),
    limit: int = typer.Option(10, "--limit", min=1, max=50),
) -> None:
    """Query registry + rank candidates for an intent."""
    route(intent=intent, capability=capability, policy=policy, registry=registry, limit=limit, bootstrap_raw=bootstrap_raw)


@app.command(name="run")
def run_cmd(
    intent: str = typer.Argument(..., help="High-level intent (human text)"),
    url: str = typer.Option(..., "--url", help="URL input"),
    capability: str = typer.Option("summarize_url", "--capability", help="Capability to request"),
    policy: str | None = typer.Option(None, "--policy", help="Policy requirement"),
    registry: str | None = typer.Option(None, "--registry", help="Registry base URL (default: https://www.moltrouter.dev)"),
    manifest_url: str | None = typer.Option(None, "--manifest-url", help="Skip registry and use this provider manifest URL (useful for local testing)"),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Soft max context tokens (constraint hint)"),
    max_cost: float | None = typer.Option(None, "--max-cost", help="Max cost (constraint hint)"),
) -> None:
    """End-to-end: DISCOVER -> EXECUTE against the best matching provider."""
    run(intent=intent, url=url, capability=capability, policy=policy, registry=registry, manifest_url=manifest_url, max_tokens=max_tokens, max_cost=max_cost)


@app.command(name="publish")
def publish_cmd(
    manifest_url: str = typer.Option(..., "--manifest-url", help="Provider manifest URL to self-register"),
    registry: str | None = typer.Option(None, "--registry", help="Registry base URL (default: https://www.moltrouter.dev)"),
    poll_seconds: float = typer.Option(5.0, "--poll-seconds", min=1.0, max=60.0),
) -> None:
    """Self-register a provider in the public registry using HTTP-01 challenge."""
    publish(manifest_url=manifest_url, registry=registry, poll_seconds=poll_seconds)


@app.command(name="init-provider")
def init_provider_cmd(
    out_dir: str = typer.Option("./mrp-provider", "--out-dir", help="Output directory"),
    capability: str = typer.Option(..., "--capability", help="Capability name (e.g. summarize_url)"),
    provider_id: str = typer.Option("service:example/provider", "--provider-id", help="Provider sender id"),
    name: str = typer.Option("MRP Provider", "--name"),
    description: str = typer.Option("", "--description"),
    policy: list[str] = typer.Option([], "--policy", help="Policy strings (repeatable)")
) -> None:
    """Scaffold a minimal FastAPI MRP provider wrapper."""
    init_provider(out_dir=out_dir, capability=capability, provider_id=provider_id, name=name, description=description, policy=policy)


@bridge_app.command(name="openapi")
def bridge_openapi_cmd(
    spec: str = typer.Option(..., "--spec", help="Path to OpenAPI spec (json/yaml)"),
    out_dir: str = typer.Option("./mrp-openapi-bridge", "--out-dir", help="Output directory"),
    provider_id: str = typer.Option("service:openapi/bridge", "--provider-id", help="Provider sender id"),
    backend_base_url: str | None = typer.Option(None, "--backend-base-url", help="Override OpenAPI servers[0].url"),
    capability_prefix: str | None = typer.Option(None, "--capability-prefix", help="Prefix for generated capabilities (e.g. svc_)"),
) -> None:
    """Generate an MRP provider wrapper from an OpenAPI spec."""
    bridge_openapi(spec=spec, out_dir=out_dir, provider_id=provider_id, backend_base_url=backend_base_url, capability_prefix=capability_prefix)


@bridge_app.command(name="mcp")
def bridge_mcp_cmd(
    tools_json: str = typer.Option(..., "--tools-json", help="Path to MCP tools list JSON"),
    out_dir: str = typer.Option("./mrp-mcp-bridge", "--out-dir", help="Output directory"),
    provider_id: str = typer.Option("service:mcp/bridge", "--provider-id", help="Provider sender id"),
    mcp_command: str = typer.Option(..., "--mcp-command", help="MCP server command (stdio)"),
    mcp_args: list[str] = typer.Option([], "--mcp-arg", help="MCP server argument (repeatable)"),
) -> None:
    """Generate an MRP provider wrapper scaffold from an MCP tool list."""
    bridge_mcp(tools_json=tools_json, out_dir=out_dir, provider_id=provider_id, mcp_command=mcp_command, mcp_args=mcp_args)


@mrpify_app.command(name="openapi")
def mrpify_openapi_cmd(
    spec: str = typer.Option(..., "--spec", help="Path to OpenAPI spec (json/yaml)"),
    out_dir: str = typer.Option("./mrp-openapi-bridge", "--out-dir", help="Output directory"),
    provider_id: str = typer.Option("service:openapi/bridge", "--provider-id", help="Provider sender id"),
    backend_base_url: str | None = typer.Option(None, "--backend-base-url", help="Override OpenAPI servers[0].url"),
    capability_prefix: str | None = typer.Option(None, "--capability-prefix", help="Prefix for generated capabilities (e.g. svc_)"),
    public_base_url: str | None = typer.Option(None, "--public-base-url", help="Deployed public base URL, e.g. https://api.example.com"),
    publish_now: bool = typer.Option(False, "--publish", help="Run mrpd publish for each generated manifest URL (requires public HTTPS)"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompts"),
    registry: str | None = typer.Option(None, "--registry", help="Registry base URL (default: https://www.moltrouter.dev)"),
    poll_seconds: float = typer.Option(5.0, "--poll-seconds", min=1.0, max=60.0),
) -> None:
    """Guided flow: OpenAPI -> MRP bridge -> (optional) publish commands."""
    mrpify_openapi(
        spec=spec,
        out_dir=out_dir,
        provider_id=provider_id,
        backend_base_url=backend_base_url,
        capability_prefix=capability_prefix,
        public_base_url=public_base_url,
        do_publish=publish_now,
        yes=yes,
        registry=registry,
        poll_seconds=poll_seconds,
    )


@mrpify_app.command(name="mcp")
def mrpify_mcp_cmd(
    tools_json: str = typer.Option(..., "--tools-json", help="Path to MCP tools list JSON"),
    out_dir: str = typer.Option("./mrp-mcp-bridge", "--out-dir", help="Output directory"),
    provider_id: str = typer.Option("service:mcp/bridge", "--provider-id", help="Provider sender id"),
    mcp_command: str = typer.Option(..., "--mcp-command", help="MCP server command (stdio)"),
    mcp_args: list[str] = typer.Option([], "--mcp-arg", help="MCP server argument (repeatable)"),
    public_base_url: str | None = typer.Option(None, "--public-base-url", help="Deployed public base URL, e.g. https://api.example.com"),
    publish_now: bool = typer.Option(False, "--publish", help="Run mrpd publish for each generated manifest URL (requires public HTTPS)"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompts"),
    registry: str | None = typer.Option(None, "--registry", help="Registry base URL (default: https://www.moltrouter.dev)"),
    poll_seconds: float = typer.Option(5.0, "--poll-seconds", min=1.0, max=60.0),
) -> None:
    """Guided flow: MCP -> MRP bridge -> (optional) publish commands."""
    mrpify_mcp(
        tools_json=tools_json,
        out_dir=out_dir,
        provider_id=provider_id,
        mcp_command=mcp_command,
        mcp_args=mcp_args,
        public_base_url=public_base_url,
        do_publish=publish_now,
        yes=yes,
        registry=registry,
        poll_seconds=poll_seconds,
    )


if __name__ == "__main__":
    app()
