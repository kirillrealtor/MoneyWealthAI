"""Provide valid env so app.config passes validation under tests.

Defaults match the local SQLite database and Redis :6380 datastore. Integration tests
use these; unit tests never open a connection.
"""
from __future__ import annotations

import base64
import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///financial_advisor_test.db")
os.environ.setdefault("MIGRATION_DATABASE_URL", "sqlite:///financial_advisor_test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6380")
os.environ.setdefault("JWT_ACCESS_SECRET", "test_access_secret_at_least_32_chars_long_000")
os.environ.setdefault("JWT_REFRESH_SECRET", "test_refresh_secret_at_least_32_chars_long_00")
# AES-256 key (base64 of exactly 32 bytes) for Plaid token-encryption tests.
os.environ.setdefault("PLAID_ENC_KEY", base64.b64encode(b"test-key-32-bytes-long-aes256!!!").decode())

import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> None:
    url = os.environ.get("DATABASE_URL", "sqlite:///financial_advisor_test.db")
    if url.startswith("sqlite:///"):
        db_path = url[len("sqlite:///"): ]
        if db_path != ":memory:":
            backend_dir = Path(__file__).resolve().parent.parent
            full_path = backend_dir / db_path
            for suffix in ("", "-shm", "-wal"):
                p = Path(f"{full_path}{suffix}")
                if p.exists():
                    try:
                        p.unlink()
                    except OSError:
                        pass

    from scripts.migrate import main as run_migrations
    ret = await run_migrations()
    if ret != 0:
        raise RuntimeError(f"Database migrations failed with exit code {ret}")

