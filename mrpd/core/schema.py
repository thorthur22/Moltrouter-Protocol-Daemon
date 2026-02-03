from __future__ import annotations

import json
from importlib import resources
from typing import Any

import jsonschema


def load_schema_text(rel_path: str) -> str:
    """Load a schema file shipped inside mrpd (package data)."""
    # rel_path like: "schemas/envelope.schema.json"
    return resources.files("mrpd.spec").joinpath(rel_path).read_text(encoding="utf-8")


def load_schema(rel_path: str) -> dict[str, Any]:
    return json.loads(load_schema_text(rel_path))


def validate_envelope(envelope: dict[str, Any]) -> None:
    schema = load_schema("schemas/envelope.schema.json")

    # Resolve local $refs inside the shipped schema folder.
    base = resources.files("mrpd.spec").joinpath("schemas")

    def _load_by_rel(rel: str) -> dict[str, Any]:
        p = rel
        if p.startswith("./"):
            p = p[2:]
        text = base.joinpath(p).read_text(encoding="utf-8")
        return json.loads(text)

    def _https_handler(uri: str) -> Any:
        """Map https://moltrouter.dev/schemas/mrp/0.1/... to bundled files.

        jsonschema will resolve relative refs against the envelope $id (https://moltrouter.dev/...).
        Without this handler, it tries to fetch over the network.
        """

        marker = "/schemas/mrp/0.1/"
        if marker in uri:
            rel = uri.split(marker, 1)[1]
            return _load_by_rel(rel)
        # Fallback: try to treat the URL path as a relative file
        # e.g. https://example/x/y.json -> y.json
        rel = uri.rsplit("/", 1)[-1]
        return _load_by_rel(rel)

    # Handlers are selected by URI scheme.
    resolver = jsonschema.RefResolver.from_schema(
        schema,
        handlers={
            "": _load_by_rel,  # relative refs
            "https": _https_handler,
            "http": _https_handler,
        },
    )

    jsonschema.validate(instance=envelope, schema=schema, resolver=resolver)
