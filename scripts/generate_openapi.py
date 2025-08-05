#!/usr/bin/env python3
"""
OpenAPI JSON generation script for AI Chatbot MCP.
Generates openapi.json file from the FastAPI application.
"""

import json
import sys
from pathlib import Path

def generate_openapi_json(output_path: str = "openapi.json"):
    """Generate OpenAPI JSON file from the FastAPI application."""
    try:
        # Add the project root to the path to import the app
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Set minimal environment to avoid database initialization
        import os
        os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_openapi_generation_32_chars_minimum')
        os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
        os.environ.setdefault('OPENAI_API_KEY', 'test_key')
        os.environ.setdefault('DEBUG', 'true')
        
        # Import the FastAPI app without triggering database initialization
        from app.main import app
        
        # Generate the OpenAPI schema (this doesn't require db)
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
        
    except ImportError as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        print("💡 Make sure you're running this from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to generate OpenAPI JSON: {e}")
        sys.exit(1)

def print_openapi_info():
    """Print information about OpenAPI endpoints without generating file."""
    try:
        # Add the project root to the path to import the app
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Set minimal environment to avoid database initialization
        import os
        os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_openapi_generation_32_chars_minimum')
        os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost/test')
        os.environ.setdefault('OPENAI_API_KEY', 'test_key')
        os.environ.setdefault('DEBUG', 'true')
        
        # Import the FastAPI app without triggering database initialization
        from app.main import app
        
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