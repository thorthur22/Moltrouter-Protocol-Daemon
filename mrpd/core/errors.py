from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def mrp_error(
    *,
    msg_id: str | None,
    timestamp: str | None,
    receiver_id: str | None = None,
    in_reply_to: str | None = None,
    code: str,
    message: str,
    retryable: bool = False,
    retry_after_ms: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message, "retryable": retryable}
    if retry_after_ms is not None:
        payload["retry_after_ms"] = retry_after_ms
    if details is not None:
        payload["details"] = details

    env = {
        "mrp_version": "0.1",
        "msg_id": msg_id,
        "msg_type": "ERROR",
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sender": {"id": "service:mrpd"},
        "payload": payload,
    }
    if receiver_id:
        env["receiver"] = {"id": receiver_id}
    if in_reply_to:
        env["in_reply_to"] = in_reply_to
    return env
