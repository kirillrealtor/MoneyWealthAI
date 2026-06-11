"""Run the alert engine across all users (cron-triggerable).

Usage: python -m scripts.run_alerts

Keyset-paginates users via the SECURITY DEFINER `list_users_for_scan` so the
cross-tenant scan doesn't need RLS bypass. PRODUCTION: this loop becomes a
scheduler that fans batches out to an SQS worker fleet — `run_alerts_for_user`
is already the per-user unit of work, so that's a transport swap, not a rewrite.
"""
from __future__ import annotations

import asyncio

from app import db
from app.alerts.engine import run_alerts_for_user
from app.db import close_pool, init_pool
from app.redis_client import close_redis

_BATCH = 500


async def main() -> int:
    await init_pool()
    after: str | None = None
    processed = 0
    dispatched = 0
    try:
        while True:
            rows = await db.fetch("SELECT user_id, tenant_id FROM list_users_for_scan($1, $2)", after, _BATCH)
            if not rows:
                break
            for r in rows:
                try:
                    dispatched += await run_alerts_for_user(str(r["user_id"]), str(r["tenant_id"]))
                except Exception as err:  # noqa: BLE001 - never let one user stop the scan
                    print(f"  user {r['user_id']} failed: {err}")
                processed += 1
            after = str(rows[-1]["user_id"])
    finally:
        # Close Redis too (the dispatcher uses it for dedup) — otherwise its
        # connection __del__ fires after the loop closes and spams the cron log
        # with "Event loop is closed" tracebacks on every run.
        await close_redis()
        await close_pool()
    print(f"Alert scan complete: {processed} users, {dispatched} notifications dispatched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
