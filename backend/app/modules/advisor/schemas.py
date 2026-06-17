"""Pydantic models for the advisor API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    chat_id: str | None = None
    module: str | None = Field(default=None, max_length=50)


class ChatResponse(BaseModel):
    chat_id: str
    message_id: str
    response: str
    tool_calls_made: list[str]
    provider: str
    tokens_used: int


class MessageOut(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: datetime


class ChatSummary(BaseModel):
    chat_id: str
    started_at: datetime
    preview: str | None


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=-1, le=1)
    issue_type: str | None = Field(default=None, max_length=50)
    free_text: str | None = Field(default=None, max_length=2000)


class MessageResponse(BaseModel):
    message: str
