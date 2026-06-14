"""Admin auth + RBAC dependencies. Enforced SERVER-SIDE on every admin route."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import jwt
from fastapi import Depends, Request

from app import db
from app.errors import ApiError

from .tokens import verify_admin_token

# Role hierarchy (higher index = more privilege). A route requires a minimum.
ROLE_ORDER = {"analyst": 0, "support": 1, "owner": 2, "super_admin": 3}


@dataclass
class CurrentAdmin:
    admin_id: str
    role: str


async def require_admin(request: Request) -> CurrentAdmin:
    header = request.headers.get("authorization")
    if not header or not header.startswith("Bearer "):
        raise ApiError("UNAUTHORIZED")
    try:
        claims = verify_admin_token(header[len("Bearer "):])
    except jwt.PyJWTError as err:
        raise ApiError("UNAUTHORIZED") from err

    # Confirm the admin still exists and is active (token alone isn't enough).
    row = await db.fetchrow(
        "SELECT admin_id, role, is_active FROM admins WHERE admin_id = $1", claims["sub"]
    )
    if row is None or not row["is_active"]:
        raise ApiError("UNAUTHORIZED")
    return CurrentAdmin(admin_id=str(row["admin_id"]), role=row["role"])


def require_role(minimum: str) -> Callable[[CurrentAdmin], Awaitable[CurrentAdmin]]:
    """Gate a route behind a minimum role. UI hiding is convenience only — this
    is the security boundary."""
    threshold = ROLE_ORDER[minimum]

    async def _dep(admin: CurrentAdmin = Depends(require_admin)) -> CurrentAdmin:
        if ROLE_ORDER.get(admin.role, -1) < threshold:
            raise ApiError("FORBIDDEN", details={"reason": f"Requires {minimum} or higher."})
        return admin

    return _dep
