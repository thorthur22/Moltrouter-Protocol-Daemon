from __future__ import annotations

from fastapi import APIRouter

from mrpd.core.errors import mrp_error
from mrpd.core.schema import validate_envelope

router = APIRouter()


def response_envelope(envelope: dict, *, msg_type: str, payload: dict) -> dict:
    """Build a response envelope.

    IMPORTANT: response message ids must be new, and in_reply_to must reference
    the triggering request msg_id.
    """

    from mrpd.core.util import utc_now_rfc3339
    import uuid

    sender_id = (envelope.get("sender") or {}).get("id")
    req_msg_id = envelope.get("msg_id")

    resp = {
        "mrp_version": envelope.get("mrp_version", "0.1"),
        "msg_id": str(uuid.uuid4()),
        "msg_type": msg_type,
        "timestamp": utc_now_rfc3339(),
        "sender": {"id": "service:mrpd"},
        "payload": payload,
    }
    if sender_id:
        resp["receiver"] = {"id": sender_id}
    if req_msg_id:
        resp["in_reply_to"] = req_msg_id
    return resp


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
        sender_id = (envelope.get("sender") or {}).get("id")
        msg_id = envelope.get("msg_id")
        return mrp_error(
            msg_id=msg_id,
            timestamp=envelope.get("timestamp"),
            receiver_id=sender_id,
            in_reply_to=msg_id,
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    return response_envelope(
        envelope,
        msg_type="HELLO",
        payload={"ok": True, "schemas": ["0.1"]},
    )


@router.post("/mrp/discover")
async def discover(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        sender_id = (envelope.get("sender") or {}).get("id")
        msg_id = envelope.get("msg_id")
        return mrp_error(
            msg_id=msg_id,
            timestamp=envelope.get("timestamp"),
            receiver_id=sender_id,
            in_reply_to=msg_id,
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    from mrpd.core.provider import offers_for_discover

    offers = offers_for_discover(envelope.get("payload") or {})
    return response_envelope(
        envelope,
        msg_type="OFFER",
        payload={"offers": offers},
    )


@router.post("/mrp/negotiate")
async def negotiate(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        sender_id = (envelope.get("sender") or {}).get("id")
        msg_id = envelope.get("msg_id")
        return mrp_error(
            msg_id=msg_id,
            timestamp=envelope.get("timestamp"),
            receiver_id=sender_id,
            in_reply_to=msg_id,
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    return response_envelope(
        envelope,
        msg_type="NEGOTIATE",
        payload={"accepted": False, "reason": "not implemented"},
    )


@router.post("/mrp/execute")
async def execute(envelope: dict) -> dict:
    try:
        validate_envelope(envelope)
    except Exception as e:
        sender_id = (envelope.get("sender") or {}).get("id")
        msg_id = envelope.get("msg_id")
        return mrp_error(
            msg_id=msg_id,
            timestamp=envelope.get("timestamp"),
            receiver_id=sender_id,
            in_reply_to=msg_id,
            code="MRP_INVALID_REQUEST",
            message=str(e),
            retryable=False,
        )

    from mrpd.core.provider import execute_summarize_url

    payload = envelope.get("payload") or {}
    route_id = payload.get("route_id")
    inputs = payload.get("inputs") or []
    job_id = (payload.get("job") or {}).get("id")

    try:
        if route_id == "route:mrpd/summarize_url@0.1":
            evidence = await execute_summarize_url(inputs)
        else:
            sender_id = (envelope.get("sender") or {}).get("id")
            msg_id = envelope.get("msg_id")
            return mrp_error(
                msg_id=msg_id,
                timestamp=envelope.get("timestamp"),
                receiver_id=sender_id,
                in_reply_to=msg_id,
                code="MRP_INVALID_REQUEST",
                message=f"Unknown route_id: {route_id}",
                retryable=False,
            )
    except Exception as e:
        sender_id = (envelope.get("sender") or {}).get("id")
        msg_id = envelope.get("msg_id")
        return mrp_error(
            msg_id=msg_id,
            timestamp=envelope.get("timestamp"),
            receiver_id=sender_id,
            in_reply_to=msg_id,
            code="MRP_INTERNAL_ERROR",
            message=str(e),
            retryable=False,
        )

    response_payload = {"route_id": route_id, **evidence}
    if job_id:
        response_payload["job_id"] = job_id
    return response_envelope(envelope, msg_type="EVIDENCE", payload=response_payload)
