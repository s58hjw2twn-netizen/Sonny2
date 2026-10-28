"""Fail-closed bearer-token gate for a future private remote bridge.

Prototype security primitive only: a static secret is NOT sufficient for
production ChatGPT OAuth, user authorization, or public deployment.
"""
from __future__ import annotations

import hmac


def authorize_bearer(headers: object, expected_token: object) -> bool:
    if not isinstance(expected_token, str) or len(expected_token) < 32:
        return False
    if not isinstance(headers, (list, tuple)):
        return False
    authorization = []
    for item in headers:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False
        key, value = item
        if not isinstance(key, bytes) or not isinstance(value, bytes):
            return False
        if key.lower() == b"authorization":
            authorization.append(value)
    if len(authorization) != 1:
        return False
    try:
        scheme, token = authorization[0].decode("ascii").split(" ", 1)
    except (UnicodeDecodeError, ValueError):
        return False
    if scheme.lower() != "bearer" or not token or token.strip() != token:
        return False
    return hmac.compare_digest(token, expected_token)
