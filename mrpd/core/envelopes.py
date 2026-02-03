from __future__ import annotations

import uuid
from typing import Any

from mrpd.core.util import utc_now_rfc3339


def mk_envelope(
    msg_type: str,
    payload: dict[str, Any],
    *,
    sender_id: str = "agent:mrpd/client",
    receiver_id: str | None = None,
    in_reply_to: str | None = None,
) -> dict[str, Any]:
    env = {
        "mrp_version": "0.1",
        "msg_id": str(uuid.uuid4()),
        "msg_type": msg_type,
        "timestamp": utc_now_rfc3339(),
        "sender": {"id": sender_id},
        "payload": payload,
    }
    if receiver_id:
        env["receiver"] = {"id": receiver_id}
    if in_reply_to:
        env["in_reply_to"] = in_reply_to
    return env
