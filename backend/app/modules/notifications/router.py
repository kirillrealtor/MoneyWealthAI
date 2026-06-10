"""Notifications routes: in-app feed, read state, and preference center."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_auth
from app.notifications.preferences import load_preferences, update_preferences

from . import service
from .schemas import MessageResponse, NotificationList, PreferencesOut, PreferencesUpdate

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications(user: CurrentUser = Depends(require_auth)) -> NotificationList:
    return NotificationList(**await service.list_notifications(user.user_id, user.tenant_id))


@router.post("/{alert_id}/read", response_model=MessageResponse)
async def mark_read(alert_id: UUID, user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    await service.mark_read(user.user_id, user.tenant_id, str(alert_id))
    return MessageResponse(message="Marked read.")


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_read(user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    await service.mark_all_read(user.user_id, user.tenant_id)
    return MessageResponse(message="All notifications marked read.")


@router.get("/preferences", response_model=PreferencesOut)
async def get_preferences(user: CurrentUser = Depends(require_auth)) -> PreferencesOut:
    prefs = await load_preferences(user.user_id, user.tenant_id)
    return PreferencesOut(**{k: prefs[k] for k in PreferencesOut.model_fields})


@router.patch("/preferences", response_model=PreferencesOut)
async def patch_preferences(body: PreferencesUpdate,
                            user: CurrentUser = Depends(require_auth)) -> PreferencesOut:
    prefs = await update_preferences(user.user_id, user.tenant_id, body.model_dump(exclude_unset=True))
    return PreferencesOut(**{k: prefs[k] for k in PreferencesOut.model_fields})
