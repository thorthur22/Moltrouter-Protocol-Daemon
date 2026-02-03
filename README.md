# mrpd — Moltrouter Protocol Daemon

One installable package that can:
- **serve** MRP endpoints for local tools (`mrpd serve`)
- **route** intents as a client (`mrpd route ...`) (WIP)
- **bridge** other tool ecosystems (MCP/REST) into MRP (`mrpd bridge ...`) (WIP)
- **validate** MRP envelopes against schemas/fixtures (`mrpd validate`) (WIP)

## Status
Minimal server + validation are working.

Implemented:
- Bundled canonical JSON Schemas + fixtures
- `mrpd validate` (including `--fixtures`)
- Basic registry discovery (`mrpd route`) (v0: query + rank + fetch manifests)

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

## Endpoints (initial)
- `GET /.well-known/mrp.json`
- `GET /mrp/manifest`
- `POST /mrp/hello`
- `POST /mrp/discover`
- `POST /mrp/negotiate`
- `POST /mrp/execute`
