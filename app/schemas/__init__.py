"""
Schema definitions have been moved to shared.schemas package.

All schema definitions are now in the shared.schemas package to eliminate
duplication between API and SDK code. Import schemas directly from shared.schemas
instead of from app.schemas.

Example:
    # Old import (deprecated)
    from app.schemas import UserResponse

    # New import (preferred)
    from shared.schemas import UserResponse

This change eliminates code duplication and ensures consistency between
API server schemas and client SDK schemas.
"""

# This module is deprecated. Import schemas directly from shared.schemas instead.
import warnings

warnings.warn(
    "app.schemas is deprecated. Import schemas directly from shared.schemas instead.",
    DeprecationWarning,
    stacklevel=2,
)
