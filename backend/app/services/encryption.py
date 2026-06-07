"""
Encryption service — Fernet symmetric encryption for secrets at rest.

All provider API keys and target config auth values are encrypted before
database storage and decrypted only at point-of-use in Celery workers.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY environment variable is not set. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plain_text: str) -> str:
    """Encrypt a plaintext string, return base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str:
    """Decrypt a Fernet-encrypted string back to plaintext."""
    f = _get_fernet()
    try:
        return f.decrypt(cipher_text.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt value — invalid key or corrupted data") from exc


def mask_secret(value: str, visible_prefix: int = 3, visible_suffix: int = 4) -> str:
    """Return a masked version of a secret string, e.g. 'sk-...7xQ2'."""
    if len(value) <= visible_prefix + visible_suffix + 3:
        return "***"
    return f"{value[:visible_prefix]}...{value[-visible_suffix:]}"
