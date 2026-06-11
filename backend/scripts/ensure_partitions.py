"""Create upcoming monthly transactions partitions (no-op on SQLite).

SQLite doesn't support table partitioning, so this script is a no-op.
"""
from __future__ import annotations

import asyncio


async def main() -> int:
    print("Table partitioning is not supported or required on SQLite database. Skipping.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
