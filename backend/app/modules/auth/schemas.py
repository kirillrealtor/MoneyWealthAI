"""Pydantic request/response models for the auth API."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject unexpected fields

    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str | None = Field(default=None, max_length=255)
    # Cloudflare Turnstile token (required when captcha is enabled).
    captcha_token: str | None = None


class SignupResponse(BaseModel):
    user_id: str
    message: str = "Account created. Check your email to verify."


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=200)
    # Required only as a step-up after repeated login failures.
    captcha_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    user_id: str


class MessageResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None
    tier: str
    advisor_persona: str
    is_verified: bool
    onboarding_step: int
