from __future__ import annotations

from fastapi import APIRouter

from mrpd.core.errors import mrp_error
from mrpd.core.schema import validate_envelope

router = APIRouter()


@router.get("/.well-known/mrp.json")
async def well_known() -> dict:
    return {
        "mrp_version": "0.1",
        "capabilities": ["summarize_url"],
        "manifest_url": "/mrp/manifest",
    }


@router.get("/mrp/manifest")
async def manifest() -> dict:
    # Provider manifest for the built-in demo capability.
    # NOTE: this endpoint returns relative URLs; clients may prefer absolute.
    # Our `mrpd run` prefers manifests from registry entries (absolute endpoints).
    return {
        "capability_id": "capability:mrp/summarize_url",
        "capability": "summarize_url",
        "version": "0.1",
        "tags": ["mrp", "summarize", "web"],
        "inputs": [{"type": "url"}],
        "outputs": [{"type": "markdown"}, {"type": "artifact"}],
        "constraints": {"policy": ["no_pii"]},
        "proofs_required": [],
        "endpoints": {
            "discover": "/mrp/discover",
            "negotiate": "/mrp/negotiate",
            "execute": "/mrp/execute",
        },
    }


@router.post("/mrp/hello")
async def hello(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        return mrp_error(
            msg_id=envelope.get("msg_id"),
            timestamp=envelope.get("timestamp"),
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    return {
        "mrp_version": envelope.get("mrp_version", "0.1"),
        "msg_id": envelope.get("msg_id"),
        "msg_type": "HELLO",
        "timestamp": envelope.get("timestamp"),
        "sender": {"id": "service:mrpd"},
        "payload": {"ok": True, "schemas": ["0.1"]},
    }


@router.post("/mrp/discover")
async def discover(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        return mrp_error(
            msg_id=envelope.get("msg_id"),
            timestamp=envelope.get("timestamp"),
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    from mrpd.core.provider import offers_for_discover

    offers = offers_for_discover(envelope.get("payload") or {})
    return {
        "mrp_version": envelope.get("mrp_version", "0.1"),
        "msg_id": envelope.get("msg_id"),
        "msg_type": "OFFER",
        "timestamp": envelope.get("timestamp"),
        "sender": {"id": "service:mrpd"},
        "payload": {"offers": offers},
    }


@router.post("/mrp/negotiate")
async def negotiate(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        return mrp_error(
            msg_id=envelope.get("msg_id"),
            timestamp=envelope.get("timestamp"),
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    return {
        "mrp_version": envelope.get("mrp_version", "0.1"),
        "msg_id": envelope.get("msg_id"),
        "msg_type": "NEGOTIATE",
        "timestamp": envelope.get("timestamp"),
        "sender": {"id": "service:mrpd"},
        "payload": {"accepted": False, "reason": "not implemented"},
    }


@router.post("/mrp/execute")
async def execute(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        return mrp_error(
            msg_id=envelope.get("msg_id"),
            timestamp=envelope.get("timestamp"),
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    from mrpd.core.provider import execute_summarize_url

    payload = envelope.get("payload") or {}
    route_id = payload.get("route_id")
    inputs = payload.get("inputs") or []

    try:
        if route_id == "route:mrpd/summarize_url@0.1":
            evidence = await execute_summarize_url(inputs)
        else:
            return mrp_error(
                msg_id=envelope.get("msg_id"),
                timestamp=envelope.get("timestamp"),
                code="MRP_INVALID_REQUEST",
                message=f"Unknown route_id: {route_id}",
                retryable=False,
            )
    except Exception as e:
        return mrp_error(
            msg_id=envelope.get("msg_id"),
            timestamp=envelope.get("timestamp"),
            code="MRP_INTERNAL_ERROR",
            message=str(e),
            retryable=False,
        )

    return {
        "mrp_version": envelope.get("mrp_version", "0.1"),
        "msg_id": envelope.get("msg_id"),
        "msg_type": "EVIDENCE",
        "timestamp": envelope.get("timestamp"),
        "sender": {"id": "service:mrpd"},
        "payload": {"route_id": route_id, **evidence},
    }
