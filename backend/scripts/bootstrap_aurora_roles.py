"""One-time Aurora post-migration bootstrap.

Sets app_user password to match Secrets Manager (via BOOTSTRAP_APP_PASSWORD env)
and grants mwadmin BYPASSRLS for admin SECURITY DEFINER functions.

Usage (ECS one-off task):
  BOOTSTRAP_APP_PASSWORD=... python -m scripts.bootstrap_aurora_roles
"""
from __future__ import annotations

import asyncio
import os
import sys

import asyncpg


def _dsn() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


async def main() -> int:
    app_pass = os.environ.get("BOOTSTRAP_APP_PASSWORD")
    if not app_pass:
        print("BOOTSTRAP_APP_PASSWORD is required", file=sys.stderr)
        return 1
    app_pass_sql = app_pass.replace("'", "''")
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        await conn.execute(f"ALTER ROLE app_user PASSWORD '{app_pass_sql}'")
        await conn.execute("ALTER ROLE mwadmin BYPASSRLS")
        print("bootstrap SQL ok")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
