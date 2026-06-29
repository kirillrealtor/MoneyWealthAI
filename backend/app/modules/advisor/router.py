"""Advisor HTTP routes. Auth-gated."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app import db
from app.ai.advisor import run_turn
from app.ai.prompts import PROMPT_VERSION
from app.config import settings
from app.deps import CurrentUser, rate_limit, require_auth
from app.errors import ApiError

from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatSummary,
    FeedbackRequest,
    MessageOut,
    MessageResponse,
)

router = APIRouter(prefix="/api/v1/advisor", tags=["advisor"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, user: CurrentUser = Depends(require_auth)) -> ChatResponse:
    # Persona + name are user profile; load tenant-scoped.
    async with db.with_tenant(user.tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT full_name, advisor_persona FROM users WHERE user_id = $1", user.user_id
        )
    if not row:
        raise ApiError("NOT_FOUND")
    first_name = (row["full_name"] or "").split(" ")[0] or None

    result = await run_turn(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        first_name=first_name,
        persona=row["advisor_persona"],
        tier=user.tier,
        chat_id=body.chat_id,
        message=body.message,
        module=body.module,
        ip=request.client.host if request.client else None,
    )
    return ChatResponse(
        chat_id=result.chat_id, message_id=result.message_id, response=result.response,
        tool_calls_made=result.tool_calls_made, provider=result.provider, tokens_used=result.tokens_used,
    )


@router.get("/chats", response_model=list[ChatSummary],
            dependencies=[Depends(rate_limit("read", settings.rate_limit_read_per_min))])
async def list_chats(user: CurrentUser = Depends(require_auth)) -> list[ChatSummary]:
    async with db.with_tenant(user.tenant_id, user.user_id) as conn:
        rows = await conn.fetch(
            """SELECT cs.chat_id, cs.started_at,
                      (SELECT cm.content FROM chat_messages cm
                        WHERE cm.chat_id = cs.chat_id AND cm.role = 'user'
                        ORDER BY cm.created_at ASC LIMIT 1) AS preview
                 FROM chat_sessions cs
                WHERE cs.user_id = $1
                ORDER BY cs.started_at DESC LIMIT 30""",
            user.user_id,
        )
    return [
        ChatSummary(chat_id=str(r["chat_id"]), started_at=r["started_at"], preview=r["preview"])
        for r in rows
    ]


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut],
            dependencies=[Depends(rate_limit("read", settings.rate_limit_read_per_min))])
async def history(chat_id: UUID, user: CurrentUser = Depends(require_auth)) -> list[MessageOut]:
    async with db.with_tenant(user.tenant_id) as conn:
        owner = await conn.fetchval("SELECT user_id FROM chat_sessions WHERE chat_id = $1", str(chat_id))
        if owner is None:
            raise ApiError("NOT_FOUND")
        if str(owner) != user.user_id:
            raise ApiError("FORBIDDEN")
        rows = await conn.fetch(
            """SELECT message_id, role, content, created_at FROM chat_messages
                WHERE chat_id = $1 AND role IN ('user', 'assistant')
                ORDER BY created_at ASC LIMIT 200""",
            str(chat_id),
        )
    return [MessageOut(message_id=str(r["message_id"]), role=r["role"],
                       content=r["content"], created_at=r["created_at"]) for r in rows]


@router.post("/messages/{message_id}/feedback", response_model=MessageResponse)
async def feedback(message_id: UUID, body: FeedbackRequest,
                   user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    async with db.with_tenant(user.tenant_id) as conn:
        # Verify the message belongs to the caller (via chat ownership).
        owner = await conn.fetchval(
            """SELECT cs.user_id FROM chat_messages cm
                 JOIN chat_sessions cs ON cm.chat_id = cs.chat_id
                WHERE cm.message_id = $1""",
            str(message_id),
        )
        if owner is None:
            raise ApiError("NOT_FOUND")
        if str(owner) != user.user_id:
            raise ApiError("FORBIDDEN")
        await conn.execute(
            """INSERT INTO ai_response_feedback
                   (message_id, tenant_id, user_id, rating, issue_type, free_text, prompt_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            str(message_id), user.tenant_id, user.user_id, body.rating, body.issue_type, body.free_text, PROMPT_VERSION,
        )
    return MessageResponse(message="Thanks for the feedback.")
