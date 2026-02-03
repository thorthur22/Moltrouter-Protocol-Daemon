from __future__ import annotations

import uvicorn


def serve(host: str, port: int, reload: bool) -> None:
    uvicorn.run(
        "mrpd.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
