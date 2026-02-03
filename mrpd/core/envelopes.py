from __future__ import annotations

import uuid
from typing import Any

from mrpd.core.util import utc_now_rfc3339


def mk_envelope(msg_type: str, payload: dict[str, Any], *, sender_id: str = "agent:mrpd/client") -> dict[str, Any]:
    return {
        "mrp_version": "0.1",
        "msg_id": str(uuid.uuid4()),
        "msg_type": msg_type,
        "timestamp": utc_now_rfc3339(),
        "sender": {"id": sender_id},
        "payload": payload,
    }
