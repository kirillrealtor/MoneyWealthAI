import jwt
import pytest

from app.config import settings
from app.errors import ApiError
from app.modules.auth.tokens import sign_access_token, verify_access_token


def test_access_token_roundtrip() -> None:
    token = sign_access_token("user-1", "tenant-1", "plus")
    claims = verify_access_token(token)
    assert claims["sub"] == "user-1"
    assert claims["tenant_id"] == "tenant-1"
    assert claims["tier"] == "plus"


def test_access_token_rejects_tampered_secret() -> None:
    token = sign_access_token("user-1", "tenant-1", "free")
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, settings.jwt_access_secret + "x", algorithms=["HS256"])


def test_api_error_has_known_code() -> None:
    err = ApiError("UNAUTHORIZED")
    assert err.code == "UNAUTHORIZED"
    assert "token" in err.message.lower()
