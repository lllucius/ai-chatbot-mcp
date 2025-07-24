"Utility functions for versioning operations."

from enum import Enum
from typing import Dict, List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel


class APIVersion(str, Enum):
    "APIVersion class for specialized functionality."

    V1 = "v1"
    V2 = "v2"


class APIVersionInfo(BaseModel):
    "APIVersionInfo class for specialized functionality."

    version: APIVersion
    description: str
    deprecated: bool = False
    sunset_date: Optional[str] = None
    supported_until: Optional[str] = None


class VersionedAPIRouter:
    "VersionedAPI API router for endpoint handling."

    def __init__(self):
        "Initialize class instance."
        self.routers: Dict[(APIVersion, APIRouter)] = {}
        self.version_info: Dict[(APIVersion, APIVersionInfo)] = {
            APIVersion.V1: APIVersionInfo(
                version=APIVersion.V1,
                description="Initial API version with core functionality",
                deprecated=False,
            )
        }

    def add_router(self, version: APIVersion, router: APIRouter) -> None:
        "Add Router operation."
        self.routers[version] = router

    def get_router(self, version: APIVersion) -> Optional[APIRouter]:
        "Get router data."
        return self.routers.get(version)

    def get_version_info(self, version: APIVersion) -> Optional[APIVersionInfo]:
        "Get version info data."
        return self.version_info.get(version)

    def list_versions(self) -> List[APIVersionInfo]:
        "List versions entries."
        return list(self.version_info.values())


def get_api_version_from_request(request: Request) -> APIVersion:
    "Get api version from request data."
    path_parts = request.url.path.split("/")
    for i, part in enumerate(path_parts):
        if part.startswith("v") and part[1:].isdigit():
            try:
                return APIVersion(part)
            except ValueError:
                pass
    accept_header = request.headers.get("accept", "")
    if "version=" in accept_header:
        version_part = accept_header.split("version=")[1].split(";")[0].strip()
        try:
            return APIVersion(f"v{version_part}")
        except ValueError:
            pass
    version_header = request.headers.get("X-API-Version", "")
    if version_header:
        try:
            return APIVersion(version_header.lower())
        except ValueError:
            pass
    return APIVersion.V1


def add_version_headers(response, version: APIVersion) -> None:
    "Add Version Headers operation."
    response.headers["X-API-Version"] = version.value
    response.headers["X-API-Supported-Versions"] = "v1"
    version_info = versioned_router.get_version_info(version)
    if version_info and version_info.deprecated:
        response.headers["Warning"] = (
            f'299 - "API version {version.value} is deprecated"'
        )
        if version_info.sunset_date:
            response.headers["Sunset"] = version_info.sunset_date


versioned_router = VersionedAPIRouter()


class APIVersioningMiddleware:
    "APIVersioningMiddleware class for specialized functionality."

    def __init__(self, app):
        "Initialize class instance."
        self.app = app

    async def __call__(self, scope, receive, send):
        "Call   operation."
        if scope["type"] == "http":
            request = Request(scope, receive)
            version = get_api_version_from_request(request)
            if not hasattr(request, "state"):
                request.state = type("State", (), {})()
            request.state.api_version = version
        (await self.app(scope, receive, send))


def version(min_version: APIVersion, max_version: Optional[APIVersion] = None):
    "Version operation."

    def decorator(func):
        "Decorator operation."
        func._api_min_version = min_version
        func._api_max_version = max_version
        return func

    return decorator


class APIMigration:
    "APIMigration class for specialized functionality."

    @staticmethod
    def migrate_v1_to_v2_user(v1_user: Dict) -> Dict:
        "Migrate V1 To V2 User operation."
        v2_user = v1_user.copy()
        v2_user.setdefault("profile", {})
        v2_user.setdefault("preferences", {})
        if "full_name" in v2_user:
            name_parts = v2_user["full_name"].split(" ", 1)
            v2_user["profile"]["first_name"] = name_parts[0]
            v2_user["profile"]["last_name"] = (
                name_parts[1] if (len(name_parts) > 1) else ""
            )
        return v2_user

    @staticmethod
    def migrate_v2_to_v1_user(v2_user: Dict) -> Dict:
        "Migrate V2 To V1 User operation."
        v1_user = v2_user.copy()
        v1_user.pop("profile", None)
        v1_user.pop("preferences", None)
        if "profile" in v2_user:
            profile = v2_user["profile"]
            first_name = profile.get("first_name", "")
            last_name = profile.get("last_name", "")
            v1_user["full_name"] = f"{first_name} {last_name}".strip()
        return v1_user


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
}


def get_version_compatibility(version: APIVersion) -> Dict:
    "Get version compatibility data."
    return VERSION_COMPATIBILITY.get(version, {})


def is_feature_supported(version: APIVersion, feature: str) -> bool:
    "Check if feature supported condition is met."
    compatibility = get_version_compatibility(version)
    supported_features = compatibility.get("supported_features", [])
    return feature in supported_features
