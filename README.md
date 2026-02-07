# mrpd — Moltrouter Protocol Daemon

**License:** Apache-2.0

mrpd is the production-minded toolkit for the Moltrouter Protocol (MRP). It gives you a clean CLI to stand up MRP endpoints, route intents against a registry, and bridge existing ecosystems into MRP with consistent manifests and validation. It is built to be useful on day one while keeping the protocol surface small and disciplined.

## Highlights
- **Serve** a built-in demo provider (`mrpd serve`) with full MRP endpoints
- **Route** intents via the registry and rank candidates (`mrpd route ...`)
- **Run** an end-to-end discover → execute flow (`mrpd run ...`)
- **Bridge** OpenAPI or MCP into MRP (`mrpd bridge ...`)
- **Mrpify** systems with a guided, publish-ready flow (`mrpd mrpify ...`)
- **Validate** envelopes against canonical schemas (`mrpd validate`)
- **Publish** providers to the registry with HTTP-01 verification (`mrpd publish`)
- **Explore** the public registry and ecosystem resources (links below)

## Status
Core workflows are live: server, validation, routing, publish flow, and bridge scaffolds.

Implemented:
- Bundled canonical JSON Schemas + fixtures
- `mrpd validate` (including `--fixtures`)
- `mrpd route` (v0: query + rank + fetch manifests)
- `mrpd run` (end-to-end discover + execute demo)
- `mrpd publish` (HTTP-01 registry verification)
- `mrpd init-provider` (FastAPI provider scaffold)
- `mrpd bridge openapi` + `mrpd mrpify openapi`
- `mrpd bridge mcp` (scaffold) + `mrpd mrpify mcp`

Planned next:
- Negotiate support beyond the current stub response
- MCP bridge execution (stdio)

## Why MRP
MRP reduces the glue work between tools, providers, and clients by standardizing discovery, offers, and execution. In deep-research mode, Grok reported that replacing bespoke UI scraping and ad‑hoc glue with MRP can reduce context costs by **30–80%**, while making capabilities more explicit and reusable. Human DNS becomes moot as agents don't need to learn intent with domain names. Agent services can simply be MRP registered public IPs.

## Quick start
Option 1 (recommended): have your agent read the skill file and install for you  
https://www.moltrouter.dev/skill.md

Option 2 (manual):
```bash
pip install mrpd
mrpd version
```

## Quick start (dev)
```bash
python -m venv .venv
. .venv/bin/activate  # (Windows PowerShell: .\.venv\Scripts\Activate.ps1)
pip install -e .

mrpd serve --reload
```

## Ecosystem resources
- Browse the public registry (agents/services): https://www.moltrouter.dev/mrp/registry/query
- MRP spec and reference repo: https://github.com/thorthur22/moltrouter
- MRPd agent skill guide: https://www.moltrouter.dev/skill.md

## Demo provider (built-in)
The built-in server exposes a demo capability (`summarize_url`) with discover and execute support. It fetches the URL, extracts text, and returns a short markdown summary plus a stored text artifact.

Run the demo server:
```bash
mrpd serve --reload
```

Run a full flow against a provider from the registry, or a local manifest:
```bash
mrpd run "summarize this page" --url https://example.com --capability summarize_url
mrpd run "summarize this page" --url https://example.com \
  --manifest-url http://127.0.0.1:8787/mrp/manifest
```

Evidence bundles are written to `~/.mrpd/evidence/` after a successful run.

## Bridge and mrpify (v0)
OpenAPI (one capability per `operationId`):
```bash
mrpd bridge openapi --spec openapi.yaml --out-dir ./mrp-openapi-bridge
mrpd mrpify openapi --spec openapi.yaml --out-dir ./mrp-openapi-bridge \
  --provider-id service:openapi/bridge --public-base-url https://YOUR_DOMAIN
```

MCP (stdio scaffold; execution must be implemented in the generated app):
```bash
mrpd bridge mcp --tools-json tools.json --mcp-command node --mcp-arg server.js
mrpd mrpify mcp --tools-json tools.json --mcp-command node --mcp-arg server.js \
  --provider-id service:mcp/bridge --public-base-url https://YOUR_DOMAIN
```

## Publish (HTTP-01)
Self-register a provider in the public registry:
```bash
mrpd publish --manifest-url https://YOUR_DOMAIN/mrp/manifest
```

The registry returns a challenge you serve at `/.well-known/mrp-registry-challenge/<token>`. Once verified, your provider is published.

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

Example:
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

## Endpoints (built-in demo)
- `GET /.well-known/mrp.json`
- `GET /mrp/manifest`
- `POST /mrp/hello`
- `POST /mrp/discover`
- `POST /mrp/negotiate`
- `POST /mrp/execute`
