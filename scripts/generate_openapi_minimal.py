#!/usr/bin/env python3
"""
Minimal OpenAPI JSON generation script for AI Chatbot MCP.
Creates a FastAPI app instance just for schema generation without database dependencies.
"""

import json
import os
import sys
from pathlib import Path

def create_minimal_app():
    """Create a minimal FastAPI app for OpenAPI generation."""
    # Set required environment variables
    os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_openapi_generation_32_chars_minimum')
    os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
    os.environ.setdefault('OPENAI_API_KEY', 'test_key')
    os.environ.setdefault('DEBUG', 'true')
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Create a minimal FastAPI app with just the routers
    from fastapi import FastAPI
    from fastapi.openapi.utils import get_openapi
    
    # Import API routers
    from app.api import (
        analytics_router,
        auth_router,
        conversations_router,
        database_router,
        documents_router,
        health_router,
        mcp_router,
        profiles_router,
        prompts_router,
        search_router,
        tasks_router,
        users_router,
    )
    
    # Import settings for metadata
    from app.config import settings
    
    # Create minimal app without lifespan or middleware
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Add routers
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    app.include_router(conversations_router, prefix="/api/v1/conversations", tags=["conversations"])
    app.include_router(database_router, prefix="/api/v1/database", tags=["database"])
    app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    app.include_router(mcp_router, prefix="/api/v1/mcp", tags=["mcp"])
    app.include_router(profiles_router, prefix="/api/v1/profiles", tags=["profiles"])
    app.include_router(prompts_router, prefix="/api/v1/prompts", tags=["prompts"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["search"])
    app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=settings.app_name,
            version=settings.app_version,
            description=settings.app_description,
            routes=app.routes,
        )

        # Add custom information
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }

        # Add authentication security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter JWT token",
            }
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    
    return app

def generate_openapi_json(output_path: str = "openapi.json"):
    """Generate OpenAPI JSON file from a minimal FastAPI application."""
    try:
        # Create minimal app
        app = create_minimal_app()
        
        # Generate the OpenAPI schema
        openapi_schema = app.openapi()
        
        # Write to JSON file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ OpenAPI JSON generated successfully: {output_file}")
        print(f"📄 Schema contains {len(openapi_schema.get('paths', {}))} endpoints")
        print(f"🏷️  API Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
        print(f"📝 Title: {openapi_schema.get('info', {}).get('title', 'unknown')}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Failed to generate OpenAPI JSON: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def print_openapi_info():
    """Print information about OpenAPI endpoints without generating file."""
    try:
        # Create minimal app
        app = create_minimal_app()
        
        # Generate the OpenAPI schema
        openapi_schema = app.openapi()
        
        print("=" * 60)
        print("AI CHATBOT MCP - OPENAPI ENDPOINTS SUMMARY")
        print("=" * 60)
        print()
        
        print("📊 API INFORMATION:")
        print(f"  • Title: {openapi_schema.get('info', {}).get('title', 'unknown')}")
        print(f"  • Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
        print(f"  • Total Endpoints: {len(openapi_schema.get('paths', {}))}")
        print()
        
        print("🔗 ENDPOINTS BY TAG:")
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        for path, methods in openapi_schema.get('paths', {}).items():
            for method, details in methods.items():
                tags = details.get('tags', ['untagged'])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append(f"{method.upper()} {path}")
        
        # Print endpoints grouped by tag
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            print(f"\n{tag.upper()}:")
            for endpoint in sorted(endpoints):
                print(f"  • {endpoint}")
        
        print()
        
    except Exception as e:
        print(f"❌ Failed to analyze OpenAPI schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate OpenAPI JSON for AI Chatbot MCP")
    parser.add_argument(
        "--output", "-o", 
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show OpenAPI information without generating file"
    )
    
    args = parser.parse_args()
    
    if args.info:
        print_openapi_info()
    else:
        generate_openapi_json(args.output)