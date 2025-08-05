# Duplicate API Consolidation - Implementation Guide

This document provides specific code changes needed to implement the duplicate API consolidation recommendations from the analysis report.

## Phase 1: Remove Duplicate /me Endpoint

### 1.1 Remove from Auth API

**File:** `app/api/auth.py`

**Remove this endpoint:**
```python
@router.get("/me", response_model=APIResponse[UserResponse])
@handle_api_errors("Failed to get current user information")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> APIResponse[UserResponse]:
    """Get current authenticated user information."""
    log_api_call("get_current_user_info", user_id=str(current_user.id))
    payload = UserResponse.model_validate(current_user)
    return APIResponse[UserResponse](
        success=True,
        message="User information retrieved successfully",
        data=payload,
    )
```

### 1.2 Update Route Registration

**File:** `app/main.py`

No changes needed - the users router already includes the `/me` endpoint.

### 1.3 Update Tests

Create test to verify the auth `/me` endpoint no longer exists:

**File:** `tests/test_api_consolidation.py` (create new file)
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_me_endpoint_removed():
    """Verify /api/v1/auth/me endpoint has been removed."""
    # This should return 404 after consolidation
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 404

def test_users_me_endpoint_works():
    """Verify /api/v1/users/me endpoint still works."""
    # Note: This will need authentication setup in real tests
    # response = client.get("/api/v1/users/me", headers=auth_headers)
    # assert response.status_code == 200
    pass
```

## Phase 2: Consolidate Password Management

### 2.1 Move Password Reset from Auth to Users

**File:** `app/api/users.py`

**Add these new endpoints:**
```python
@router.post("/password-reset", response_model=APIResponse)
@handle_api_errors("Password reset request failed")
async def request_password_reset(
    request: PasswordResetRequest,
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Request password reset for user account."""
    log_api_call("request_password_reset", email=request.email)
    
    # Implementation note: Move logic from auth service to user service
    await user_service.request_password_reset(request.email)
    
    return APIResponse(
        success=True,
        message="Password reset request processed. Check email for instructions.",
    )

@router.post("/password-reset/confirm", response_model=APIResponse)
@handle_api_errors("Password reset confirmation failed")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    user_service: UserService = Depends(get_user_service),
) -> APIResponse:
    """Confirm password reset with token."""
    log_api_call("confirm_password_reset", token=request.token[:8] + "...")
    
    await user_service.confirm_password_reset(request.token, request.new_password)
    
    return APIResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password.",
    )
```

### 2.2 Remove from Auth API

**File:** `app/api/auth.py`

**Remove these endpoints:**
```python
# Remove these functions:
# - request_password_reset()
# - confirm_password_reset()
```

### 2.3 Add Service Methods

**File:** `app/services/user.py`

**Add these methods to UserService class:**
```python
async def request_password_reset(self, email: str) -> None:
    """Request password reset for user."""
    # Move implementation from auth service
    # Check if user exists
    stmt = select(User).where(User.email == email)
    result = await self.db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists for security
        return
    
    # Generate reset token and send email
    # Implementation details...
    pass

async def confirm_password_reset(self, token: str, new_password: str) -> None:
    """Confirm password reset with token."""
    # Move implementation from auth service
    # Validate token, update password
    # Implementation details...
    pass
```

### 2.4 Update Imports

**File:** `shared/schemas/user.py`

**Add imports if not already present:**
```python
from shared.schemas.auth import PasswordResetRequest, PasswordResetConfirm
```

## Phase 3: Add Deprecation Warnings (Transition Period)

### 3.1 Deprecated Auth Endpoints

**File:** `app/api/auth.py`

**Add deprecation warnings to removed endpoints:**
```python
from fastapi import status
from warnings import warn

@router.get("/me", response_model=APIResponse[UserResponse], deprecated=True)
@handle_api_errors("Failed to get current user information")
async def get_current_user_info_deprecated(
    current_user: Annotated[User, Depends(get_current_user)],
) -> APIResponse[UserResponse]:
    """
    Get current authenticated user information.
    
    **DEPRECATED**: Use /api/v1/users/me instead. This endpoint will be removed in v2.0.
    """
    warn("GET /api/v1/auth/me is deprecated. Use GET /api/v1/users/me instead.", 
         DeprecationWarning, stacklevel=2)
    
    log_api_call("get_current_user_info_deprecated", user_id=str(current_user.id))
    payload = UserResponse.model_validate(current_user)
    return APIResponse[UserResponse](
        success=True,
        message="User information retrieved successfully (deprecated endpoint)",
        data=payload,
    )
```

### 3.2 Add Deprecation Headers

**File:** `app/middleware/deprecation.py` (create new file)
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add deprecation warnings to response headers."""
    
    DEPRECATED_ENDPOINTS = {
        "/api/v1/auth/me": {
            "message": "Use /api/v1/users/me instead",
            "sunset": "2024-12-31",  # Removal date
            "replacement": "/api/v1/users/me"
        }
    }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        path = request.url.path
        if path in self.DEPRECATED_ENDPOINTS:
            deprecation_info = self.DEPRECATED_ENDPOINTS[path]
            response.headers["Deprecated"] = "true"
            response.headers["Sunset"] = deprecation_info["sunset"]
            response.headers["Link"] = f'<{deprecation_info["replacement"]}>; rel="successor-version"'
            response.headers["Warning"] = f'299 - "Deprecated API: {deprecation_info["message"]}"'
        
        return response
```

**File:** `app/main.py`

**Add deprecation middleware:**
```python
from .middleware.deprecation import DeprecationMiddleware

# Add after other middleware
app.add_middleware(DeprecationMiddleware)
```

## Phase 4: Update Documentation

### 4.1 OpenAPI Schema Updates

**File:** `app/main.py`

**Update OpenAPI schema to mark deprecated endpoints:**
```python
def custom_openapi():
    """Generate custom OpenAPI schema with deprecation markers."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        routes=app.routes,
    )

    # Mark deprecated endpoints
    if "paths" in openapi_schema:
        deprecated_paths = {
            "/api/v1/auth/me": {
                "get": {
                    "deprecated": True,
                    "description": "DEPRECATED: Use /api/v1/users/me instead"
                }
            }
        }
        
        for path, methods in deprecated_paths.items():
            if path in openapi_schema["paths"]:
                for method, updates in methods.items():
                    if method in openapi_schema["paths"][path]:
                        openapi_schema["paths"][path][method].update(updates)

    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

### 4.2 Update CLI Documentation

**File:** `cli/manage.py`

**Add migration help command:**
```python
@app.command()
async def api_migration_info():
    """Show information about API endpoint changes and migrations."""
    console = Console()
    
    console.print("🔄 API Endpoint Migration Information", style="bold blue")
    console.print()
    
    console.print("Deprecated Endpoints:", style="bold red")
    console.print("- GET /api/v1/auth/me → Use GET /api/v1/users/me instead")
    console.print("- POST /api/v1/auth/password-reset → Use POST /api/v1/users/password-reset instead")
    console.print()
    
    console.print("Migration Timeline:", style="bold yellow")
    console.print("- Phase 1: Deprecation warnings added")
    console.print("- Phase 2: 6-month transition period") 
    console.print("- Phase 3: Old endpoints removed in v2.0")
```

## Phase 5: Update Client SDK

### 5.1 Client Library Updates

**File:** `client/ai_chatbot_sdk.py`

**Update client methods:**
```python
class AIChatbotSDK:
    """AI Chatbot Platform SDK with updated endpoints."""
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user profile information."""
        # Updated to use consolidated endpoint
        response = await self._make_request("GET", "/api/v1/users/me")
        return response
    
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset."""
        # Updated to use consolidated endpoint
        response = await self._make_request(
            "POST", 
            "/api/v1/users/password-reset",
            json={"email": email}
        )
        return response
```

## Testing Strategy

### 5.1 Integration Tests

**File:** `tests/test_api_consolidation_integration.py`
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIConsolidation:
    """Test API endpoint consolidation."""
    
    def test_me_endpoint_consolidation(self):
        """Test that /me endpoints are properly consolidated."""
        # Test that users/me works
        # Note: Add proper auth setup
        pass
    
    def test_password_reset_consolidation(self):
        """Test that password reset is properly consolidated."""
        # Test password reset endpoints
        pass
    
    def test_deprecated_endpoints_warnings(self):
        """Test that deprecated endpoints show proper warnings."""
        # Test deprecation headers
        pass
```

### 5.2 Backward Compatibility Tests

**File:** `tests/test_backward_compatibility.py`
```python
def test_deprecated_endpoints_still_work():
    """Ensure deprecated endpoints still function during transition."""
    # Test that old endpoints work but show deprecation warnings
    pass

def test_deprecation_headers():
    """Test that deprecation headers are properly set."""
    # Test HTTP headers for deprecated endpoints
    pass
```

## Rollback Plan

If issues arise during implementation, here's the rollback strategy:

### Immediate Rollback
1. Re-enable removed endpoints in auth API
2. Comment out new endpoints in users API  
3. Remove deprecation middleware
4. Deploy previous version

### Gradual Rollback
1. Extend deprecation period
2. Keep both old and new endpoints active
3. Monitor usage metrics
4. Gradually migrate clients

## Monitoring and Metrics

### Track Migration Progress
- Monitor usage of deprecated endpoints
- Track 404 errors on removed endpoints
- Monitor client migration status
- Set up alerts for increased error rates

### Success Metrics
- Reduction in duplicate endpoint calls
- Improved API response consistency
- Reduced support requests about endpoint confusion
- Successful client migrations

## Communication Plan

### Developer Communication
1. **Announcement**: Send migration notice to all developers
2. **Documentation**: Update all API documentation
3. **Timeline**: Provide clear migration timeline
4. **Support**: Offer migration assistance

### Client Updates
1. **Email notification** to API users
2. **Slack/Discord announcements** 
3. **Documentation updates**
4. **Migration guides** and examples