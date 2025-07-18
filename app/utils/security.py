"""
Security utilities for password hashing and validation.

This module provides functions for secure password handling,
token generation, and other security-related operations.

Generated on: 2025-07-14 03:10:09 UTC
Current User: lllucius
"""

import secrets
import string

import bcrypt


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        bool: True if password matches hash
    """
    plain_byte_enc = plain_password.encode("utf-8")
    hashed_byte_enc = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password=plain_byte_enc, hashed_password=hashed_byte_enc)


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
