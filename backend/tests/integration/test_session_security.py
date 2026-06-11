"""Refresh-token reuse detection: a replayed (rotated-away) token revokes the
whole session family. Exercised at the service layer because the test client's
base_url doesn't round-trip the host-scoped refresh cookie."""
from __future__ import annotations

import time

import httpx
import pytest

from app.config import settings
from app.errors import ApiError
from app.modules.auth.service import AuthCtx, refresh
from app.modules.auth.tokens import issue_refresh_token
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="SQLite is always reachable")


async def test_refresh_reuse_revokes_whole_family(client: httpx.AsyncClient) -> None:
    email = f"sess+{int(time.time()*1000)}@example.com"
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
    user_id = r.json()["user_id"]
    tenant = settings.default_tenant_id
    ctx = AuthCtx(ip="10.0.0.1", user_agent="pytest")

    raw1 = await issue_refresh_token(user_id, tenant, "10.0.0.1", "pytest")
    pair = await refresh(raw1, ctx)        # rotates: raw1 revoked, raw2 issued
    raw2 = pair.refresh_token

    # Replaying the old (revoked) token signals theft -> 401 AND family revoke.
    with pytest.raises(ApiError) as e1:
        await refresh(raw1, ctx)
    assert e1.value.code == "UNAUTHORIZED"

    # Because the family was revoked, the previously-valid raw2 is now dead too.
    with pytest.raises(ApiError) as e2:
        await refresh(raw2, ctx)
    assert e2.value.code == "UNAUTHORIZED"
