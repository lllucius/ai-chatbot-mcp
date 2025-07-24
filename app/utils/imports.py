"Utility functions for imports operations."

from typing import List

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
    "Organize Imports operation."
    standard_imports = []
    third_party_imports = []
    local_imports = []
    for import_line in imports:
        if import_line.strip().startswith("from ") or import_line.strip().startswith(
            "import "
        ):
            if any(((module in import_line) for module in STANDARD_LIBRARY_MODULES)):
                standard_imports.append(import_line)
            elif any(((module in import_line) for module in THIRD_PARTY_MODULES)):
                third_party_imports.append(import_line)
            else:
                local_imports.append(import_line)
    organized = []
    if standard_imports:
        organized.extend(sorted(standard_imports))
        organized.append("")
    if third_party_imports:
        organized.extend(sorted(third_party_imports))
        organized.append("")
    if local_imports:
        organized.extend(sorted(local_imports))
    return organized


def validate_import_order(file_path: str) -> List[str]:
    "Validate import order data."
    violations = []
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        import_section = []
        in_import_section = False
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                in_import_section = True
                import_section.append(((i + 1), line.strip()))
            elif in_import_section and (line.strip() == ""):
                continue
            elif in_import_section and (not line.strip().startswith("#")):
                break
        if import_section:
            current_group = None
            for line_num, import_line in import_section:
                if any(
                    ((module in import_line) for module in STANDARD_LIBRARY_MODULES)
                ):
                    group = "standard"
                elif any(((module in import_line) for module in THIRD_PARTY_MODULES)):
                    group = "third_party"
                else:
                    group = "local"
                if current_group and (group != current_group):
                    if ((current_group == "standard") and (group == "local")) or (
                        (current_group == "third_party") and (group == "standard")
                    ):
                        violations.append(
                            f"Line {line_num}: Import order violation - {group} after {current_group}"
                        )
                current_group = group
    except Exception as e:
        violations.append(f"Error reading file: {e}")
    return violations


COMMON_PATTERNS = {
    "service": "\n# Standard library imports\nfrom typing import Any, Dict, List, Optional\nfrom uuid import UUID\n\n# Third-party imports\nfrom sqlalchemy.ext.asyncio import AsyncSession\n\n# Local imports\nfrom ..core.exceptions import NotFoundError, ValidationError\nfrom .base import BaseService\n",
    "api_endpoint": "\n# Standard library imports\nfrom typing import Any, Dict, Optional\n\n# Third-party imports\nfrom fastapi import APIRouter, Depends, status\nfrom sqlalchemy.ext.asyncio import AsyncSession\n\n# Local imports\nfrom ..database import get_db\nfrom ..utils.api_errors import handle_api_errors, log_api_call\n",
    "model": "\n# Standard library imports\nfrom typing import TYPE_CHECKING, List, Optional\nfrom uuid import UUID\n\n# Third-party imports\nfrom sqlalchemy import Column, String, Boolean\nfrom sqlalchemy.orm import Mapped, mapped_column, relationship\n\n# Local imports\nfrom .base import BaseModelDB\n",
    "schema": "\n# Standard library imports\nfrom typing import List, Optional\nfrom uuid import UUID\n\n# Third-party imports\nfrom pydantic import Field, field_validator\n\n# Local imports\nfrom .base import BaseSchema\n",
}
