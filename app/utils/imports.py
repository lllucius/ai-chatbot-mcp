"""
Import organization standards and utilities for the AI Chatbot Platform.

This module defines import organization standards to ensure consistency
across all Python files in the project. It provides guidelines for
import ordering, grouping, and formatting.

Import Order Standards:
1. Standard library imports (alphabetically sorted)
2. Third-party library imports (alphabetically sorted)
3. Local application imports (alphabetically sorted within groups):
   - Core modules (config, exceptions, etc.)
   - Database and models
   - Services and utilities
   - Schemas and API modules

Example Import Organization:
    # Standard library imports
    import logging
    import uuid
    from datetime import datetime
    from typing import Any, Dict, List, Optional

    # Third-party imports
    from fastapi import APIRouter, Depends
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    # Local imports - Core
    from ..config import settings
    from ..core.exceptions import ValidationError

    # Local imports - Database and models
    from ..database import get_db
    from ..models.user import User

    # Local imports - Services
    from ..services.user import UserService
    from ..core.logging import get_service_logger

    # Local imports - Schemas
    from shared.schemas.user import UserResponse

"""

# Standard library imports
from typing import List

# Import organization rules and validation

STANDARD_LIBRARY_MODULES = {
    "asyncio",
    "datetime",
    "functools",
    "json",
    "logging",
    "math",
    "os",
    "pathlib",
    "sys",
    "time",
    "typing",
    "uuid",
    "warnings",
    "re",
}

THIRD_PARTY_MODULES = {
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "asyncpg",
    "pydantic",
    "jose",
    "passlib",
    "openai",
    "tiktoken",
    "numpy",
    "httpx",
}


def organize_imports(imports: List[str]) -> List[str]:
    """
    Organize imports according to project standards.

    Args:
        imports: List of import statements

    Returns:
        List[str]: Organized import statements
    """
    standard_imports = []
    third_party_imports = []
    local_imports = []

    for import_line in imports:
        if import_line.strip().startswith("from ") or import_line.strip().startswith(
            "import "
        ):
            if any(module in import_line for module in STANDARD_LIBRARY_MODULES):
                standard_imports.append(import_line)
            elif any(module in import_line for module in THIRD_PARTY_MODULES):
                third_party_imports.append(import_line)
            else:
                local_imports.append(import_line)

    # Sort each group
    organized = []
    if standard_imports:
        organized.extend(sorted(standard_imports))
        organized.append("")  # Empty line separator

    if third_party_imports:
        organized.extend(sorted(third_party_imports))
        organized.append("")  # Empty line separator

    if local_imports:
        organized.extend(sorted(local_imports))

    return organized


def validate_import_order(file_path: str) -> List[str]:
    """
    Validate import organization in a Python file.

    Args:
        file_path: Path to Python file to validate

    Returns:
        List[str]: List of violations found
    """
    violations = []

    try:
        with open(file_path) as f:
            lines = f.readlines()

        import_section = []
        in_import_section = False

        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                in_import_section = True
                import_section.append((i + 1, line.strip()))
            elif in_import_section and line.strip() == "":
                continue
            elif in_import_section and not line.strip().startswith("#"):
                # End of import section
                break

        if import_section:
            # Check for proper organization
            current_group = None
            for line_num, import_line in import_section:
                if any(module in import_line for module in STANDARD_LIBRARY_MODULES):
                    group = "standard"
                elif any(module in import_line for module in THIRD_PARTY_MODULES):
                    group = "third_party"
                else:
                    group = "local"

                if current_group and group != current_group:
                    violation_conditions = (
                        current_group == "standard" and group == "local"
                    ) or (current_group == "third_party" and group == "standard")
                    if violation_conditions:
                        violations.append(
                            f"Line {line_num}: Import order violation - {group} after {current_group}"
                        )

                current_group = group

    except Exception as e:
        violations.append(f"Error reading file: {e}")

    return violations


# Common import patterns for code generation
COMMON_PATTERNS = {
    "service": """
# Standard library imports
from typing import Any, Dict, List, Optional


# Third-party imports
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from ..core.exceptions import NotFoundError, ValidationError
from .base import BaseService
""",
    "api_endpoint": """
# Standard library imports
from typing import Any, Dict, Optional

# Third-party imports
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from ..database import get_db
from ..utils.api_errors import handle_api_errors, log_api_call
""",
    "model": """
# Standard library imports
from typing import TYPE_CHECKING, List, Optional


# Third-party imports
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from .base import BaseModelDB
""",
    "schema": """
# Standard library imports
from typing import List, Optional


# Third-party imports
from pydantic import Field, field_validator

# Local imports
from .base import BaseSchema
""",
}
