import re

from app.crypto import hash_password, random_token, sha256, verify_password


def test_sha256_deterministic_and_hex() -> None:
    assert sha256("hello") == sha256("hello")
    assert re.fullmatch(r"[0-9a-f]{64}", sha256("hello"))


def test_random_token_unique_and_urlsafe() -> None:
    a, b = random_token(), random_token()
    assert a != b
    assert re.fullmatch(r"[A-Za-z0-9_\-]+", a)


def test_password_hash_and_verify() -> None:
    h = hash_password("SecurePass123!")
    assert "SecurePass123!" not in h
    assert verify_password("SecurePass123!", h) is True
    assert verify_password("wrong", h) is False
