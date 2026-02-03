from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def evidence_dir() -> Path:
    return Path.home() / ".mrpd" / "evidence"


def write_evidence_bundle(job_id: str, bundle: dict[str, Any]) -> Path:
    directory = evidence_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{job_id}.json"
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return path
