"""
Authentication manager for the API-based CLI.

This module handles authentication token management, login/logout operations,
and credential storage for the CLI application.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from .base import APIClient, APIError


class AuthManager:
    """Manages authentication for API CLI."""
    
    def __init__(self):
        self.token_file = Path.home() / ".ai-chatbot-cli" / "token"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._token: Optional[str] = None
        self._load_token()
    
    def _load_token(self):
        """Load token from file."""
        try:
            if self.token_file.exists():
                with open(self.token_file, "r") as f:
                    data = json.load(f)
                    self._token = data.get("access_token")
        except Exception:
            # If token file is corrupted, ignore and start fresh
            pass
    
    def save_token(self, token: str):
        """Save token to file."""
        try:
            data = {"access_token": token}
            with open(self.token_file, "w") as f:
                json.dump(data, f)
            
            # Set restrictive permissions
            self.token_file.chmod(0o600)
            self._token = token
        except Exception as e:
            raise APIError(f"Failed to save authentication token: {str(e)}")
    
    def get_token(self) -> Optional[str]:
        """Get current token."""
        return self._token
    
    def has_token(self) -> bool:
        """Check if token is available."""
        return self._token is not None
    
    def clear_token(self):
        """Clear stored token."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
            self._token = None
        except Exception as e:
            raise APIError(f"Failed to clear authentication token: {str(e)}")
    
    async def login(self, username: str, password: str) -> Dict[str, str]:
        """Login and get authentication token."""
        client = APIClient()
        
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            # Use the SDK's auth method
            sdk = client.get_sdk()
            response = await sdk.login(username, password)
            return response
        except Exception as e:
            # Parse and re-raise as APIError
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise APIError("Invalid username or password")
            elif "422" in error_msg or "validation" in error_msg.lower():
                raise APIError("Invalid login request format")
            else:
                raise APIError(f"Login failed: {error_msg}")
    
    async def logout(self):
        """Logout from API."""
        if not self.has_token():
            return
        
        client = APIClient()
        client.set_token(self._token)
        
        try:
            # Use SDK method  
            sdk = client.get_sdk()
            sdk.logout()  # Sync method in SDK
        except Exception:
            # Continue with local logout even if API call fails
            pass
        finally:
            self.clear_token()
    
    async def get_current_user(self) -> Dict[str, str]:
        """Get current user information."""
        if not self.has_token():
            raise APIError("Not authenticated")
        
        client = APIClient()
        client.set_token(self._token)
        
        try:
            # Use SDK method
            sdk = client.get_sdk()
            response = sdk.get_current_user()  # Sync method in SDK
            if not response:
                raise APIError("Failed to get user information")
            return response
        except Exception as e:
            # Token might be expired, clear it
            self.clear_token()
            raise APIError("Authentication token is invalid or expired")
    
    async def refresh_token(self) -> bool:
        """Refresh authentication token."""
        if not self.has_token():
            return False
        
        client = APIClient()
        client.set_token(self._token)
        
        try:
            # Use SDK method if available, otherwise make direct API call
            sdk = client.get_sdk()
            
            # Since SDK may not have a refresh method, fall back to API call
            response = await client.post("/api/v1/auth/refresh")
            if response and "access_token" in response:
                self.save_token(response["access_token"])
                return True
        except Exception:
            # Refresh failed, clear token
            self.clear_token()
        
        return False


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager