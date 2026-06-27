"""Auth mode guards — password vs passwordless magic-link."""
from __future__ import annotations

from app.config import settings
from app.errors import ApiError


def require_password_mode() -> None:
    if settings.auth_mode != "password":
        raise ApiError("NOT_FOUND")


def require_magic_link_mode() -> None:
    if settings.auth_mode != "magic_link":
        raise ApiError("NOT_FOUND")
