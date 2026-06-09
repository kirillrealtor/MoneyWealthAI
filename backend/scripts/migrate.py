"""Minimal forward-only migration runner.

Runs every db/migrations/*.sql file (sorted) exactly once, each in its own
transaction, recording applied files in schema_migrations.

Usage: python -m scripts.migrate
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"


def _dsn() -> str:
    # Migrations run as the owner/superuser. Prefer MIGRATION_DATABASE_URL;
    # fall back to DATABASE_URL for single-role setups.
    url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ["DATABASE_URL"]
    return "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url


async def main() -> int:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                   filename   TEXT PRIMARY KEY,
                   applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
               );"""
        )
        applied = {r["filename"] for r in await conn.fetch("SELECT filename FROM schema_migrations")}
        files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))

        count = 0
        for path in files:
            if path.name in applied:
                continue
            sql = path.read_text(encoding="utf-8")
            print(f"Applying {path.name} ... ", end="", flush=True)
            try:
                async with conn.transaction():
                    await conn.execute(sql)  # simple-query protocol: multi-statement ok
                    await conn.execute("INSERT INTO schema_migrations (filename) VALUES ($1)", path.name)
                print("done")
                count += 1
            except Exception as err:  # noqa: BLE001
                print("FAILED")
                print(err, file=sys.stderr)
                return 1

        print("No pending migrations." if count == 0 else f"Applied {count} migration(s).")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
