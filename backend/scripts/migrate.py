"""Minimal forward-only migration runner for SQLite.

Runs every db/migrations/*.sql file (sorted) exactly once, each in its own
transaction, recording applied files in schema_migrations.

Usage: python -m scripts.migrate
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import aiosqlite
from dotenv import load_dotenv

load_dotenv()

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"


def _get_db_path() -> str:
    url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ["DATABASE_URL"]
    if url.startswith("sqlite+aiosqlite:///"):
        return url[len("sqlite+aiosqlite:///") :]
    elif url.startswith("sqlite:///"):
        return url[len("sqlite:///") :]
    return url


async def main() -> int:
    db_path = _get_db_path()
    if db_path != ":memory:" and not os.path.isabs(db_path):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(backend_dir, db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = await aiosqlite.connect(db_path)
    try:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                   filename   TEXT PRIMARY KEY,
                   applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
               );"""
        )
        await conn.commit()

        # Query applied migrations
        applied = set()
        async with conn.execute("SELECT filename FROM schema_migrations") as cursor:
            async for row in cursor:
                applied.add(row[0])

        files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))

        count = 0
        for path in files:
            if path.name in applied:
                continue
            sql = path.read_text(encoding="utf-8")
            print(f"Applying {path.name} ... ", end="", flush=True)
            try:
                # SQLite executes scripts using executescript, which handles transactions
                # or executes them inside one. We execute the script and write schema_migrations entry.
                await conn.executescript(sql)
                await conn.execute("INSERT INTO schema_migrations (filename) VALUES (?)", (path.name,))
                await conn.commit()
                print("done")
                count += 1
            except Exception as err:
                print("FAILED")
                print(err, file=sys.stderr)
                return 1

        print("No pending migrations." if count == 0 else f"Applied {count} migration(s).")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
