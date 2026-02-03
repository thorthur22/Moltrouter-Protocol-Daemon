from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mrpd.core.util import sha256_hex


def default_artifact_dir() -> Path:
    root = os.getenv("MRPD_ARTIFACT_DIR")
    if root:
        return Path(root)
    # default under user home
    return Path.home() / ".mrpd" / "artifacts"


def store_bytes(data: bytes, *, mime: str, suffix: str = "") -> dict[str, Any]:
    d = default_artifact_dir()
    d.mkdir(parents=True, exist_ok=True)

    h = sha256_hex(data)
    name = h + (suffix if suffix else "")
    path = d / name
    path.write_bytes(data)

    return {
        "type": "artifact",
        "uri": f"file://{path.as_posix()}",
        "hash": f"sha256:{h}",
        "size": len(data),
        "mime": mime,
    }


def store_json(obj: Any, *, suffix: str = ".json") -> dict[str, Any]:
    data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    return store_bytes(data, mime="application/json", suffix=suffix)
