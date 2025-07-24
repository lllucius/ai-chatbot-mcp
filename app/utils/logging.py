"""
DEPRECATED: This module has been replaced by app.core.logging.

This module is kept for compatibility but should not be used in new code.
All functionality has been moved to app.core.logging which provides
a unified, more advanced logging service.

Please update imports to use:
    from app.core.logging import setup_logging, get_logger, etc.
"""

# For backward compatibility, re-export from the new module
from ..core.logging import (
    setup_logging,
    get_logger,
    get_api_logger,
    get_service_logger,
    get_component_logger,
    StructuredLogger,
)
