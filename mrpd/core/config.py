from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class RegistrySource(BaseModel):
    name: str
    base_url: str


class Config(BaseModel):
    registries: list[RegistrySource] = Field(default_factory=list)
    cache_dir: str | None = None
    # TODO: adapters, local tools, auth keys


def load_config(path: str | Path) -> Config:
    p = Path(path)
    data: Any = {}
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return Config.model_validate(data)
