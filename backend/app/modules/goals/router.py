"""Goals HTTP routes (auth-gated)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_auth
from app.errors import ApiError

from . import service
from .schemas import GoalCreate, GoalOut, GoalUpdate, MessageResponse

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


@router.post("", response_model=GoalOut, status_code=201)
async def create(body: GoalCreate, user: CurrentUser = Depends(require_auth)) -> GoalOut:
    goal_id = await service.create_goal(
        user.user_id, user.tenant_id, title=body.title, description=body.description,
        target_amount=body.target_amount, current_amount=body.current_amount,
        target_date=body.target_date, priority=body.priority,
    )
    goal = next((g for g in await service.list_goals(user.user_id, user.tenant_id)
                 if g["goal_id"] == goal_id), None)
    if goal is None:
        raise ApiError("INTERNAL_ERROR")
    return GoalOut(**goal)


@router.get("", response_model=list[GoalOut])
async def list_goals(user: CurrentUser = Depends(require_auth)) -> list[GoalOut]:
    return [GoalOut(**g) for g in await service.list_goals(user.user_id, user.tenant_id)]


@router.patch("/{goal_id}", response_model=MessageResponse)
async def update(goal_id: UUID, body: GoalUpdate,
                 user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    await service.update_goal(
        user.user_id, user.tenant_id, str(goal_id), title=body.title, target_amount=body.target_amount,
        current_amount=body.current_amount, target_date=body.target_date,
        priority=body.priority, status=body.status,
    )
    return MessageResponse(message="Goal updated.")


@router.delete("/{goal_id}", response_model=MessageResponse)
async def delete(goal_id: UUID, user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    await service.delete_goal(user.user_id, user.tenant_id, str(goal_id))
    return MessageResponse(message="Goal deleted.")
