"""
API versioning strategy and utilities.

This module provides a comprehensive API versioning strategy to ensure
backward compatibility and smooth transitions between API versions.
"""

# Standard library imports
from enum import Enum
from typing import Dict, List, Optional

# Third-party imports
from fastapi import APIRouter, Request
from pydantic import BaseModel


class APIVersion(str, Enum):
    """Supported API versions."""

    V1 = "v1"
    V2 = "v2"  # Future version


class APIVersionInfo(BaseModel):
    """API version information."""

    version: APIVersion
    description: str
    deprecated: bool = False
    sunset_date: Optional[str] = None
    supported_until: Optional[str] = None


class VersionedAPIRouter:
    """Router with version management capabilities."""

    def __init__(self):
        self.routers: Dict[APIVersion, APIRouter] = {}
        self.version_info: Dict[APIVersion, APIVersionInfo] = {
            APIVersion.V1: APIVersionInfo(
                version=APIVersion.V1,
                description="Initial API version with core functionality",
                deprecated=False,
            )
        }

    def add_router(self, version: APIVersion, router: APIRouter) -> None:
        """Add a router for a specific API version."""
        self.routers[version] = router

    def get_router(self, version: APIVersion) -> Optional[APIRouter]:
        """Get router for a specific API version."""
        return self.routers.get(version)

    def get_version_info(self, version: APIVersion) -> Optional[APIVersionInfo]:
        """Get version information."""
        return self.version_info.get(version)

    def list_versions(self) -> List[APIVersionInfo]:
        """List all available API versions."""
        return list(self.version_info.values())


def get_api_version_from_request(request: Request) -> APIVersion:
    """Extract API version from request."""
    # Method 1: From URL path (e.g., /api/v1/...)
    path_parts = request.url.path.split("/")
    for _i, part in enumerate(path_parts):
        if part.startswith("v") and part[1:].isdigit():
            try:
                return APIVersion(part)
            except ValueError:
                pass

    # Method 2: From Accept header (e.g., application/vnd.api+json;version=1)
    accept_header = request.headers.get("accept", "")
    if "version=" in accept_header:
        version_part = accept_header.split("version=")[1].split(";")[0].strip()
        try:
            return APIVersion(f"v{version_part}")
        except ValueError:
            pass

    # Method 3: From custom header
    version_header = request.headers.get("X-API-Version", "")
    if version_header:
        try:
            return APIVersion(version_header.lower())
        except ValueError:
            pass

    # Default to v1
    return APIVersion.V1


def add_version_headers(response, version: APIVersion) -> None:
    """Add version information to response headers."""
    response.headers["X-API-Version"] = version.value
    response.headers["X-API-Supported-Versions"] = (
        "v1"  # Update as new versions are added
    )

    # Add deprecation warning if applicable
    version_info = versioned_router.get_version_info(version)
    if version_info and version_info.deprecated:
        response.headers["Warning"] = (
            f'299 - "API version {version.value} is deprecated"'
        )
        if version_info.sunset_date:
            response.headers["Sunset"] = version_info.sunset_date


# Global versioned router instance
versioned_router = VersionedAPIRouter()


class APIVersioningMiddleware:
    """Middleware for API versioning."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            version = get_api_version_from_request(request)

            # Store version in request state
            if not hasattr(request, "state"):
                request.state = type("State", (), {})()
            request.state.api_version = version

        await self.app(scope, receive, send)


# Decorator for version-specific endpoints
def version(min_version: APIVersion, max_version: Optional[APIVersion] = None):
    """
    Decorator to specify version requirements for endpoints.

    Args:
        min_version: Minimum API version required
        max_version: Maximum API version supported (optional)
    """

    def decorator(func):
        """
        Decorator function that adds version metadata to the wrapped function.

        Args:
            func: Function to decorate with version requirements

        Returns:
            function: The same function with version metadata attached
        """
        func._api_min_version = min_version
        func._api_max_version = max_version
        return func

    return decorator


# Migration utilities
class APIMigration:
    """Utilities for API data migration between versions."""

    @staticmethod
    def migrate_v1_to_v2_user(v1_user: Dict) -> Dict:
        """Migrate user data from v1 to v2 format."""
        # Example migration logic
        v2_user = v1_user.copy()

        # Add new fields with defaults
        v2_user.setdefault("profile", {})
        v2_user.setdefault("preferences", {})

        # Transform existing fields if needed
        if "full_name" in v2_user:
            name_parts = v2_user["full_name"].split(" ", 1)
            v2_user["profile"]["first_name"] = name_parts[0]
            v2_user["profile"]["last_name"] = (
                name_parts[1] if len(name_parts) > 1 else ""
            )

        return v2_user

    @staticmethod
    def migrate_v2_to_v1_user(v2_user: Dict) -> Dict:
        """Migrate user data from v2 to v1 format."""
        v1_user = v2_user.copy()

        # Remove v2-specific fields
        v1_user.pop("profile", None)
        v1_user.pop("preferences", None)

        # Reconstruct v1 fields
        if "profile" in v2_user:
            profile = v2_user["profile"]
            first_name = profile.get("first_name", "")
            last_name = profile.get("last_name", "")
            v1_user["full_name"] = f"{first_name} {last_name}".strip()

        return v1_user


# Version compatibility matrix
VERSION_COMPATIBILITY = {
    APIVersion.V1: {
        "supported_features": [
            "user_management",
            "authentication",
            "document_upload",
            "basic_search",
            "conversations",
        ],
        "deprecated_features": [],
        "breaking_changes": [],
    }
    # V2 will be added when implemented
}


def get_version_compatibility(version: APIVersion) -> Dict:
    """Get compatibility information for a specific API version."""
    return VERSION_COMPATIBILITY.get(version, {})


def is_feature_supported(version: APIVersion, feature: str) -> bool:
    """Check if a feature is supported in a specific API version."""
    compatibility = get_version_compatibility(version)
    supported_features = compatibility.get("supported_features", [])
    return feature in supported_features
