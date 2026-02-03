from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone


def utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def approx_tokens(text: str) -> int:
    # rough heuristic: ~4 chars/token for English-ish text
    return max(1, len(text) // 4)


def strip_html(html: str) -> str:
    # extremely simple tag stripper for v0 (good enough for demo)
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text
