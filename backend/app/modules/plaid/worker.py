"""Durable Plaid-sync worker.

Replaces the old fire-and-forget asyncio tasks. Work is enqueued into the
sync_jobs table (survives restarts) and drained by a worker that claims jobs
atomically with FOR UPDATE SKIP LOCKED — so any number of workers, across any
number of instances, pull disjoint jobs with no double-processing. A crashed
worker's in-flight jobs are requeued by the recovery sweep.

Run it as a dedicated process (the worker fleet):  python -m scripts.worker
or, for single-node/dev, set SYNC_WORKER_ENABLED=true to run one in-process
worker alongside the API (started in the app lifespan).
"""
from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from app import db
from app.config import settings
from app.logging_conf import logger

from .sync import sync_item_core


async def enqueue_sync(item_id: str, tenant_id: str, user_id: str) -> str | None:
    """Durably enqueue a sync for one item. Idempotent: returns None if a job
    for the item is already pending/running (coalesced), else the new sync_id."""
    sync_id = await db.fetchval("SELECT enqueue_sync_job($1, $2, $3)", item_id, tenant_id, user_id)
    if sync_id is not None:
        logger.info("sync enqueued", service="plaid-worker", item_id=item_id)
    return str(sync_id) if sync_id is not None else None


async def _claim(limit: int) -> list[Any]:
    return await db.fetch("SELECT sync_id, item_id, tenant_id, user_id FROM claim_sync_jobs($1)", limit)


async def _mark_completed(sync_id: str, tenant_id: str, added: int) -> None:
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute(
            "UPDATE sync_jobs SET status = 'completed', transactions_synced = $1, "
            "completed_at = NOW() WHERE sync_id = $2",
            added, sync_id,
        )


async def _mark_failed_or_retry(sync_id: str, tenant_id: str, err: str) -> None:
    """A failed run is requeued (status back to 'pending') until retry_count hits
    the cap, after which it stays 'failed'. The worker that picks it up next gets
    a fresh attempt — transient Plaid/network errors self-heal."""
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute(
            """UPDATE sync_jobs
                  SET retry_count = retry_count + 1,
                      error_message = $1,
                      status = CASE WHEN retry_count + 1 > $2 THEN 'failed' ELSE 'pending' END,
                      completed_at = CASE WHEN retry_count + 1 > $2 THEN NOW() ELSE NULL END
                WHERE sync_id = $3""",
            err[:500], settings.sync_job_max_retries, sync_id,
        )


async def process_job(job: Any, sem: asyncio.Semaphore) -> None:
    sync_id, item_id, tenant_id, user_id = (
        str(job["sync_id"]), str(job["item_id"]), str(job["tenant_id"]), str(job["user_id"])
    )
    async with sem:
        try:
            added = await sync_item_core(item_id, tenant_id, user_id)
            await _mark_completed(sync_id, tenant_id, added)
        except Exception as err:  # noqa: BLE001 - one bad job must not sink the worker
            logger.error("sync job failed", service="plaid-worker", item_id=item_id, error_message=str(err))
            with contextlib.suppress(Exception):
                await _mark_failed_or_retry(sync_id, tenant_id, str(err))


async def run_worker_loop(*, stop: asyncio.Event | None = None) -> None:
    """Poll the queue until `stop` is set (or forever). Recovers stale jobs every
    cycle, claims a batch, and processes the batch with bounded concurrency."""
    stop = stop or asyncio.Event()
    sem = asyncio.Semaphore(settings.sync_worker_concurrency)
    logger.info("plaid sync worker started", service="plaid-worker",
                batch=settings.sync_worker_batch, concurrency=settings.sync_worker_concurrency)
    while not stop.is_set():
        try:
            recovered = await db.fetchval(
                "SELECT recover_stale_sync_jobs($1, $2)",
                settings.sync_job_stale_seconds, settings.sync_job_max_retries,
            )
            if recovered:
                logger.warning("recovered stale sync jobs", service="plaid-worker", count=int(recovered))

            jobs = await _claim(settings.sync_worker_batch)
            if jobs:
                await asyncio.gather(*(process_job(j, sem) for j in jobs))
                continue  # drain fast when there's a backlog
        except Exception as err:  # noqa: BLE001 - keep the loop alive across blips
            logger.error("worker loop error", service="plaid-worker", error_message=str(err))

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=settings.sync_worker_poll_interval_s)
