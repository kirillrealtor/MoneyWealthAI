"""AES-256-GCM token encryption: roundtrip, AAD binding, tamper detection."""
from __future__ import annotations

import pytest

from app.encryption import EncryptionError, decrypt, encrypt, generate_key_b64


def test_roundtrip() -> None:
    blob = encrypt("access-sandbox-secret", aad="user-123")
    assert isinstance(blob, bytes)
    assert b"access-sandbox-secret" not in blob  # not stored in plaintext
    assert decrypt(blob, aad="user-123") == "access-sandbox-secret"


def test_wrong_aad_fails() -> None:
    blob = encrypt("token", aad="user-A")
    with pytest.raises(EncryptionError):
        decrypt(blob, aad="user-B")  # can't transplant a token to another user


def test_tampered_ciphertext_fails() -> None:
    blob = bytearray(encrypt("token", aad="u"))
    blob[-1] ^= 0x01  # flip a bit in the tag/ciphertext
    with pytest.raises(EncryptionError):
        decrypt(bytes(blob), aad="u")


def test_truncated_blob_fails() -> None:
    with pytest.raises(EncryptionError):
        decrypt(b"\x01\x02", aad="u")


def test_generated_key_is_32_bytes_b64() -> None:
    import base64

    assert len(base64.b64decode(generate_key_b64())) == 32
