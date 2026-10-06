import os
import time

import jwt
from fastapi import Header, HTTPException


JWT_ALGORITHM = "HS256"
JWT_ISSUER = "sonny-assistant"
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7


def _secret() -> str:
    secret = os.getenv("SONNY_AUTH_SECRET")

    if not secret:
        raise RuntimeError(
            "SONNY_AUTH_SECRET is not configured"
        )

    return secret


def create_access_token(user_id: str) -> str:
    now = int(time.time())

    payload = {
        "sub": user_id,
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }

    return jwt.encode(
        payload,
        _secret(),
        algorithm=JWT_ALGORITHM,
    )


def authenticated_user(
    authorization: str | None = Header(None),
) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=401,
            detail="Invalid token subject",
        )

    return user_id
