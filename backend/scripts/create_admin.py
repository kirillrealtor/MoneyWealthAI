"""Bootstrap (or reset) an admin account.

Usage:
    python -m scripts.create_admin <email> <password> [role]

role ∈ {super_admin, owner, support, analyst} (default: super_admin).
Idempotent: re-running updates the password + role for that email.
"""
from __future__ import annotations

import asyncio
import sys

from app.crypto import hash_password
from app.db import close_pool, execute, init_pool
from app.redis_client import close_redis

ROLES = {"super_admin", "owner", "support", "analyst"}


async def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    email = sys.argv[1].lower().strip()
    password = sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "super_admin"
    if role not in ROLES:
        print(f"Invalid role '{role}'. Choose one of: {', '.join(sorted(ROLES))}")
        return 2
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return 2

    await init_pool()
    try:
        await execute(
            """INSERT INTO admins (email, password_hash, role)
               VALUES ($1, $2, $3)
               ON CONFLICT (email) DO UPDATE
                   SET password_hash = EXCLUDED.password_hash, role = EXCLUDED.role, is_active = true""",
            email,
            hash_password(password),
            role,
        )
    finally:
        await close_redis()
        await close_pool()
    print(f"Admin ready: {email} ({role})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
