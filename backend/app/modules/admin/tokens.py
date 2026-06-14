"""Admin JWT — separate audience from end-user tokens (blast-radius isolation)."""
from __future__ import annotations

import time
from typing import Any

import jwt

from app.config import settings


def sign_admin_token(admin_id: str, role: str) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": admin_id,
        "role": role,
        "iat": now,
        "exp": now + settings.admin_access_token_ttl,
        "iss": settings.jwt_issuer,
        "aud": settings.admin_jwt_audience,  # distinct from the user audience
    }
    return jwt.encode(payload, settings.jwt_access_secret, algorithm="HS256")


def verify_admin_token(token: str) -> dict[str, Any]:
    # The audience check is what stops a user access token from reaching admin
    # routes — it was minted for `jwt_audience`, not `admin_jwt_audience`.
    return jwt.decode(
        token,
        settings.jwt_access_secret,
        algorithms=["HS256"],
        audience=settings.admin_jwt_audience,
        issuer=settings.jwt_issuer,
    )
