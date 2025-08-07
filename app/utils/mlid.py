"""Machine Learning ID (MLID) utilities for unique entity identification.

This module provides MLID generation and validation for the AI Chatbot Platform.
MLIDs are shorter, more readable alternatives to UUIDs that are specifically
designed for ML/AI applications.

MLID Format:
    - Prefix: 'ml_'
    - Identifier: 14 character alphanumeric string
    - Total length: 17 characters
    - Character set: 'abcdefghijkmnpqrstuvwxyz23456789' (32 chars, excluding 0,O,1,l)
    - Example: ml_a1b2c3d4e5f6g7

Features:
    - URL-safe and database-friendly
    - Human-readable with meaningful prefix
    - High collision resistance (32^14 = ~1.2e21 possible values)
    - Shorter than UUIDs (17 vs 36 characters)
    - Globally unique within the platform

Security:
    - Cryptographically secure random generation
    - Non-sequential to prevent enumeration attacks
    - Sufficient entropy for global uniqueness
"""

import re
import secrets
from typing import Any

# Character set for MLID generation (32 characters)
# Excludes confusing characters: 0 (zero), O (oh), 1 (one), l (el)
MLID_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"
MLID_PREFIX = "ml_"
MLID_ID_LENGTH = 14
MLID_TOTAL_LENGTH = len(MLID_PREFIX) + MLID_ID_LENGTH  # 17 characters

# Regex pattern for MLID validation
MLID_PATTERN = re.compile(rf"^{re.escape(MLID_PREFIX)}[{re.escape(MLID_ALPHABET)}]{{{MLID_ID_LENGTH}}}$")


def generate_mlid() -> str:
    """Generate a new MLID with cryptographic randomness.
    
    Creates a new Machine Learning ID using cryptographically secure
    random generation. The MLID consists of the 'ml_' prefix followed
    by 14 random characters from the safe alphabet.
    
    Returns:
        str: A new MLID in the format 'ml_xxxxxxxxxxxxxx'
        
    Example:
        >>> mlid = generate_mlid()
        >>> print(mlid)
        ml_a2b3c4d5e6f7g8
        >>> len(mlid)
        17
    """
    # Generate 14 random characters from the alphabet
    random_chars = ''.join(secrets.choice(MLID_ALPHABET) for _ in range(MLID_ID_LENGTH))
    
    return f"{MLID_PREFIX}{random_chars}"


def is_valid_mlid(value: Any) -> bool:
    """Validate if a value is a properly formatted MLID.
    
    Checks if the provided value is a string that matches the MLID
    format requirements: 'ml_' prefix followed by exactly 14 characters
    from the allowed alphabet.
    
    Args:
        value: The value to validate (can be any type)
        
    Returns:
        bool: True if the value is a valid MLID, False otherwise
        
    Example:
        >>> is_valid_mlid("ml_a2b3c4d5e6f7g8")
        True
        >>> is_valid_mlid("invalid")
        False
        >>> is_valid_mlid(None)
        False
    """
    if not isinstance(value, str):
        return False
        
    return bool(MLID_PATTERN.match(value))


def validate_mlid(mlid: str) -> str:
    """Validate and return a MLID, raising an exception if invalid.
    
    Validates that the provided string is a properly formatted MLID
    and returns it if valid. Raises ValueError if the MLID is invalid.
    
    Args:
        mlid: The MLID string to validate
        
    Returns:
        str: The validated MLID string
        
    Raises:
        ValueError: If the MLID is invalid or malformed
        
    Example:
        >>> validate_mlid("ml_a2b3c4d5e6f7g8")
        'ml_a2b3c4d5e6f7g8'
        >>> validate_mlid("invalid")
        Traceback (most recent call last):
        ...
        ValueError: Invalid MLID format: invalid
    """
    if not is_valid_mlid(mlid):
        raise ValueError(f"Invalid MLID format: {mlid}")
    
    return mlid


def mlid_from_any(value: Any) -> str:
    """Convert various input types to a valid MLID.
    
    Attempts to convert different input types to a valid MLID:
    - If already a valid MLID string, returns as-is
    - If a string that's not a valid MLID, raises ValueError
    - If None or other types, raises ValueError
    
    Args:
        value: The value to convert to MLID
        
    Returns:
        str: A valid MLID string
        
    Raises:
        ValueError: If the value cannot be converted to a valid MLID
        
    Example:
        >>> mlid_from_any("ml_a2b3c4d5e6f7g8")
        'ml_a2b3c4d5e6f7g8'
        >>> mlid_from_any(None)
        Traceback (most recent call last):
        ...
        ValueError: Cannot convert None to MLID
    """
    if value is None:
        raise ValueError("Cannot convert None to MLID")
    
    if isinstance(value, str):
        return validate_mlid(value)
    
    raise ValueError(f"Cannot convert {type(value).__name__} to MLID: {value}")


def get_mlid_info(mlid: str) -> dict[str, Any]:
    """Get information about a MLID.
    
    Provides detailed information about a MLID including its components,
    validation status, and metadata for debugging and analysis.
    
    Args:
        mlid: The MLID to analyze
        
    Returns:
        dict: Information about the MLID including:
            - is_valid: Whether the MLID is valid
            - prefix: The prefix part ('ml_')
            - identifier: The random identifier part
            - length: Total length of the MLID
            - alphabet_used: Character set used for generation
            
    Example:
        >>> info = get_mlid_info("ml_a2b3c4d5e6f7g8")
        >>> info['is_valid']
        True
        >>> info['identifier']
        'a2b3c4d5e6f7g8'
    """
    info = {
        "is_valid": is_valid_mlid(mlid),
        "prefix": mlid[:len(MLID_PREFIX)] if isinstance(mlid, str) and len(mlid) >= len(MLID_PREFIX) else None,
        "identifier": mlid[len(MLID_PREFIX):] if isinstance(mlid, str) and len(mlid) > len(MLID_PREFIX) else None,
        "length": len(mlid) if isinstance(mlid, str) else 0,
        "alphabet_used": MLID_ALPHABET,
        "expected_length": MLID_TOTAL_LENGTH,
    }
    
    return info


# Export commonly used functions and constants
__all__ = [
    "generate_mlid",
    "is_valid_mlid", 
    "validate_mlid",
    "mlid_from_any",
    "get_mlid_info",
    "MLID_PREFIX",
    "MLID_TOTAL_LENGTH",
    "MLID_PATTERN",
]