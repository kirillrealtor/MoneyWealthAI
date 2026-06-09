"""FastAPI application factory + lifecycle."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.db import close_pool, init_pool
from app.errors import register_exception_handlers
from app.logging_conf import configure_logging, logger
from app.middleware import SecurityMiddleware, TracingMiddleware
from app.modules.advisor.router import router as advisor_router
from app.modules.auth.router import router as auth_router
from app.modules.health.router import router as health_router
from app.modules.plaid.router import router as plaid_router
from app.modules.plaid.router import webhook_router as plaid_webhook_router
from app.redis_client import close_redis


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await init_pool()
    logger.info("server starting", service="api", port=settings.port, env=settings.env)
    try:
        yield
    finally:
        await close_pool()
        await close_redis()
        logger.info("server stopped", service="api")


def create_app() -> FastAPI:
    app = FastAPI(title="AI Financial Advisor API", version="1.0.0", lifespan=lifespan)

    # NOTE: Starlette applies middleware in reverse add order, so the LAST added
    # runs FIRST. Order below means: Tracing (outermost) -> Security -> CORS ->
    # TrustedHost -> handler.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,  # empty = no cross-origin
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["authorization", "content-type", "x-tenant-id", "x-trace-id"],
    )
    app.add_middleware(SecurityMiddleware)
    # Pure-ASGI tracing wraps everything so trace_id is set before handlers run.
    app.add_middleware(TracingMiddleware)

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(plaid_router)
    app.include_router(plaid_webhook_router)
    app.include_router(advisor_router)
    return app


app = create_app()
