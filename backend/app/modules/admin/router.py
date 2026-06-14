"""Admin HTTP routes — separate audience + server-side RBAC on every endpoint."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.deps import rate_limit

from . import service
from .deps import CurrentAdmin, require_admin, require_role
from .schemas import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminUserDetail,
    AdminUserList,
    AdminUserRow,
    AdminUserUpdate,
    AuditList,
    AuditRow,
    Kpis,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/auth/login", response_model=AdminTokenResponse,
             dependencies=[Depends(rate_limit("admin_login", 10))])
async def login(body: AdminLoginRequest, request: Request) -> AdminTokenResponse:
    result = await service.login(body.email, body.password, _ip(request))
    return AdminTokenResponse(access_token=result["access_token"], role=result["role"])


@router.get("/metrics", response_model=Kpis)
async def metrics(_: CurrentAdmin = Depends(require_admin)) -> Kpis:
    return Kpis(**await service.kpis())


@router.get("/users", response_model=AdminUserList)
async def users(
    _: CurrentAdmin = Depends(require_admin),
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminUserList:
    items = await service.list_users(search, limit, offset)
    return AdminUserList(items=[AdminUserRow(**u) for u in items], limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def user_detail(user_id: UUID, _: CurrentAdmin = Depends(require_admin)) -> AdminUserDetail:
    return AdminUserDetail(**await service.get_user(str(user_id)))


@router.patch("/users/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: UUID, body: AdminUserUpdate, request: Request,
    admin: CurrentAdmin = Depends(require_role("support")),
) -> AdminUserDetail:
    await service.update_user(
        admin_id=admin.admin_id, user_id=str(user_id), tier=body.tier,
        suspended=body.suspended, is_verified=body.is_verified, reason=body.reason, ip=_ip(request),
    )
    return AdminUserDetail(**await service.get_user(str(user_id)))


@router.get("/audit", response_model=AuditList)
async def audit_feed(
    _: CurrentAdmin = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AuditList:
    items = await service.audit_feed(limit, offset)
    return AuditList(items=[AuditRow(**a) for a in items], limit=limit, offset=offset)
