from __future__ import annotations

from fastapi import APIRouter

from mrpd.core.errors import mrp_error
from mrpd.core.schema import validate_envelope

router = APIRouter()


@router.get("/.well-known/mrp.json")
async def well_known() -> dict:
    return {
        "mrp_version": "0.1",
        "capabilities": ["registry_query", "route", "validate", "bridge"],
        "manifest_url": "/mrp/manifest",
    }


@router.get("/mrp/manifest")
async def manifest() -> dict:
    # Minimal placeholder manifest for the daemon itself.
    return {
        "capability_id": "service:mrpd",
        "capability": "router",
        "version": "0.1",
        "tags": ["mrp", "router", "gateway"],
        "inputs": [],
        "outputs": [],
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

    # Placeholder: no real offers yet.
    return {
        "mrp_version": envelope.get("mrp_version", "0.1"),
        "msg_id": envelope.get("msg_id"),
        "msg_type": "OFFER",
        "timestamp": envelope.get("timestamp"),
        "sender": {"id": "service:mrpd"},
        "payload": {"offers": []},
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

    return mrp_error(
        msg_id=envelope.get("msg_id"),
        timestamp=envelope.get("timestamp"),
        code="MRP_NOT_IMPLEMENTED",
        message="mrpd execute not implemented yet",
        retryable=False,
    )
