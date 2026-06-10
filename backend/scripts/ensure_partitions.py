"""Create upcoming monthly `transactions` partitions ahead of time.

Run monthly (cron / EventBridge). Calls the idempotent SQL function
`ensure_transactions_partition` (migration 005) for the current month plus the
next `MONTHS_AHEAD` so writes never fall into the default partition.

Usage: python -m scripts.ensure_partitions
"""
from __future__ import annotations

import asyncio
import os
from datetime import date

import asyncpg
from dotenv import load_dotenv

load_dotenv()

MONTHS_AHEAD = 3


def _dsn() -> str:
    # Partition DDL must run as the owner — use the migration URL if set.
    url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ["DATABASE_URL"]
    return "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url


def _add_months(d: date, n: int) -> date:
    total = (d.year * 12 + (d.month - 1)) + n
    return date(total // 12, total % 12 + 1, 1)


async def main() -> int:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        first = date.today().replace(day=1)
        for n in range(MONTHS_AHEAD + 1):
            month = _add_months(first, n)
            await conn.execute("SELECT ensure_transactions_partition($1)", month)
            print(f"ensured partition for {month:%Y-%m}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
