# mrpd — Moltrouter Protocol Daemon

**License:** Apache-2.0

One installable package that can:
- **serve** MRP endpoints for local tools (`mrpd serve`)
- **route** intents as a client (`mrpd route ...`) (v0: registry query + ranking)
- **bridge** other tool ecosystems (OpenAPI/MCP) into MRP (`mrpd bridge ...`)
- **mrpify** existing systems with a guided flow (`mrpd mrpify ...`)
- **validate** MRP envelopes against schemas/fixtures (`mrpd validate`) (working)

## Status
Minimal server + validation are working.

Implemented:
- Bundled canonical JSON Schemas + fixtures
- `mrpd validate` (including `--fixtures`)
- `mrpd route` (v0: query + rank + fetch manifests)
- `mrpd bridge openapi` + `mrpd mrpify openapi`
- `mrpd bridge mcp` (scaffold) + `mrpd mrpify mcp`

Planned next:
- negotiate/execute
- MCP bridge execute (stdio)

## Dev
```bash
python -m venv .venv
. .venv/bin/activate  # (Windows PowerShell: .\.venv\Scripts\Activate.ps1)
pip install -e .

mrpd serve --reload
```

## Bridge / Mrpify (v0)
OpenAPI:
```bash
mrpd bridge openapi --spec openapi.yaml --out-dir ./mrp-openapi-bridge
mrpd mrpify openapi --spec openapi.yaml --out-dir ./mrp-openapi-bridge \
  --provider-id service:openapi/bridge --public-base-url https://YOUR_DOMAIN
```

MCP (stdio scaffold):
```bash
mrpd bridge mcp --tools-json tools.json --mcp-command node --mcp-arg server.js
mrpd mrpify mcp --tools-json tools.json --mcp-command node --mcp-arg server.js \
  --provider-id service:mcp/bridge --public-base-url https://YOUR_DOMAIN
```

## Validate
Run the bundled conformance fixtures:
```bash
mrpd validate --fixtures
```

Validate a single envelope JSON file:
```bash
mrpd validate --path path/to/envelope.json
```

## Route (v0)
`mrpd route` queries a registry and prints ranked candidates. **Registry entries must include `manifest_url`.**

Defaults:
- Registry base URL: `https://www.moltrouter.dev`
- No raw bootstrap fallback is used unless explicitly configured (see below).

Examples:
```bash
mrpd route "inspect router capability" --capability router --policy no_pii --limit 5
```

Optional bootstrap (mostly for offline/dev):

- Env var: `MRP_BOOTSTRAP_REGISTRY_RAW` (supports `file://...`)
- Or CLI: `mrpd route ... --bootstrap-raw file:///C:/path/to/registry.json`

Example:
```bash
mrpd route "inspect router capability" --capability router --policy no_pii \
  --bootstrap-raw "file:///C:/path/to/registry.json"
```

## Endpoints (initial)
- `GET /.well-known/mrp.json`
- `GET /mrp/manifest`
- `POST /mrp/hello`
- `POST /mrp/discover`
- `POST /mrp/negotiate`
- `POST /mrp/execute`
