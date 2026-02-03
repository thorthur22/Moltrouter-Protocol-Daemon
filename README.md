# mrpd — Moltrouter Protocol Daemon

One installable package that can:
- **serve** MRP endpoints for local tools (`mrpd serve`)
- **route** intents as a client (`mrpd route ...`) (WIP)
- **bridge** other tool ecosystems (MCP/REST) into MRP (`mrpd bridge ...`) (WIP)
- **validate** MRP envelopes against schemas/fixtures (`mrpd validate`) (WIP)

## Status
Scaffold + minimal HTTP server endpoints are in place. Next step is to wire in the canonical schemas/fixtures from `moltrouter` and implement:
- schema validation
- registry query + offer scoring
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
