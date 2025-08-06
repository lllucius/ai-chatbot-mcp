"""
Test API consolidation changes from PR #107.
Tests that duplicate endpoints have been removed and consolidated correctly.
"""

import os
from pathlib import Path

import pytest


def test_auth_me_endpoint_removed_from_code():
    """
    Test that the duplicate /me endpoint code has been removed from auth API file.

    This test verifies Phase 1 of the API consolidation by checking the source code
    directly instead of importing modules that have database dependencies.
    """
    # Get the auth.py file path
    project_root = Path(__file__).parent.parent
    auth_file = project_root / "app" / "api" / "auth.py"

    # Read the auth.py file
    with open(auth_file) as f:
        auth_content = f.read()

    # Check that the duplicate /me endpoint function is not present
    assert "get_current_user_info" not in auth_content, "The get_current_user_info function should be removed from auth.py"
    assert 'async def get_current_user_info(' not in auth_content, "The duplicate /me endpoint function should be removed"

    # Check that expected auth functions still exist
    assert "async def register(" in auth_content, "Register function should still exist"
    assert "async def login(" in auth_content, "Login function should still exist"
    assert "async def logout(" in auth_content, "Logout function should still exist"

def test_users_me_endpoint_exists_in_code():
    """
    Test that the /me endpoint still exists in users API file.

    This verifies that the users API still has the consolidated /me endpoint.
    """
    # Get the users.py file path
    project_root = Path(__file__).parent.parent
    users_file = project_root / "app" / "api" / "users.py"

    # Read the users.py file
    with open(users_file) as f:
        users_content = f.read()

    # Check that the /me endpoint functions exist in users API
    assert "async def get_my_profile(" in users_content, "The get_my_profile function should exist in users.py"
    assert "async def update_my_profile(" in users_content, "The update_my_profile function should exist in users.py"
    assert '@router.get("/me"' in users_content, "The GET /me route should exist in users.py"
    assert '@router.put("/me"' in users_content, "The PUT /me route should exist in users.py"

def test_password_reset_endpoints_added_to_users():
    """
    Test that password reset endpoints have been added to users API.

    This verifies Phase 2 of the API consolidation - moving password reset
    endpoints from auth API to users API.
    """
    # Get the users.py file path
    project_root = Path(__file__).parent.parent
    users_file = project_root / "app" / "api" / "users.py"

    # Read the users.py file
    with open(users_file) as f:
        users_content = f.read()

    # Check that password reset endpoints exist in users API
    assert "async def request_password_reset(" in users_content, "The request_password_reset function should exist in users.py"
    assert "async def confirm_password_reset(" in users_content, "The confirm_password_reset function should exist in users.py"
    assert '@router.post("/password-reset"' in users_content, "The POST /password-reset route should exist in users.py"
    assert '@router.post("/password-reset/confirm"' in users_content, "The POST /password-reset/confirm route should exist in users.py"

    # Check that imports are correct
    assert "PasswordResetConfirm" in users_content, "PasswordResetConfirm should be imported"
    assert "PasswordResetRequest" in users_content, "PasswordResetRequest should be imported"

def test_user_service_password_methods_added():
    """
    Test that password reset methods have been added to UserService.

    This verifies that the service layer supports the new consolidated
    password reset functionality.
    """
    # Get the user service file path
    project_root = Path(__file__).parent.parent
    service_file = project_root / "app" / "services" / "user.py"

    # Read the user service file
    with open(service_file) as f:
        service_content = f.read()

    # Check that password reset methods exist
    assert "async def request_password_reset(" in service_content, "request_password_reset method should exist in UserService"
    assert "async def confirm_password_reset(" in service_content, "confirm_password_reset method should exist in UserService"
    assert "async def get_user_by_id(" in service_content, "get_user_by_id method should exist in UserService"
    assert "async def update_user_password(" in service_content, "update_user_password method should exist in UserService"

def test_auth_api_password_endpoints_deprecated():
    """
    Test that auth API password reset endpoints are properly deprecated.

    This verifies that the auth API endpoints include deprecation warnings
    and references to the new consolidated endpoints.
    """
    # Get the auth.py file path
    project_root = Path(__file__).parent.parent
    auth_file = project_root / "app" / "api" / "auth.py"

    # Read the auth.py file
    with open(auth_file) as f:
        auth_content = f.read()

    # Check that deprecation is properly marked
    assert "deprecated=True" in auth_content, "Auth password reset endpoints should be marked as deprecated"
    assert "DEPRECATED" in auth_content, "Deprecation warning should be in the docstrings/messages"
    assert "/api/v1/users/password-reset" in auth_content, "Should reference new consolidated endpoints"

def test_openapi_shows_consolidated_endpoints():
    """
    Test that OpenAPI generation includes both deprecated and new endpoints.

    This verifies that the OpenAPI schema correctly shows the API consolidation
    with proper deprecation markings.
    """
    from scripts.generate_openapi_simple import get_basic_openapi_schema

    schema = get_basic_openapi_schema()

    # Verify basic structure
    assert "openapi" in schema
    assert "paths" in schema

    # Check that consolidated endpoints exist
    assert "/api/v1/users/password-reset" in schema["paths"], "New consolidated password reset endpoint should exist"
    assert "/api/v1/users/password-reset/confirm" in schema["paths"], "New consolidated password reset confirm endpoint should exist"

    # Check that deprecated endpoints are marked
    auth_reset_path = schema["paths"].get("/api/v1/auth/password-reset", {}).get("post", {})
    assert auth_reset_path.get("deprecated") is True, "Auth password reset should be marked as deprecated"

    auth_confirm_path = schema["paths"].get("/api/v1/auth/password-reset/confirm", {}).get("post", {})
    assert auth_confirm_path.get("deprecated") is True, "Auth password reset confirm should be marked as deprecated"

    # Check endpoint count increase
    assert len(schema["paths"]) >= 18, "Should have increased endpoint count with new consolidated endpoints"

def test_openapi_generation_works():
    """Test that OpenAPI generation script works correctly."""
    from scripts.generate_openapi_simple import get_basic_openapi_schema

    schema = get_basic_openapi_schema()

    # Verify basic structure
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert "components" in schema

    # Verify it contains the consolidated endpoint
    assert "/api/v1/users/me" in schema["paths"]

    # Verify the schema has reasonable content
    assert len(schema["paths"]) > 10, "Should have multiple endpoints documented"

def test_api_analysis_command_works():
    """Test that the API analysis command works."""
    from scripts.duplicate_api_summary import print_duplicate_summary

    # This should not raise an exception
    try:
        print_duplicate_summary()
    except Exception as e:
        pytest.fail(f"API analysis command failed: {e}")

def test_cli_commands_exist():
    """Test that the new CLI commands have been added."""
    # Get the cli/core.py file path
    project_root = Path(__file__).parent.parent
    cli_file = project_root / "cli" / "core.py"

    # Read the cli/core.py file
    with open(cli_file) as f:
        cli_content = f.read()

    # Check that new CLI commands exist
    assert "async def api_analysis(" in cli_content, "The api-analysis CLI command should exist"
    assert "async def generate_openapi(" in cli_content, "The generate-openapi CLI command should exist"

def test_documentation_files_exist():
    """Test that the documentation files from PR #107 have been created."""
    project_root = Path(__file__).parent.parent

    # Check that all documentation files exist
    docs_files = [
        "docs/duplicate_api_analysis_report.md",
        "docs/duplicate_api_implementation_guide.md",
        "docs/duplicate_api_summary.md"
    ]

    for doc_file in docs_files:
        file_path = project_root / doc_file
        assert file_path.exists(), f"Documentation file {doc_file} should exist"

        # Verify file has content
        assert file_path.stat().st_size > 1000, f"Documentation file {doc_file} should have substantial content"

def test_scripts_exist():
    """Test that the analysis and generation scripts exist."""
    project_root = Path(__file__).parent.parent

    script_files = [
        "scripts/duplicate_api_summary.py",
        "scripts/generate_openapi_simple.py"
    ]

    for script_file in script_files:
        file_path = project_root / script_file
        assert file_path.exists(), f"Script file {script_file} should exist"
        assert file_path.stat().st_size > 500, f"Script file {script_file} should have substantial content"

def test_openapi_json_can_be_generated():
    """Test that openapi.json can be generated successfully."""
    project_root = Path(__file__).parent.parent

    # Change to project directory and generate openapi.json
    original_cwd = os.getcwd()
    try:
        os.chdir(project_root)

        # Import and use the generation function
        from scripts.generate_openapi_simple import generate_openapi_json

        # Generate the file
        output_file = generate_openapi_json("test_openapi.json")

        # Verify the file was created
        assert Path(output_file).exists(), "OpenAPI JSON file should be generated"

        # Verify file has content
        with open(output_file) as f:
            import json
            data = json.load(f)
            assert "openapi" in data
            assert "paths" in data
            assert len(data["paths"]) > 5, "Should have multiple endpoints"

        # Clean up
        Path(output_file).unlink()

    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__])
