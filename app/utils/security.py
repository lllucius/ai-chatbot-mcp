"""
Security utilities for password hashing and validation.

This module provides functions for secure password handling,
token generation, and other security-related operations.

Generated on: 2025-07-21 03:36:44 UTC
Current User: lllucius
"""

import base64
import hashlib
import secrets
import string

# Scrypt configuration parameters (recommended for secure usage)
SCRYPT_N = 2**14  # CPU/memory cost factor
SCRYPT_R = 8      # Block size
SCRYPT_P = 1      # Parallelization factor
SCRYPT_DKLEN = 64 # Length of derived key

def get_password_hash(password: str) -> str:
    """
    Hash a password using scrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Base64-encoded salt + hash for storage
    """
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password=password.encode('utf-8'),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN
    )
    # Store salt + hash together (salt first, then hash)
    data = base64.b64encode(salt + key).decode('utf-8')
    return data

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its scrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Base64-encoded salt + hash to verify against

    Returns:
        bool: True if password matches hash
    """
    try:
        decoded = base64.b64decode(hashed_password.encode('utf-8'))
        salt = decoded[:16]
        key = decoded[16:]
        new_key = hashlib.scrypt(
            password=plain_password.encode('utf-8'),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            dklen=len(key)
        )
        return secrets.compare_digest(new_key, key)
    except Exception:
        return False

def generate_random_password(length: int = 12) -> str:
    """
    Generate a random password.

    Args:
        length: Length of password to generate

    Returns:
        str: Random password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_secret_key(length: int = 32) -> str:
    """
    Generate a random secret key.

    Args:
        length: Length of secret key in bytes

    Returns:
        str: Random secret key as hex string
    """
    return secrets.token_hex(length)

def generate_token(length: int = 32) -> str:
    """
    Generate a random token.

    Args:
        length: Length of token in bytes

    Returns:
        str: Random token as URL-safe string
    """
    return secrets.token_urlsafe(length)
