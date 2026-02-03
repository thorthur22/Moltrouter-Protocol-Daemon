from __future__ import annotations

from fastapi import FastAPI

from mrpd.api.routes import router

app = FastAPI(title="mrpd (Moltrouter Protocol Daemon)")
app.include_router(router)
