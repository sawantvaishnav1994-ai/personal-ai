from __future__ import annotations

import re
from typing import Any

# Narrow value-pattern redaction for externally influenced owner-facing text.
# It preserves ordinary/user-authored prose and removes only credential-shaped material.
_PATTERNS = (
    re.compile(r'(?i)(authorization\\s*:\\s*)(?:bearer\\s+)?[^\\s,;]+'),
    re.compile(r'(?i)\\bbearer\\s+[A-Za-z0-9._~+\\/=-]{8,}'),
    re.compile(r'(?i)\\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|credential|session[_-]?(?:token|secret)|cookie)\\b(\\s*[:=]\\s*)([^\\s&;,]+)'),
    re.compile(r'(?is)-----BEGIN [^-\\r\\n]*PRIVATE KEY-----.*?-----END [^-\\r\\n]*PRIVATE KEY-----'),
)


def sanitize_sensitive_text(value: str) -> str:
    text = str(value)
    text = _PATTERNS[0].sub(r'\\1[redacted]', text)
    text = _PATTERNS[1].sub('[redacted bearer token]', text)
    text = _PATTERNS[2].sub(lambda m: f'{m.group(1)}{m.group(2)}[redacted]', text)
    text = _PATTERNS[3].sub('[redacted private key]', text)
    return text


def sanitize_external_value(value: Any, *, depth: int = 0):
    if depth > 12:
        return value
    if isinstance(value, dict):
        return {key: sanitize_external_value(item, depth=depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_external_value(item, depth=depth + 1) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_external_value(item, depth=depth + 1) for item in value)
    if isinstance(value, str):
        return sanitize_sensitive_text(value)
    return value
