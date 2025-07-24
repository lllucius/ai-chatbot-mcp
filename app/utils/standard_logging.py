"""
DEPRECATED: This module has been replaced by app.core.logging.

This module provided advanced logging functionality that has been
consolidated into the unified logging service at app.core.logging.

Please update imports to use:
    from app.core.logging import setup_logging, get_logger, etc.

This file is kept for reference but should not be used in new code.
The new unified logging service provides all the same functionality
with better organization and additional features.
"""

# For backward compatibility, re-export from the new module
from ..core.logging import (
    StructuredFormatter,
    DevelopmentFormatter,
    ContextFilter,
    PerformanceLogger,
    OperationTimer,
    setup_logging,
    get_logger,
    get_performance_logger,
    set_correlation_id,
    set_user_context,
    set_operation_context,
)
