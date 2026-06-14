"""Dedicated Plaid-sync worker process (the worker fleet).

Runs the durable-queue drain loop independently of the API, so background sync
never competes with request handling and scales horizontally: run as many
replicas as throughput needs — FOR UPDATE SKIP LOCKED hands each one disjoint
jobs. Shuts down cleanly on SIGINT/SIGTERM (the in-flight batch finishes, the
rest stay 'pending' for another worker).

Usage: python -m scripts.worker
"""
from __future__ import annotations

import asyncio
import signal

from dotenv import load_dotenv

load_dotenv()


async def main() -> int:
    from app import db
    from app.logging_conf import configure_logging, logger
    from app.modules.plaid.worker import run_worker_loop
    from app.redis_client import close_redis

    configure_logging()
    await db.init_pool()
    stop = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows: no add_signal_handler for SIGTERM
            signal.signal(sig, lambda *_: stop.set())

    try:
        await run_worker_loop(stop=stop)
    finally:
        await db.close_pool()
        await close_redis()
        logger.info("worker stopped", service="plaid-worker")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
