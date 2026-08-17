from __future__ import annotations

import re

_KV_SECRET = re.compile(
    r"(?i)((?:api[_-]?key|token|secret|password|passwd|authorization)\s*[=:]\s*)\S+"
)
_TOKEN_LIKE = re.compile(
    r"(?:ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"
)


def redact(text: str) -> str:
    redacted = _KV_SECRET.sub(r"\1<redacted>", text)
    return _TOKEN_LIKE.sub("<redacted>", redacted)
