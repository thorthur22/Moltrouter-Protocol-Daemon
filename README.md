# mrpd — Moltrouter Protocol Daemon

One installable package that can:
- **serve** MRP endpoints for local tools (`mrpd serve`)
- **route** intents as a client (`mrpd route ...`) (v0: registry query + ranking)
- **bridge** other tool ecosystems (MCP/REST) into MRP (`mrpd bridge ...`) (planned)
- **validate** MRP envelopes against schemas/fixtures (`mrpd validate`) (working)

## Status
Minimal server + validation are working.

Implemented:
- Bundled canonical JSON Schemas + fixtures
- `mrpd validate` (including `--fixtures`)
- `mrpd route` (v0: query + rank + fetch manifests)

Planned next:
- negotiate/execute
- MCP bridge adapter

## Dev
```bash
python -m venv .venv
. .venv/bin/activate  # (Windows PowerShell: .\.venv\Scripts\Activate.ps1)
pip install -e .

mrpd serve --reload
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
