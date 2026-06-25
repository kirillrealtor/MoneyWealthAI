"""Thin async Plaid API client (direct httpx).

Chosen over the SDK for explicit control of timeouts, retries, and error
mapping at scale. Credentials (client_id/secret) are injected per request and
NEVER logged; access tokens are treated as secrets in logs too.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import settings
from app.errors import ApiError
from app.logging_conf import logger

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_RETRYABLE = {429, 500, 502, 503, 504}
_MAX_RETRIES = 2


class PlaidNotConfigured(RuntimeError):
    pass


class PlaidClient:
    def __init__(self, env: str) -> None:
        self._client_id = settings.plaid_client_id
        if not self._client_id or not settings.plaid_enc_key:
            raise PlaidNotConfigured("Plaid client_id or enc_key not configured")
        
        self._env = env
        if env == "sandbox":
            self._base = "https://sandbox.plaid.com"
            self._secret = settings.plaid_sandbox_secret
        elif env == "development":
            self._base = "https://development.plaid.com"
            self._secret = settings.plaid_development_secret
        elif env == "production":
            self._base = "https://production.plaid.com"
            self._secret = settings.plaid_development_secret
        else:
            raise ValueError(f"Invalid Plaid env: {env}")
            
        if not self._secret:
            raise PlaidNotConfigured(f"Plaid secret for {env} not configured")

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"client_id": self._client_id, "secret": self._secret, **payload}
        last_exc: Exception | None = None
        async with httpx.AsyncClient(base_url=self._base, timeout=_TIMEOUT) as client:
            for attempt in range(_MAX_RETRIES + 1):
                try:
                    resp = await client.post(path, json=body)
                    if resp.status_code == 200:
                        return resp.json()  # type: ignore[no-any-return]
                    if resp.status_code in _RETRYABLE and attempt < _MAX_RETRIES:
                        await asyncio.sleep(0.25 * (2**attempt))
                        continue
                    # Map Plaid error without leaking secrets.
                    err = _safe_error(resp)
                    # Log integration details server-side; return a generic error
                    # to the client (don't expose Plaid internals / error codes).
                    logger.warning(
                        "plaid api error", service="plaid", path=path, status=resp.status_code, plaid_error=err
                    )
                    raise ApiError("PLAID_ERROR")
                except httpx.HTTPError as exc:
                    last_exc = exc
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(0.25 * (2**attempt))
                        continue
                    logger.error("plaid network error", service="plaid", path=path, error_message=str(exc))
                    raise ApiError("PLAID_ERROR") from exc
        raise ApiError("PLAID_ERROR") from last_exc  # pragma: no cover

    # ---- Link / items ----
    async def create_link_token(self, user_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "user": {"client_user_id": user_id},
            "client_name": "AI Financial Advisor",
            "products": settings.plaid_products_list,
            "country_codes": settings.plaid_country_codes_list,
            "language": "en",
        }
        if settings.plaid_redirect_uri:
            payload["redirect_uri"] = settings.plaid_redirect_uri
        if settings.plaid_webhook_url:
            payload["webhook"] = settings.plaid_webhook_url
        return await self._post("/link/token/create", payload)

    async def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        return await self._post("/item/public_token/exchange", {"public_token": public_token})

    async def get_item(self, access_token: str) -> dict[str, Any]:
        return await self._post("/item/get", {"access_token": access_token})

    async def item_remove(self, access_token: str) -> dict[str, Any]:
        return await self._post("/item/remove", {"access_token": access_token})

    async def get_accounts(self, access_token: str) -> dict[str, Any]:
        return await self._post("/accounts/get", {"access_token": access_token})

    async def transactions_sync(self, access_token: str, cursor: str | None, count: int = 500) -> dict[str, Any]:
        payload: dict[str, Any] = {"access_token": access_token, "count": count}
        if cursor:
            payload["cursor"] = cursor
        return await self._post("/transactions/sync", payload)

    async def investments_holdings_get(self, access_token: str) -> dict[str, Any]:
        return await self._post("/investments/holdings/get", {"access_token": access_token})

    async def liabilities_get(self, access_token: str) -> dict[str, Any]:
        return await self._post("/liabilities/get", {"access_token": access_token})

    async def webhook_verification_key_get(self, key_id: str) -> dict[str, Any]:
        return await self._post("/webhook_verification_key/get", {"key_id": key_id})


def _safe_error(resp: httpx.Response) -> dict[str, Any]:
    """Extract Plaid's structured error fields, dropping anything sensitive."""
    try:
        data = resp.json()
    except Exception:  # noqa: BLE001
        return {"error_type": "UNKNOWN", "status": resp.status_code}
    return {
        "error_type": data.get("error_type"),
        "error_code": data.get("error_code"),
        "request_id": data.get("request_id"),
    }


def get_plaid(env: str | None = None) -> PlaidClient:
    """Construct a client or raise a generic error if Plaid isn't configured.
    The 'not configured' detail is logged, not returned (don't disclose env state)."""
    target_env = env or settings.plaid_env
    try:
        return PlaidClient(target_env)
    except PlaidNotConfigured as err:
        logger.error("plaid not configured", service="plaid", env=target_env)
        raise ApiError("PLAID_ERROR") from err
