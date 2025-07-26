#!/usr/bin/env python3
"""
Integration tests for the refactored API CLI using the SDK.

This test suite validates that the CLI works correctly with the SDK
and that all major functionality is accessible.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestAPIManageCLI:
    """Test the API management CLI with SDK integration."""

    def test_cli_help(self):
        """Test that the CLI help command works."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "--help"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "AI Chatbot Platform" in result.stdout
        assert "User management commands" in result.stdout
        assert "Document management commands" in result.stdout

    def test_users_command_help(self):
        """Test that the users command help works."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "users", "--help"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "User management commands" in result.stdout
        assert "create" in result.stdout
        assert "list" in result.stdout
        assert "show" in result.stdout
        assert "stats" in result.stdout

    def test_documents_command_help(self):
        """Test that the documents command help works."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "documents", "--help"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Document management commands" in result.stdout
        assert "upload" in result.stdout
        assert "list" in result.stdout
        assert "search" in result.stdout

    def test_auth_status_without_login(self):
        """Test auth status when not logged in."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "auth-status"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Not authenticated" in result.stdout

    def test_version_command(self):
        """Test that the version command works."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "version"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        # This might fail if the API server is not running, but the command should exist
        assert "version" in result.stdout.lower() or "connect" in result.stderr.lower()

    def test_config_command(self):
        """Test that the config command works."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "config"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Configuration Settings" in result.stdout or "API Base URL" in result.stdout

    def test_quickstart_command(self):
        """Test that the quickstart command works."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "quickstart"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Quick Start" in result.stdout
        assert "Authentication" in result.stdout
        assert "User Management" in result.stdout

    def test_health_command_no_server(self):
        """Test health command when server is not available."""
        result = subprocess.run(
            [sys.executable, "api_manage.py", "health"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        # Should show some health check attempt even if server is down
        assert "Health Check" in result.stdout or "connect" in result.stderr.lower()


class TestSDKIntegration:
    """Test SDK integration in the CLI."""

    def test_sdk_import(self):
        """Test that the SDK can be imported successfully."""
        try:
            from client.ai_chatbot_sdk import AIChatbotSDK
            sdk = AIChatbotSDK("http://localhost:8000")
            assert sdk is not None
            assert sdk.base_url == "http://localhost:8000"
        except ImportError as e:
            pytest.fail(f"Failed to import SDK: {e}")

    def test_base_module_import(self):
        """Test that the base module imports correctly."""
        try:
            from api_cli.base import get_sdk_with_auth, APIClient
            assert get_sdk_with_auth is not None
            assert APIClient is not None
        except ImportError as e:
            pytest.fail(f"Failed to import base module: {e}")

    def test_users_module_import(self):
        """Test that the users module imports correctly."""
        try:
            from api_cli.users import user_app
            assert user_app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import users module: {e}")

    def test_documents_module_import(self):
        """Test that the documents module imports correctly."""
        try:
            from api_cli.documents import document_app
            assert document_app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import documents module: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])