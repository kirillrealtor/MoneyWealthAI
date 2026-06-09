"""Authenticated encryption for secrets at rest (Plaid access tokens).

AES-256-GCM with:
  * a versioned key (supports rotation without rewriting old ciphertext blindly),
  * a random 96-bit nonce per message,
  * Additional Authenticated Data (AAD) binding the ciphertext to its context
    (e.g. the owning user_id), so a token blob can't be transplanted to another
    row.

Stored blob layout (BYTEA):  [version:1][nonce:12][ciphertext+tag:N]

Production note: the key comes from AWS KMS / Secrets Manager (envelope
encryption — KMS-wrapped data key). Locally it's a base64 32-byte key in env.
Plaintext tokens are NEVER logged or returned to clients.
"""
from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

_NONCE_LEN = 12


class EncryptionError(RuntimeError):
    pass


def _load_key() -> tuple[int, bytes]:
    if not settings.plaid_enc_key:
        raise EncryptionError("PLAID_ENC_KEY is not configured")
    try:
        key = base64.b64decode(settings.plaid_enc_key)
    except Exception as err:  # noqa: BLE001
        raise EncryptionError("PLAID_ENC_KEY is not valid base64") from err
    if len(key) != 32:
        raise EncryptionError("PLAID_ENC_KEY must decode to exactly 32 bytes (AES-256)")
    return settings.plaid_enc_key_version, key


def encrypt(plaintext: str, *, aad: str) -> bytes:
    """Encrypt a secret string, binding it to `aad` (e.g. the user_id)."""
    version, key = _load_key()
    nonce = os.urandom(_NONCE_LEN)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), aad.encode("utf-8"))
    return bytes([version]) + nonce + ct


def decrypt(blob: bytes, *, aad: str) -> str:
    """Decrypt a blob produced by encrypt(). Raises EncryptionError on tamper,
    wrong AAD, or key mismatch."""
    if len(blob) < 1 + _NONCE_LEN + 16:
        raise EncryptionError("ciphertext blob too short")
    version = blob[0]
    expected_version, key = _load_key()
    if version != expected_version:
        # In a rotation scenario you'd look up the historical key by version.
        raise EncryptionError(f"unknown key version {version}")
    nonce = blob[1 : 1 + _NONCE_LEN]
    ct = blob[1 + _NONCE_LEN :]
    try:
        pt = AESGCM(key).decrypt(nonce, ct, aad.encode("utf-8"))
    except InvalidTag as err:
        raise EncryptionError("authentication failed (tampered ciphertext or wrong context)") from err
    return pt.decode("utf-8")


def generate_key_b64() -> str:
    """Helper to mint a new base64 AES-256 key (used in setup scripts)."""
    return base64.b64encode(os.urandom(32)).decode("ascii")
